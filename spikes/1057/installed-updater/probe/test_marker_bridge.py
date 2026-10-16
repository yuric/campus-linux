"""Source-only JavaScript marker regressions: no logger, polkit or guest access.

The real next-lease executable and journal preflight remains mandatory. A mocked
spawn succeeding here is not runtime marker or authority acceptance evidence.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


spec = importlib.util.spec_from_file_location("authority_marker_window", Path(__file__).with_name("authority-window.py"))
authority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority)

LOGGER_PREFIX = ["/usr/bin/logger", "--socket-errors=on", "--priority", "user.notice",
                 "--tag", "campus-updater-1057", "--"]
NODE_HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const result = {events: [], attempted: [], delivered: [], diagnostics: []};
let callback;
const polkit = {
  Result: {NO: 'NO'},
  addRule: function(rule) {
    result.events.push('register');
    if (input.registrationFails) throw new Error('mock registration failed');
    callback = rule;
  },
  spawn: function(argv) {
    result.events.push('spawn');
    result.attempted.push(Array.from(argv));
    if (result.attempted.length === input.spawnFailsAt)
      throw new Error('mock logger missing or nonzero exit');
    result.delivered.push(Array.from(argv));
    return '';
  },
  log: function(message) { result.diagnostics.push(String(message)); }
};
try {
  vm.runInNewContext(input.source, {polkit: polkit}, {timeout: 1000});
} catch (error) {
  result.loadError = String(error);
}
if (callback && input.subject && !result.loadError) {
  const action = {
    id: input.action.id,
    lookup: function(key) { return input.action[key]; }
  };
  try {
    const answer = callback(action, input.subject);
    result.answer = answer === undefined ? null : answer;
  } catch (error) {
    result.callbackError = String(error);
  }
}
process.stdout.write(JSON.stringify(result));
"""


class MarkerBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if cls.node is None:
            raise RuntimeError("marker source regressions require an existing Node executable; do not install dependencies")

    def execute(self, *, user="fixture-user", lease="lease:1057.1", pid=None,
                session="c3", subject=None, action=None, **options):
        payload = {
            "source": authority.deny_rule(user, lease, pid=pid, session=session).decode(),
            "subject": subject,
            "action": action or {"id": authority.ACTION, "program": authority.PROGRAM, "user": "root"},
            **options,
        }
        completed = subprocess.run(
            [self.node, "-e", NODE_HARNESS], input=json.dumps(payload), text=True,
            capture_output=True, check=True, timeout=5,
            env={"PATH": os.defpath, "LC_ALL": "C"},
        )
        self.assertEqual(completed.stderr, "")
        return json.loads(completed.stdout)

    def subject(self, **overrides):
        return {"user": "fixture-user", "pid": 123, "session": "c3",
                "local": True, "active": True, **overrides}

    def test_fixed_argv_and_exact_single_message_operand(self):
        result = self.execute(subject=self.subject())
        self.assertEqual(result["events"], ["register", "spawn", "spawn"])
        self.assertEqual(result["attempted"], [
            LOGGER_PREFIX + ["campus1057-deny-loaded lease=lease:1057.1"],
            LOGGER_PREFIX + ["campus1057-deny lease=lease:1057.1 pid=123 user=fixture-user session=c3 active=true"],
        ])
        self.assertEqual(result["delivered"], result["attempted"])
        self.assertEqual(result["answer"], "NO")

    def test_valid_punctuation_and_maximum_lengths_stay_one_literal_operand(self):
        user = "_" + "a" * 60 + "_.-"
        lease = "L" + "a" * 122 + "_.:-0"
        session = "s" + "a" * 58 + "_.:-0"
        self.assertEqual((len(user), len(lease), len(session)), (64, 128, 64))
        result = self.execute(user=user, lease=lease, session=session,
                              subject=self.subject(user=user, session=session))
        self.assertEqual(result["answer"], "NO")
        self.assertEqual(result["delivered"][-1], LOGGER_PREFIX + [
            f"campus1057-deny lease={lease} pid=123 user={user} session={session} active=true"])

    def test_untrusted_marker_values_rejected_before_javascript_generation(self):
        for field, values in {
            "user": ["", "0user", "user name", "user\nforged", 'user";throw 1;//',
                     "user$(id)", "user`id`", "user\\escape", "u" * 65, None],
            "lease": ["", "-lease", "lease\nforged", 'lease";throw 1;//',
                      "lease$(id)", "lease`id`", "lease\\escape", "l" * 129, None],
            "session": [None, "", "-session", "session name", "session\nforged",
                        'session";throw 1;//', "session$(id)", "session`id`",
                        "session\\escape", "s" * 65],
            "pid": [True, False, 0, 1, -1, 2.5, "123", 2147483648],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    arguments = {"user": "fixture-user", "lease": "lease:1057.1", "session": "c3"}
                    arguments[field] = value
                    with self.assertRaises(RuntimeError):
                        authority.deny_rule(**arguments)

    def test_loaded_marker_requires_successful_registration(self):
        result = self.execute(registrationFails=True)
        self.assertEqual(result["events"], ["register"])
        self.assertEqual(result["attempted"], [])
        self.assertIn("mock registration failed", result["loadError"])

    def test_failed_loaded_logger_propagates_without_qualifying_marker(self):
        result = self.execute(spawnFailsAt=1, subject=self.subject())
        self.assertEqual(result["events"], ["register", "spawn"])
        self.assertEqual(result["delivered"], [])
        self.assertIn("mock logger missing or nonzero exit", result["loadError"])
        self.assertNotIn("answer", result)

    def test_failed_rejecting_logger_still_denies_without_qualifying_marker(self):
        result = self.execute(spawnFailsAt=2, subject=self.subject())
        self.assertEqual(result["answer"], "NO")
        self.assertNotIn("callbackError", result)
        self.assertEqual(len(result["attempted"]), 2)
        self.assertEqual(result["delivered"], [LOGGER_PREFIX + [
            "campus1057-deny-loaded lease=lease:1057.1"]])

    def test_scope_mismatch_has_no_deny_or_rejecting_marker(self):
        for change in ({"user": "other-user"}, {"session": "c4"},
                       {"local": False}, {"active": False}, {"pid": 124}):
            with self.subTest(change=change):
                result = self.execute(pid=123, subject=self.subject(**change))
                self.assertIsNone(result["answer"])
                self.assertEqual(len(result["attempted"]), 1)
        for change in ({"id": "other.action"}, {"program": "/usr/bin/other"}, {"user": "other"}):
            with self.subTest(action_change=change):
                action = {"id": authority.ACTION, "program": authority.PROGRAM, "user": "root", **change}
                result = self.execute(subject=self.subject(), action=action)
                self.assertIsNone(result["answer"])
                self.assertEqual(len(result["attempted"]), 1)

    def test_invalid_runtime_pid_denies_without_marker(self):
        for pid in (None, True, False, 0, 1, -1, 2.5, "123", 2147483648):
            with self.subTest(pid=pid):
                result = self.execute(subject=self.subject(pid=pid))
                self.assertEqual(result["answer"], "NO")
                self.assertNotIn("callbackError", result)
                self.assertEqual(len(result["attempted"]), 1)

    def test_pid_boundaries_preserve_exact_subject_marker(self):
        for pid in (2, 2147483647):
            with self.subTest(pid=pid):
                result = self.execute(pid=pid, subject=self.subject(pid=pid))
                self.assertEqual(result["answer"], "NO")
                self.assertEqual(result["delivered"][-1], LOGGER_PREFIX + [
                    f"campus1057-deny lease=lease:1057.1 pid={pid} user=fixture-user session=c3 active=true"])


if __name__ == "__main__":
    unittest.main()
