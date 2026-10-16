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


NONCE = "0123456789abcdef0123456789abcdef"
BOOT = "12345678123412341234123456789abc"
PROCESS = {"pid": 77, "starttime": "123", "exe": "/usr/lib/polkit-1/polkitd",
           "cgroup": "0::/system.slice/polkit.service\n", "uids": ["987"] * 4, "gids": ["986"] * 4}
BINDING = {"uid": "987", "gid": "986", "logger_exe": authority.LOGGER,
           "unit": "polkit.service", "boot_id": BOOT, "account": "polkitd",
           "account_primary_gid": 985, "account_groups": [985, 986], "nss_users": ["polkitd"],
           "main_pid": 77, "starttime": "123", "exe": PROCESS["exe"], "cgroup": PROCESS["cgroup"],
           "process": PROCESS, "same_uid_processes": [PROCESS],
           "service_state": {"Id": "polkit.service", "LoadState": "loaded", "ActiveState": "active",
                             "SubState": "running", "DropInPaths": "", "MainPID": "77",
                             "ControlGroup": "/system.slice/polkit.service"},
           "logger": {"path": authority.LOGGER, "sha256": "a" * 64, "uid": 0, "mode": 0o755},
           "executable": {"path": PROCESS["exe"], "sha256": "b" * 64, "uid": 0, "mode": 0o755}}



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

    def test_logger_executable_setid_or_writable_bytes_refuse(self):
        path = self.source_path()
        path.stat.return_value = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o755)
        with patch.object(authority, "safe_root_parent"):
            self.assertEqual(authority.root_executable(path)["uid"], 0)
            for bits in (0o4000, 0o2000, 0o020, 0o002):
                path.stat.return_value.st_mode = stat.S_IFREG | 0o755 | bits
                with self.subTest(bits=bits), self.assertRaises(RuntimeError):
                    authority.root_executable(path)

    def test_restoration_timestamp_precedes_removal_even_when_receipt_io_fails(self):
        for failing_write in (False, True):
            with self.subTest(failing_write=failing_write), tempfile.TemporaryDirectory() as directory:
                rule = Path(directory) / "owned.rules"
                rule.write_bytes(b"exact owned rule")
                info = rule.stat()
                window = authority.Window.__new__(authority.Window)
                window.args = SimpleNamespace(mode="deny")
                window.recheck_service = Mock()
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
        window.record = {"window_started_unix_ns": 1_000_000_123, "commands": [],
                         "marker_nonce": NONCE, "service_binding": dict(BINDING), "boot_id": BOOT}
        window.save = Mock()
        return window

    def marker(self):
        return {"MESSAGE": "campus1057-deny-loaded lease=1057-source-test nonce=" + NONCE,
                "SYSLOG_IDENTIFIER": "campus-updater-1057", "_EXE": "/usr/bin/logger",
                "_UID": "987", "_GID": "986", "_TRANSPORT": "syslog", "_SYSTEMD_UNIT": "polkit.service",
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
                patch.object(authority.time, "time_ns", side_effect=lambda: 1_000_002_000 + int(clock.now * 1e9)), \
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
        self.assertEqual(argv[:4], ["/usr/bin/journalctl", "--no-pager", "--output=json", "--lines=65"])
        self.assertIn("--since=@1", argv)
        for match in ("SYSLOG_IDENTIFIER=campus-updater-1057", "_GID=986",
                      "_TRANSPORT=syslog", "_UID=987", "_BOOT_ID=" + self.BOOT.replace("-", "")):
            self.assertIn(match, argv)
        self.assertFalse(any(arg.startswith(("_EXE=", "_SYSTEMD_UNIT=")) for arg in argv))
        self.assertIn("+", argv)
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
                    with self.assertRaisesRegex(RuntimeError, "loaded (logger marker absent|marker candidate)"):
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

    def test_candidate_current_nonce_cannot_supply_loaded_readiness(self):
        window, row = self.window(), self.marker()
        row["MESSAGE"] = row["MESSAGE"].replace("deny-loaded", "deny-candidate") + ' {"status":"observed"}'
        with self.environment(), patch.object(window, "run", return_value=SimpleNamespace(stdout=json.dumps(row))):
            with self.assertRaisesRegex(RuntimeError, "contradictory current-nonce loaded marker candidate"):
                window.wait_loaded_marker()
        self.assertNotIn("loaded_marker", window.record)
        self.assertEqual(window.record["loaded_marker_evidence"]["anomalies"][0]["row"], row)

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
        # Fractional origins reproduce elapsed-time rounding on either side of
        # 45 seconds without relying on the host's current monotonic clock.
        for origin in (0.0, 20.1, 63.9):
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as directory:
                self.check_failed_loaded_prerequisite(directory, origin)

    def test_late_observation_overflow_and_malformed_candidates_never_qualify(self):
        for case in ("late", "overflow", "malformed", "oversized"):
            with self.subTest(case=case):
                window = self.window()
                row = self.marker()
                if case == "oversized":
                    row["extra"] = "x" * (768 * 1024)
                lines = [json.dumps(row)] * (65 if case == "overflow" else 1)
                if case == "malformed":
                    lines.insert(0, '{"MESSAGE": "broken nonce=' + NONCE)
                with self.environment() as clock:
                    def result(*args, **kwargs):
                        if case == "late":
                            clock.now = 5.01
                        return SimpleNamespace(stdout="\n".join(lines))
                    window.run = Mock(side_effect=result)
                    with self.assertRaises(RuntimeError):
                        window.wait_loaded_marker()
                self.assertNotIn("loaded_marker", window.record)
                self.assertIn("loaded_marker_evidence", window.record)

    def test_fresh_nonce_is_persisted_once_before_each_rule_creation(self):
        nonces = ["a" * 32, "b" * 32]
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(authority.secrets, "token_hex", side_effect=nonces) as random:
            for nonce in nonces:
                rule = Path(directory) / "rule"
                window = self.window()
                window.args = SimpleNamespace(lease="1057-source-test", uid=1000, mode="deny",
                                              subject_pid=None, session_id="6", duration_seconds=45,
                                              receipt=Path(directory) / "receipt")
                window.owned = None
                persisted = []
                window.save = lambda: persisted.append((dict(window.record), rule.exists()))
                account = SimpleNamespace(pw_name="campusqa", pw_uid=1000)
                with patch.object(authority, "RULE", rule), patch.object(authority, "safe_root_parent"), \
                        patch.object(authority.pwd, "getpwuid", return_value=account), \
                        patch.object(authority.pwd, "getpwnam", return_value=account), \
                        patch.object(window, "bind_service", return_value=BINDING), \
                        patch.object(window, "wait_loaded_marker"), \
                        patch.object(window, "recheck_service"), patch("builtins.print"):
                    window.begin()
                    self.assertEqual(persisted[0][0]["marker_nonce"], nonce)
                    self.assertFalse(persisted[0][1])
                    self.assertEqual(rule.read_text().count("nonce=" + nonce), 3)
                    window.restore()
            self.assertEqual(random.call_args_list, [unittest.mock.call(16), unittest.mock.call(16)])

    def test_absent_or_failed_service_binding_refuses_before_rule_mutation(self):
        for binding in (None, {}):
            with tempfile.TemporaryDirectory() as directory:
                rule = Path(directory) / "rule"
                window = self.window()
                window.args = SimpleNamespace(lease="1057-source-test", uid=1000, mode="deny",
                                              subject_pid=None, session_id="6", duration_seconds=45)
                account = SimpleNamespace(pw_name="campusqa", pw_uid=1000)
                with patch.object(authority, "RULE", rule), patch.object(authority, "safe_root_parent"), \
                        patch.object(authority.pwd, "getpwuid", return_value=account), \
                        patch.object(authority.pwd, "getpwnam", return_value=account), \
                        patch.object(window, "bind_service", return_value=binding), \
                        patch.object(authority.secrets, "token_hex") as random, patch("builtins.print") as output:
                    with self.assertRaises(RuntimeError):
                        window.begin()
                    self.assertFalse(rule.exists())
                    random.assert_not_called()
                    output.assert_not_called()

    def check_failed_loaded_prerequisite(self, directory, origin):
        with patch.object(authority.time, "monotonic", return_value=origin):
            rule = Path(directory) / "fixture-deny.rules"
            window = self.window()
            window.args = SimpleNamespace(lease="1057-source-test", uid=1000, mode="deny",
                                          subject_pid=None, session_id="6", duration_seconds=45)
            window.owned = None
            account = SimpleNamespace(pw_name="campusqa", pw_uid=1000)
            with patch.object(authority, "RULE", rule), patch.object(authority, "safe_root_parent"), \
                    patch.object(authority.pwd, "getpwuid", return_value=account), \
                    patch.object(authority.pwd, "getpwnam", return_value=account), \
                    patch.object(window, "bind_service", return_value=dict(BINDING)), \
                    patch.object(window, "wait_loaded_marker", side_effect=RuntimeError("exact loaded marker absent")), \
                    patch("builtins.print") as output:
                with self.assertRaisesRegex(RuntimeError, "exact loaded marker absent"):
                    window.begin()
                self.assertTrue(rule.exists())
                self.assertEqual(rule.read_bytes(), window.rule_bytes)
                self.assertEqual(window.record["owned_device_inode"], [rule.stat().st_dev, rule.stat().st_ino])
                self.assertEqual(window.record["rule_sha256"], hashlib.sha256(rule.read_bytes()).hexdigest())
                self.assertEqual(window.record["cleanup_reserve_seconds"], 10)
                self.assertEqual(window.started_at, origin)
                self.assertEqual(window.total_deadline, origin + 45)
                self.assertEqual(window.deadline, (origin + 45) - 10)
                self.assertAlmostEqual(window.total_deadline - window.started_at, 45, delta=1e-12)
                self.assertNotIn("ready_unix_ns", window.record)
                output.assert_not_called()
                window.restore()
                self.assertFalse(rule.exists())
                self.assertEqual(window.record["cleanup"], "restored")


class MarkerProvenanceTests(unittest.TestCase):
    def marker(self):
        return {"MESSAGE": "campus1057-deny-loaded lease=lease1 nonce=" + NONCE,
                "SYSLOG_IDENTIFIER": authority.LOGGER_TAG, "_UID": "987", "_GID": "986",
                "_PID": "1234", "_TRANSPORT": "syslog", "_BOOT_ID": BOOT,
                "__REALTIME_TIMESTAMP": "2000000", "__MONOTONIC_TIMESTAMP": "10000",
                "_SOURCE_REALTIME_TIMESTAMP": "1999999"}

    def validate(self, rows, binding=BINDING):
        return authority.validate_marker_rows(rows, self.marker()["MESSAGE"], NONCE, "lease1",
                                              binding, BOOT, 1_000_000_000, 3_000_000_000)

    def test_optional_metadata_absent_or_corroborating_is_preserved(self):
        for optional in ({}, {"_EXE": authority.LOGGER}, {"_SYSTEMD_UNIT": "polkit.service"},
                         {"_EXE": authority.LOGGER, "_SYSTEMD_UNIT": "polkit.service"}):
            with self.subTest(optional=optional):
                row = {**self.marker(), **optional}
                evidence = self.validate([row, row])
                self.assertEqual(evidence["accepted"], [row, row])
                self.assertFalse(evidence["anomalies"])
                self.assertEqual(evidence["missing_optional_fields"][0]["fields"],
                                 [key for key in ("_EXE", "_SYSTEMD_UNIT") if key not in optional])

    def test_candidate_is_not_a_loaded_or_rejecting_marker(self):
        candidate = {**self.marker(), "MESSAGE": self.marker()["MESSAGE"].replace("deny-loaded", "deny-candidate")
                     + ' {"status":"observed"}'}
        for expected in (self.marker()["MESSAGE"], self.marker()["MESSAGE"].replace("deny-loaded", "deny")
                         + " pid=123 user=fixture-user session=c3 active=true"):
            evidence = authority.validate_marker_rows([candidate], expected, NONCE, "lease1", BINDING,
                                                      BOOT, 1_000_000_000, 3_000_000_000)
            self.assertFalse(evidence["accepted"])
            self.assertEqual(evidence["anomalies"][0]["row"], candidate)

    def test_missing_malformed_or_wrong_reliable_fields_cannot_be_forged(self):
        bad = {"_UID": ["0", "1000", "988"], "_GID": ["0", "1000", "985"],
               "_PID": ["0", "1", "-1", "2147483648", "1.5", "01234", "9" * 5000],
               "_TRANSPORT": ["journal"], "_BOOT_ID": ["f" * 32],
               "SYSLOG_IDENTIFIER": ["forged"], "__REALTIME_TIMESTAMP": ["999999", "3000001"],
               "_SOURCE_REALTIME_TIMESTAMP": ["999999", "3000001"], "__MONOTONIC_TIMESTAMP": ["0"]}
        required = ("_UID", "_GID", "_PID", "_TRANSPORT", "_BOOT_ID", "SYSLOG_IDENTIFIER", "__REALTIME_TIMESTAMP")
        for field, values in bad.items():
            for value in [*values, None, [], [self.marker()[field]], 123, True, ""]:
                with self.subTest(field=field, value=value):
                    row = {**self.marker(), field: value, "SYSLOG_PID": "1234"}
                    evidence = self.validate([row, self.marker()])
                    self.assertEqual(evidence["rejected"][0]["row"], row)
                    self.assertEqual(len(evidence["anomalies"]), 1)
        for field in required:
            row = self.marker()
            del row[field]
            self.assertFalse(self.validate([row])["accepted"])

    def test_optional_contradiction_cannot_be_hidden_by_good_row(self):
        for field in ("_EXE", "_SYSTEMD_UNIT"):
            for value in ("", None, [], [authority.LOGGER], "untrusted", 123):
                row = {**self.marker(), field: value}
                result = self.validate([row, self.marker()])
                self.assertEqual(result["anomalies"][0]["row"], row)
                self.assertTrue(result["accepted"])

    def test_wrong_nonce_lease_event_and_fractional_time_do_not_qualify(self):
        for message in (self.marker()["MESSAGE"].replace(NONCE, "f" * 32),
                        self.marker()["MESSAGE"].replace("lease1", "lease2"),
                        self.marker()["MESSAGE"].replace("deny-loaded", "deny"),
                        self.marker()["MESSAGE"].replace(" nonce=" + NONCE, "")):
            row = {**self.marker(), "MESSAGE": message}
            self.assertFalse(self.validate([row])["accepted"])
        row = self.marker()
        result = authority.validate_marker_rows([row], row["MESSAGE"], NONCE, "lease1", BINDING,
                                                BOOT, 2_000_000_001, 3_000_000_000)
        self.assertFalse(result["accepted"])

    def test_full_service_context_is_mandatory(self):
        for key in BINDING:
            binding = dict(BINDING)
            del binding[key]
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                self.validate([self.marker()], binding)


class ServiceBindingTests(unittest.TestCase):
    @contextmanager
    def environment(self, process=None, extra=False):
        process = PROCESS if process is None else process
        window = authority.Window.__new__(authority.Window)
        window.args = SimpleNamespace(uid=1000)
        window.deadline, window.total_deadline = 35, 45
        window.record, window.save = {}, Mock()
        window.run = Mock(return_value=SimpleNamespace(stdout="\n".join(
            key + "=" + value for key, value in BINDING["service_state"].items())))
        account = SimpleNamespace(pw_uid=987, pw_gid=985, pw_name="polkitd")
        paths = [Path("/proc/77")] + ([Path("/proc/78")] if extra else [])
        def read(path, *args, **kwargs):
            return BOOT if path.name == "boot_id" else "Uid:\t987\t987\t987\t987\n"
        def identity(pid):
            return {**process, "pid": pid}
        with patch.object(authority.pwd, "getpwnam", return_value=account), \
                patch.object(authority.pwd, "getpwuid", return_value=account), \
                patch.object(authority.pwd, "getpwall", return_value=[account]), \
                patch.object(authority.os, "getgrouplist", return_value=[985, 986]), \
                patch.object(authority, "process_identity", side_effect=identity), \
                patch.object(authority, "root_executable", side_effect=lambda path: BINDING[
                    "logger" if str(path) == authority.LOGGER else "executable"]), \
                patch.object(authority.Path, "iterdir", return_value=iter(paths)), \
                patch.object(authority.Path, "read_text", read), \
                patch.object(authority.time, "monotonic", return_value=0):
            yield window

    def test_actual_gid_membership_and_complete_process_binding(self):
        with self.environment() as window:
            self.assertEqual(window.bind_service(), BINDING)
        self.assertNotEqual(BINDING["account_primary_gid"], int(BINDING["gid"]))

    def test_mismatched_real_effective_saved_credentials_or_unexplained_process_refuse(self):
        for field, values in (("uids", ["1000"] * 4), ("uids", ["987", "0", "987", "987"]),
                              ("gids", ["984"] * 4), ("gids", ["986", "986", "0", "986"]),
                              ("cgroup", "0::/other.service\n")):
            with self.subTest(field=field, values=values), self.environment({**PROCESS, field: values}) as window:
                with self.assertRaises(RuntimeError):
                    window.bind_service()
        with self.environment(extra=True) as window, self.assertRaisesRegex(RuntimeError, "same-UID"):
            window.bind_service()

    def test_service_pid_starttime_or_boot_change_invalidates_recheck(self):
        for field, value in (("main_pid", 78), ("starttime", "124"), ("boot_id", "f" * 32)):
            with self.subTest(field=field):
                window = authority.Window.__new__(authority.Window)
                window.record, window.save = {"service_binding": BINDING}, Mock()
                window.bind_service = Mock(return_value={**BINDING, field: value})
                with self.assertRaisesRegex(RuntimeError, "identity changed"):
                    window.recheck_service("service_binding_before_ready")
                self.assertFalse(window.record["service_identity_valid"])
                self.assertIn("service_binding_before_ready", window.record)

    def test_context_collection_obeys_restoration_deadline(self):
        with self.environment() as window:
            window.total_deadline = 0
            with self.assertRaisesRegex(RuntimeError, "deadline"):
                window.bind_service(restoring=True)

    def test_service_inventory_count_is_bounded(self):
        with self.environment() as window, patch.object(authority.Path, "iterdir",
                return_value=iter([Path("/proc/nonprocess")] * 4097)):
            with self.assertRaisesRegex(RuntimeError, "inventory exceeds"):
                window.bind_service()

    def test_rule_replacement_during_context_scan_is_not_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            rule, replacement = Path(directory) / "rule", Path(directory) / "replacement"
            rule.write_bytes(b"same contents")
            replacement.write_bytes(b"same contents")
            info = rule.stat()
            window = authority.Window.__new__(authority.Window)
            window.args = SimpleNamespace(mode="deny")
            window.record, window.save = {}, Mock()
            window.owned, window.rule_bytes = (info.st_dev, info.st_ino), rule.read_bytes()
            window.recheck_service = Mock(side_effect=lambda *args, **kwargs: replacement.replace(rule))
            with patch.object(authority, "RULE", rule), self.assertRaisesRegex(RuntimeError, "identity changed"):
                window.restore()
            self.assertTrue(rule.exists())

    def test_changed_context_still_removes_only_owned_unchanged_rule(self):
        for changed_bytes in (False, True):
            with self.subTest(changed_bytes=changed_bytes), tempfile.TemporaryDirectory() as directory:
                rule = Path(directory) / "owned.rules"
                rule.write_bytes(b"owned")
                info = rule.stat()
                window = authority.Window.__new__(authority.Window)
                window.args = SimpleNamespace(mode="deny")
                window.record, window.save = {}, Mock()
                window.owned, window.rule_bytes = (info.st_dev, info.st_ino), b"owned"
                def failed_recheck(*args, **kwargs):
                    window.record["service_identity_valid"] = False
                    raise RuntimeError("changed daemon")
                window.recheck_service = Mock(side_effect=failed_recheck)
                if changed_bytes:
                    rule.write_bytes(b"someone else's rule")
                with patch.object(authority, "RULE", rule):
                    if changed_bytes:
                        with self.assertRaisesRegex(RuntimeError, "deny rule changed"):
                            window.restore()
                        self.assertTrue(rule.exists())
                    else:
                        window.restore()
                        self.assertFalse(rule.exists())
                        self.assertEqual(window.record["cleanup"], "restored")
                        self.assertEqual(window.record["status"], "failed")
                        self.assertFalse(window.record["service_identity_valid"])


if __name__ == "__main__":
    unittest.main()
