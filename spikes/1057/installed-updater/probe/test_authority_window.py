"""Local receipt/staging regressions; no root, polkit or desktop execution."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("authority_window", Path(__file__).with_name("authority-window.py"))
authority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority)


class AuthorityReceiptTests(unittest.TestCase):
    def source_path(self):
        path = Mock()
        path.is_absolute.return_value = True
        path.resolve.return_value = path
        path.parent.stat.return_value = SimpleNamespace(st_mode=stat.S_IFDIR | 0o500)
        path.stat.return_value = SimpleNamespace(st_mode=stat.S_IFREG | 0o400, st_uid=0)
        path.read_bytes.return_value = b"reviewed helper bytes\n"
        return path

    def test_staged_helper_requires_reviewed_hash_and_locked_root_bytes(self):
        expected = hashlib.sha256(b"reviewed helper bytes\n").hexdigest()
        with patch.object(authority, "safe_root_parent") as parent_check:
            path = self.source_path()
            self.assertEqual(authority.staged_source(path, expected)["sha256"], expected)
            parent_check.assert_called_once_with(path.parent, private=True)
            for mutation in ("wrong_hash", "writable_directory", "writable_file", "nonroot_file", "symlink"):
                with self.subTest(mutation=mutation):
                    path = self.source_path()
                    if mutation == "wrong_hash":
                        path.read_bytes.return_value = b"changed helper"
                    elif mutation == "writable_directory":
                        path.parent.stat.return_value.st_mode |= 0o200
                    elif mutation == "writable_file":
                        path.stat.return_value.st_mode |= 0o200
                    elif mutation == "nonroot_file":
                        path.stat.return_value.st_uid = 1000
                    else:
                        path.resolve.return_value = Path("/different-source")
                    with self.assertRaises(RuntimeError):
                        authority.staged_source(path, expected)

    def test_restoration_timestamp_precedes_removal_even_when_receipt_io_fails(self):
        for failing_write in (False, True):
            with self.subTest(failing_write=failing_write), tempfile.TemporaryDirectory() as directory:
                rule = Path(directory) / "owned.rules"
                rule.write_bytes(b"exact owned rule")
                info = rule.stat()
                window = authority.Window.__new__(authority.Window)
                window.args = SimpleNamespace(mode="deny")
                window.owned = (info.st_dev, info.st_ino)
                window.rule_bytes = rule.read_bytes()
                window.record = {"ready_unix_ns": 100}
                saved = []

                def save():
                    saved.append((dict(window.record), rule.exists()))
                    if failing_write and len(saved) == 1:
                        raise OSError("receipt unavailable")

                window.save = save
                with patch.object(authority, "RULE", rule), patch.object(authority.time, "time_ns", return_value=200):
                    window.restore()
                self.assertEqual(saved[0][0]["restore_started_unix_ns"], 200)
                self.assertTrue(saved[0][1])
                self.assertFalse(rule.exists())
                self.assertEqual(window.record["cleanup"], "restored")
                if failing_write:
                    self.assertEqual(window.record["restore_start_persist_error"], "OSError")


class LoadedMarkerTests(unittest.TestCase):
    BOOT = "12345678-1234-1234-1234-123456789abc"

    def window(self, deadline=35.0):
        window = authority.Window.__new__(authority.Window)
        window.args = SimpleNamespace(lease="1057-source-test")
        window.deadline = deadline
        window.record = {"window_started_unix_ns": 1_000_000_123, "commands": []}
        window.save = Mock()
        return window

    def marker(self):
        return {"MESSAGE": "campus1057-deny-loaded lease=1057-source-test",
                "SYSLOG_IDENTIFIER": "campus-updater-1057", "_EXE": "/usr/bin/logger",
                "_UID": "987", "_SYSTEMD_UNIT": "polkit.service",
                "_BOOT_ID": self.BOOT.replace("-", ""),
                "__REALTIME_TIMESTAMP": "1000001", "_PID": "1234", "_COMM": "logger"}

    @contextmanager
    def environment(self):
        clock = SimpleNamespace(now=0.0)

        def sleep(seconds):
            self.assertGreaterEqual(seconds, 0)
            clock.now += seconds

        with patch.object(authority.pwd, "getpwnam", return_value=SimpleNamespace(pw_uid=987)), \
                patch.object(authority.Path, "read_text", return_value=self.BOOT + "\n"), \
                patch.object(authority.time, "monotonic", side_effect=lambda: clock.now), \
                patch.object(authority.time, "sleep", side_effect=sleep):
            yield clock

    def test_exact_current_daemon_marker_is_preserved_before_readiness(self):
        window, marker = self.window(), self.marker()
        saved = []
        window.save.side_effect = lambda: saved.append(dict(window.record))
        with self.environment(), patch.object(window, "run", return_value=SimpleNamespace(
                stdout=json.dumps(marker))) as run:
            window.wait_loaded_marker()
        self.assertEqual(window.record["loaded_marker"], marker)
        self.assertNotIn("loaded_marker", saved[0])
        self.assertEqual(saved[0]["marker_bridge"]["expected_loaded_message"], marker["MESSAGE"])
        self.assertTrue(saved[0]["marker_bridge"]["rejecting_marker_required_for_case_acceptance"])
        self.assertEqual(saved[-1]["loaded_marker"], marker)
        run.assert_called_once()
        argv = run.call_args.args[0]
        self.assertEqual(argv[:4], ["/usr/bin/journalctl", "--no-pager", "--output=json", "--lines=64"])
        self.assertIn("--since=@1", argv)
        for match in ("SYSLOG_IDENTIFIER=campus-updater-1057", "_EXE=/usr/bin/logger",
                      "_SYSTEMD_UNIT=polkit.service", "_UID=987", "_BOOT_ID=" + self.BOOT.replace("-", "")):
            self.assertIn(match, argv)
        self.assertEqual(run.call_args.kwargs["timeout_seconds"], 5.0)

    def test_stale_wrong_lease_and_untrusted_producers_never_qualify(self):
        mutations = {"MESSAGE": "campus1057-deny-loaded lease=another-lease",
                     "SYSLOG_IDENTIFIER": "another-tag", "_EXE": "/usr/lib/polkit-1/polkitd",
                     "_UID": "0", "_SYSTEMD_UNIT": "sshd.service", "_BOOT_ID": "0" * 32,
                     "__REALTIME_TIMESTAMP": "1000000"}
        for field, value in mutations.items():
            with self.subTest(field=field):
                window, marker = self.window(), self.marker()
                marker[field] = value
                with self.environment(), patch.object(window, "run", return_value=SimpleNamespace(
                        stdout=json.dumps(marker))):
                    with self.assertRaisesRegex(RuntimeError, "required exact loaded logger marker absent"):
                        window.wait_loaded_marker()
                self.assertNotIn("loaded_marker", window.record)
                window.save.assert_called()
                self.assertEqual(window.record["marker_bridge"]["daemon_uid"], "987")
                self.assertEqual(window.record["marker_bridge"]["argv_prefix"], authority.LOGGER_ARGV)

    def test_absent_marker_fails_inside_existing_deadline_without_extension(self):
        for remaining, expected in ((35.0, 5.0), (0.25, 0.25), (0.0, 0.0)):
            with self.subTest(remaining=remaining):
                window = self.window(deadline=remaining)
                with self.environment() as clock, patch.object(window, "run", return_value=SimpleNamespace(
                        stdout="")) as run:
                    with self.assertRaisesRegex(RuntimeError, "logging/registration prerequisite failed"):
                        window.wait_loaded_marker()
                self.assertAlmostEqual(clock.now, expected)
                self.assertEqual(window.deadline, remaining)
                self.assertNotIn("loaded_marker", window.record)
                for call in run.call_args_list:
                    self.assertGreater(call.kwargs["timeout_seconds"], 0)
                    self.assertLessEqual(call.kwargs["timeout_seconds"], expected)

    def test_journal_command_failure_is_recorded_and_cannot_qualify(self):
        window = self.window()
        failed = SimpleNamespace(returncode=1, stdout="", stderr="journal unavailable")
        with self.environment(), patch.object(authority.subprocess, "run", return_value=failed) as run:
            with self.assertRaisesRegex(RuntimeError, "required command failed: /usr/bin/journalctl"):
                window.wait_loaded_marker()
        run.assert_called_once()
        self.assertEqual(window.record["commands"][0]["exit"], 1)
        self.assertEqual(window.record["commands"][0]["stderr"], "journal unavailable")
        self.assertNotIn("loaded_marker", window.record)

    def test_journal_timeout_is_bounded_and_visible(self):
        window = self.window(deadline=0.25)
        with self.environment(), patch.object(authority.subprocess, "run", side_effect=
                subprocess.TimeoutExpired("/usr/bin/journalctl", 0.25)) as run:
            with self.assertRaisesRegex(RuntimeError, "bounded command timed out"):
                window.wait_loaded_marker()
        self.assertEqual(run.call_args.kwargs["timeout"], 0.25)
        self.assertEqual(window.record["commands"][0]["timeout"], 0.25)
        self.assertNotIn("loaded_marker", window.record)

    def test_failed_loaded_prerequisite_never_announces_ready_and_owned_rule_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            rule = Path(directory) / "fixture-deny.rules"
            window = self.window()
            window.args = SimpleNamespace(lease="1057-source-test", uid=1000, mode="deny",
                                          subject_pid=None, session_id="6", duration_seconds=45)
            window.owned = None
            account = SimpleNamespace(pw_name="campusqa", pw_uid=1000)
            with patch.object(authority, "RULE", rule), patch.object(authority, "safe_root_parent"), \
                    patch.object(authority.pwd, "getpwuid", return_value=account), \
                    patch.object(authority.pwd, "getpwnam", return_value=account), \
                    patch.object(window, "wait_loaded_marker", side_effect=RuntimeError("exact loaded marker absent")), \
                    patch("builtins.print") as output:
                with self.assertRaisesRegex(RuntimeError, "exact loaded marker absent"):
                    window.begin()
                self.assertTrue(rule.exists())
                self.assertEqual(rule.read_bytes(), window.rule_bytes)
                self.assertEqual(window.record["owned_device_inode"], [rule.stat().st_dev, rule.stat().st_ino])
                self.assertEqual(window.record["rule_sha256"], hashlib.sha256(rule.read_bytes()).hexdigest())
                self.assertEqual(window.record["cleanup_reserve_seconds"], 10)
                self.assertEqual(window.total_deadline - window.started_at, 45)
                self.assertNotIn("ready_unix_ns", window.record)
                output.assert_not_called()
                window.restore()
                self.assertFalse(rule.exists())
                self.assertEqual(window.record["cleanup"], "restored")


if __name__ == "__main__":
    unittest.main()
