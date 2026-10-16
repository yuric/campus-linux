"""Source-only recorder regressions; no guest, authority or installed app is used."""
import hashlib
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


if __name__ == "__main__":
    unittest.main()
