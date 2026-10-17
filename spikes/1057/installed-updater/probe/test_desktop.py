"""Source-only recorder regressions; no guest, authority or installed app is used."""
import hashlib
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock


spec = importlib.util.spec_from_file_location("desktop_probe", Path(__file__).with_name("desktop.py"))
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)


class RootPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "root.json"
        self.value = {"schema": 1, "kind": "campus1057-root-preflight", "lease_reference": "lease",
                      "graphical_uid": os.getuid(), "observed_unix_ns": time.time_ns(),
                      "hosted_allow_rule": {"path": str(desktop.HOSTED_RULE), "exists": False},
                      "rules": []}

    def bind(self, value=None, digest=None, lease="lease", uid=None):
        self.path.write_text(json.dumps(self.value if value is None else value))
        digest = digest or hashlib.sha256(self.path.read_bytes()).hexdigest()
        return desktop.root_preflight(self.path, digest, lease, os.getuid() if uid is None else uid)

    def test_exported_root_receipt_is_bound_without_claiming_owner_preservation(self):
        evidence = self.bind()
        self.assertEqual(evidence["observation"], self.value)
        self.assertIn("refresh", evidence["freshness"])

    def test_unbound_or_different_lease_user_or_rule_cannot_supply_absence(self):
        for kwargs in ({"digest": "0" * 64}, {"lease": "other"}, {"uid": os.getuid() + 1},
                       {"value": {**self.value, "hosted_allow_rule": {"path": str(desktop.HOSTED_RULE), "exists": True}}}):
            with self.subTest(kwargs=kwargs), self.assertRaises(RuntimeError):
                self.bind(**kwargs)

    def test_protected_path_requires_bound_root_fact_and_retains_unreadability(self):
        preflight = self.bind()
        with mock.patch.object(Path, "lstat", side_effect=PermissionError):
            with self.assertRaisesRegex(RuntimeError, "root preflight"):
                desktop.hosted_rule_observation()
            observed = desktop.hosted_rule_observation(preflight)
        self.assertIsNone(observed["exists"])
        self.assertEqual(observed["unreadable"], "PermissionError")
        self.assertEqual(observed["absence_source"], "root_preflight.observation.hosted_allow_rule")

    def test_existing_rule_is_refused_even_with_root_receipt(self):
        preflight = self.bind()
        with mock.patch.object(Path, "lstat", return_value=object()), self.assertRaisesRegex(RuntimeError, "must not exist"):
            desktop.hosted_rule_observation(preflight)

    def test_direct_absence_does_not_require_root_receipt(self):
        with mock.patch.object(Path, "lstat", side_effect=FileNotFoundError):
            observed = desktop.hosted_rule_observation()
        self.assertIs(observed["exists"], False)
        self.assertEqual(observed["source"], "desktop lstat")


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "case.json"
        self.value = {"schema": 1, "status": "not_certified", "acceptance": "pending_coordinator_review",
                      "planned_scenario": {"observer": "witness", "description": "cancel the prompt"},
                      "observer_statement": None,
                      "commands": [{"argv": [desktop.APP, "--update", "http://127.0.0.1:17857/stable/linux.json"],
                                    "finished_ns": time.time_ns() - 1_000_000}]}

    def write(self):
        self.path.write_text(json.dumps(self.value))
        self.path.chmod(0o600)

    def test_outcome_is_timestamped_after_invocation_without_promoting_status(self):
        self.write()
        desktop.record_outcome(self.path, "witness", "observed prompt and selected Cancel")
        value = json.loads(self.path.read_text())
        statement = value["observer_statement"]
        self.assertGreaterEqual(statement["recorded_unix_ns"], statement["invocation_finished_ns"])
        self.assertEqual(value["status"], "not_certified")
        self.assertEqual(value["acceptance"], "pending_coordinator_review")
        self.assertEqual(value["planned_scenario"], self.value["planned_scenario"])
        self.assertIn("independent", statement["review"])

    def test_incomplete_run_can_record_observation_without_claiming_success(self):
        self.value["status"] = "incomplete"
        self.write()
        desktop.record_outcome(self.path, "witness", "application timed out")
        self.assertEqual(json.loads(self.path.read_text())["status"], "incomplete")

    def test_running_uninvoked_and_already_observed_receipts_are_refused(self):
        for change in ({"status": "recording"}, {"commands": []}, {"observer_statement": {"observation": "old"}}):
            with self.subTest(change=change):
                self.path.write_text(json.dumps({**self.value, **change}))
                self.path.chmod(0o600)
                before = self.path.read_bytes()
                with self.assertRaises(RuntimeError):
                    desktop.record_outcome(self.path, "witness", "actual")
                self.assertEqual(self.path.read_bytes(), before)

    def test_run_receipt_has_only_planned_scenario(self):
        args = SimpleNamespace(receipt=self.path, case="cancel", lease_reference="lease",
                               authority_reference="ordinary", source_head="1" * 40,
                               observer="witness", planned_observation="cancel planned", timeout=40)
        recorder = desktop.Recorder(args)
        recorder.output.close()
        value = json.loads(self.path.read_text())
        self.assertIsNone(value["observer_statement"])
        self.assertEqual(value["planned_scenario"]["description"], "cancel planned")


class CommandTests(unittest.TestCase):
    def recorder(self):
        recorder = desktop.Recorder.__new__(desktop.Recorder)
        recorder.receipt = {"commands": []}
        recorder.save = lambda: None
        return recorder

    def test_capture_is_bounded_and_failure_retains_process_result(self):
        recorder = self.recorder()
        with self.assertRaisesRegex(RuntimeError, "bounded capture"):
            recorder.command([sys.executable, "-c", "print('x' * 200000)"], timeout=5)
        command = recorder.receipt["commands"][0]
        self.assertLessEqual(len(command["stdout"]) + len(command["stderr"]), desktop.CAPTURE_LIMIT)
        self.assertIn("finished_ns", command)
        self.assertIsNotNone(command["returncode"])

    def test_timeout_retains_result_and_never_looks_like_success(self):
        recorder = self.recorder()
        with self.assertRaisesRegex(RuntimeError, "timeout"):
            recorder.command([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.05)
        command = recorder.receipt["commands"][0]
        self.assertIsNotNone(command["returncode"])
        self.assertNotEqual(command["returncode"], 0)
        self.assertIn("finished_ns", command)


class DenialCorrelationTests(unittest.TestCase):
    def setUp(self):
        helper_spec = importlib.util.spec_from_file_location("authority_validation", Path(__file__).with_name("authority-window.py"))
        self.helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(self.helper)
        self.nonce = "a" * 32
        self.boot = "b" * 32
        process = {"pid": 101, "starttime": "100", "exe": "/usr/lib/polkit-1/polkitd",
                   "cgroup": "0::/system.slice/polkit.service\n", "uids": ["987"] * 4, "gids": ["986"] * 4}
        self.binding = {"uid": "987", "gid": "986", "logger_exe": "/usr/bin/logger", "unit": "polkit.service",
                        "main_pid": 101, "starttime": "100", "exe": process["exe"], "cgroup": process["cgroup"],
                        "account": "polkitd", "boot_id": self.boot, "account_primary_gid": 985,
                        "account_groups": [985, 986], "nss_users": ["polkitd"],
                        "process": process, "same_uid_processes": [process],
                        "service_state": {"Id": "polkit.service", "LoadState": "loaded", "ActiveState": "active",
                                          "SubState": "running", "DropInPaths": "", "MainPID": "101",
                                          "ControlGroup": "/system.slice/polkit.service"},
                        "logger": {"path": "/usr/bin/logger", "sha256": "a" * 64, "uid": 0, "mode": 0o755},
                        "executable": {"path": process["exe"], "sha256": "b" * 64, "uid": 0, "mode": 0o755}}
        self.session = {"Id": "6", "User": "1000", "Active": "yes", "Remote": "no"}
        self.before = {"event": "installed_identity", "app_sha256": "c" * 64, "helper_sha256": "d" * 64}
        self.desktop = {"schema": 1, "case": "deny", "status": "observation_recorded",
                        "boot_id": self.boot, "boot_id_after": self.boot,
                        "session_binding": "exact_logind_session", "lease_reference": "lease",
                        "session": self.session, "session_after": self.session,
                        "before": self.before, "after": self.before,
                        "commands": [{"argv": [desktop.APP, "--update", "http://127.0.0.1:17857/stable/linux.json"],
                                      "started_ns": 4_000_000_000, "finished_ns": 6_000_000_000, "returncode": 1,
                                      "process": {"pid": 200, "starttime_ticks": 300, "uids": [1000, 1000, 1000, 1000],
                                                  "logind_owner_uid": 1000, "session": "6"}}],
                        "updater_events": [self.before, {"event": "selected"}, {"event": "verified_download"},
                                           {"event": "polkit_adapter_result", "success": False, "stdout": ""},
                                           {"event": "refusal_bytes", "app_unchanged": True, "helper_unchanged": True},
                                           {"event": "refused", "error": "polkit adapter did not install the fixture; inspect its receipt"}]}
        self.authority = {"mode": "deny", "status": "window_elapsed", "cleanup": "restored", "deadline_exceeded": False,
                          "lease": "lease", "uid": 1000, "user": "campusqa", "marker_nonce": self.nonce,
                          "service_binding": self.binding, "service_binding_before_ready": self.binding,
                          "service_binding_before_restore": self.binding, "service_binding_after_restore": self.binding,
                          "service_identity_valid": True, "subject_session": "6", "boot_id": self.boot,
                          "window_started_unix_ns": 1_000_000_000, "loaded_marker_observed_unix_ns": 3_000_000_000,
                          "ready_unix_ns": 3_500_000_000, "restore_started_unix_ns": 7_000_000_000,
                          "window_finished_unix_ns": 8_000_000_000}
        self.authority.update(owned_path="/etc/polkit-1/rules.d/00-campus-updater-1057-deny.rules",
                              owned_device_inode=[1, 2], rule_sha256=hashlib.sha256(self.helper.deny_rule(
                                  "campusqa", "lease", None, "6", nonce=self.nonce)).hexdigest())
        self.rows = [self.row("campus1057-deny-loaded lease=lease nonce=" + self.nonce, "201", "2000000"),
                     self.row("campus1057-deny lease=lease nonce=" + self.nonce
                              + " pid=200 user=campusqa session=6 active=true", "202", "5000000")]

    def row(self, message, pid, timestamp):
        return {"MESSAGE": message, "SYSLOG_IDENTIFIER": "campus-updater-1057", "_UID": "987", "_GID": "986",
                "_PID": pid, "_TRANSPORT": "syslog", "_BOOT_ID": self.boot,
                "__REALTIME_TIMESTAMP": timestamp, "__MONOTONIC_TIMESTAMP": timestamp}

    def check(self):
        return desktop.validate_denial_evidence(self.desktop, self.authority, self.rows,
                                               self.helper.validate_marker_rows, self.helper.deny_rule)

    def test_both_optional_fields_absent_correlates_but_stays_pending_and_preserves_sender_separation(self):
        result = self.check()
        self.assertEqual(result["status"], "correlated_pending_coordinator_review", result)
        self.assertEqual(result["acceptance"], "pending_coordinator_review")
        self.assertEqual(result["app_subject"], {"pid": 200, "starttime_ticks": 300, "session": "6"})
        self.assertEqual(result["logger_sender_pids"], ["202"])
        self.assertTrue(result["loaded"]["missing_optional_fields"])
        self.assertTrue(result["rejecting"]["missing_optional_fields"])
        self.assertEqual(result["journal_rows"], self.rows)

    def test_rejecting_reliable_fields_and_optional_contradictions_fail_even_with_later_good_row(self):
        original = copy.deepcopy(self.rows)
        for key, value in (("_UID", "0"), ("_GID", "1000"), ("_PID", "bad"), ("_PID", ["202"]),
                           ("_TRANSPORT", "journal"), ("_BOOT_ID", "c" * 32), ("_EXE", "/tmp/logger"),
                           ("_SYSTEMD_UNIT", ""), ("_EXE", []), ("__REALTIME_TIMESTAMP", "3000000"),
                           ("__REALTIME_TIMESTAMP", "7000000")):
            with self.subTest(field=key, value=value):
                bad = {**original[1], key: value, "SYSLOG_PID": "202"}
                self.rows = [original[0], bad, original[1]]
                result = self.check()
                self.assertEqual(result["status"], "incomplete", result)
                self.assertTrue(result["rejecting"]["anomalies"])
                self.assertIn(bad, result["journal_rows"])
        for key in ("_UID", "_GID", "_PID", "_TRANSPORT", "_BOOT_ID", "__REALTIME_TIMESTAMP"):
            with self.subTest(missing=key):
                bad = dict(original[1])
                bad.pop(key)
                self.rows = [original[0], bad]
                self.assertEqual(self.check()["status"], "incomplete")

    def test_wrong_subject_session_nonce_and_unknown_current_event_never_qualify(self):
        original = copy.deepcopy(self.rows)
        for old, new in (("pid=200", "pid=202"), ("session=6", "session=7"),
                         ("nonce=" + self.nonce, "nonce=" + "c" * 32), ("lease=lease", "lease=old")):
            with self.subTest(new=new):
                self.rows = [original[0], {**original[1], "MESSAGE": original[1]["MESSAGE"].replace(old, new)}]
                self.assertEqual(self.check()["status"], "incomplete")
        self.rows = [*original, {**original[1], "MESSAGE": "unknown nonce=" + self.nonce}]
        self.assertEqual(self.check()["status"], "incomplete")

    def test_service_change_unclean_restore_missing_ready_and_historical_failure_remain_incomplete(self):
        for key, value in (("service_identity_valid", False), ("cleanup", "manual_recovery_required"),
                           ("ready_unix_ns", None), ("status", "failed"),
                           ("service_binding_after_restore", {**self.binding, "main_pid": 102})):
            with self.subTest(change=key):
                saved = self.authority[key]
                self.authority[key] = value
                self.assertEqual(self.check()["status"], "incomplete")
                self.authority[key] = saved
        for key, value in (("case", "cancel"), ("case", "missing-authority"), ("status", "incomplete")):
            with self.subTest(change=value):
                saved = self.desktop[key]
                self.desktop[key] = value
                self.assertEqual(self.check()["status"], "incomplete")
                self.desktop[key] = saved

    def test_rule_ownership_hash_or_app_boot_mismatch_prevents_correlation(self):
        for key, value in (("owned_path", "/tmp/rule"), ("owned_device_inode", []), ("rule_sha256", "0" * 64)):
            with self.subTest(change=key):
                saved = self.authority[key]
                self.authority[key] = value
                self.assertEqual(self.check()["status"], "incomplete")
                self.authority[key] = saved
        for key in ("boot_id", "boot_id_after"):
            saved = self.desktop.pop(key)
            self.assertEqual(self.check()["status"], "incomplete")
            self.desktop[key] = saved
        self.rows[1]["_PID"] = "200"
        self.assertEqual(self.check()["status"], "incomplete")

    def test_no_app_lifetime_no_exact_session_or_adapter_entry_cannot_be_accepted(self):
        process = self.desktop["commands"][0]["process"]
        for key, value in (("starttime_ticks", None), ("session", None), ("uids", [0, 0]), ("pid", True)):
            with self.subTest(change=key):
                saved = process[key]
                process[key] = value
                self.assertEqual(self.check()["status"], "incomplete")
                process[key] = saved
        self.desktop["updater_events"][3]["stdout"] = '{"phase":"entered"}'
        self.assertEqual(self.check()["status"], "incomplete")

    def test_export_digest_failure_creates_incomplete_receipt_without_rewriting_original(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "desktop.json"
            original.write_text(json.dumps(self.desktop))
            saved = original.read_bytes()
            args = SimpleNamespace(validate_denial=original, desktop_receipt_sha256="0" * 64,
                                   authority_receipt=original, authority_receipt_sha256="0" * 64,
                                   journal=original, journal_sha256="0" * 64, authority_helper_sha256="0" * 64,
                                   validation_receipt=Path(directory) / "validation.json")
            self.assertEqual(desktop.validate_denial_exports(args), 1)
            self.assertEqual(original.read_bytes(), saved)
            self.assertEqual(json.loads(args.validation_receipt.read_text())["status"], "incomplete")

    def test_bound_export_uses_real_shared_validator_and_retains_rows_on_source_mismatch(self):
        helper_sha = hashlib.sha256(Path(__file__).with_name("authority-window.py").read_bytes()).hexdigest()
        recorder_sha = hashlib.sha256(Path(__file__).with_name("desktop.py").read_bytes()).hexdigest()
        for matching_helper, matching_recorder in ((True, True), (False, True), (True, False)):
            with self.subTest(helper=matching_helper, recorder=matching_recorder), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.authority["authority_helper"] = {"sha256": helper_sha if matching_helper else "0" * 64}
                self.desktop["recorder"] = {"sha256": recorder_sha if matching_recorder else "0" * 64}
                contents = {"desktop": json.dumps(self.desktop), "authority": json.dumps(self.authority),
                            "journal": "\n".join(map(json.dumps, self.rows)) + "\n"}
                paths, hashes = {}, {}
                for key, content in contents.items():
                    paths[key] = root / (key + ".json")
                    paths[key].write_text(content)
                    hashes[key] = hashlib.sha256(content.encode()).hexdigest()
                args = SimpleNamespace(validate_denial=paths["desktop"], desktop_receipt_sha256=hashes["desktop"],
                                       authority_receipt=paths["authority"], authority_receipt_sha256=hashes["authority"],
                                       journal=paths["journal"], journal_sha256=hashes["journal"],
                                       authority_helper_sha256=helper_sha, validation_receipt=root / "validation.json")
                self.assertEqual(desktop.validate_denial_exports(args), 0 if matching_helper and matching_recorder else 1)
                result = json.loads(args.validation_receipt.read_text())
                self.assertEqual(result["journal_rows"], self.rows)
                self.assertEqual(result["acceptance"], "pending_coordinator_review")
                self.assertEqual(result["recorder_source"]["sha256"], recorder_sha)
                self.assertEqual(result["observed_recorder_source"], self.desktop["recorder"])
                for key, path in paths.items():
                    self.assertEqual(path.read_text(), contents[key])

    def test_loaded_and_rejecting_optional_metadata_and_inventory_must_agree(self):
        original = copy.deepcopy(self.rows)
        for fields in ({"_EXE": "/usr/bin/logger"}, {"_SYSTEMD_UNIT": "polkit.service"},
                       {"_EXE": "/usr/bin/logger", "_SYSTEMD_UNIT": "polkit.service"}):
            with self.subTest(optional_fields=fields):
                self.rows = [{**row, **fields} for row in original]
                self.assertEqual(self.check()["status"], "correlated_pending_coordinator_review")
        self.rows.append({**self.rows[0], "_EXE": "/tmp/spoof"})
        self.assertEqual(self.check()["status"], "incomplete")
        self.rows.pop()
        self.binding["same_uid_processes"].append({"pid": 999})
        self.assertEqual(self.check()["status"], "incomplete")

    def test_journal_overflow_and_fractional_invocation_window_fail_closed(self):
        original = copy.deepcopy(self.rows)
        self.rows = [original[0]] * 64 + [original[1]]
        self.assertEqual(self.check()["status"], "incomplete")
        self.rows = original
        self.desktop["commands"][0]["started_ns"] = 5_000_000_001
        self.assertEqual(self.check()["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
