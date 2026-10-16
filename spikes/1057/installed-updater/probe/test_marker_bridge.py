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

NONCE = "0123456789abcdef0123456789abcdef"
LOGGER_PREFIX = ["/usr/bin/logger", "--socket-errors=on", "--priority", "user.notice",
                 "--tag", "campus-updater-1057", "--"]
NODE_HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const result = {events: [], attempted: [], delivered: [], diagnostics: []};
let callback;
if (input.subject && input.runtimeField) {
  const key = input.runtimeField[0];
  const kind = input.runtimeField[1];
  if (kind === 'absent') delete input.subject[key];
  else if (kind === 'undefined') input.subject[key] = undefined;
  else if (kind === 'nan') input.subject[key] = NaN;
  else if (kind === 'infinity') input.subject[key] = Infinity;
  else if (kind === 'function') input.subject[key] = function() { throw new Error('must not call field'); };
  else if (kind === 'symbol') input.subject[key] = Symbol('unsupported');
  else if (kind === 'throwing-getter') Object.defineProperty(input.subject, key, {
    get: function() { throw new Error('mock unavailable field'); }, enumerable: true
  });
  else if (kind === 'hostile-object') input.subject[key] = {
    toString: function() { throw new Error('must not coerce object'); },
    toJSON: function() { throw new Error('must not serialize object'); }
  };
}
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
  const context = {polkit: polkit};
  if (input.constructionFails) context.JSON = {stringify: function() { throw new Error('mock construction failed'); }};
  vm.runInNewContext(input.source, context, {timeout: 1000});
} catch (error) {
  result.loadError = String(error);
}
if (callback && input.subject && !result.loadError) {
  const action = {
    id: input.action.id,
    lookup: function(key) { return input.action[key]; }
  };
  try {
    // Independent original authorization predicate, before diagnostic changes.
    // Invalid runtime PID still returns NO when no optional PID filter exists:
    // original rejecting-marker validation catches it and unconditionally denies.
    const s = input.subject;
    result.originalAnswer = action.id === 'dev.campus.updater1057.install' &&
      action.lookup('program') === '/usr/lib/campus-updater-1057/install-deb.py' &&
      action.lookup('user') === 'root' && s.user === input.configuredUser &&
      s.local === true && s.active === true && s.session === input.configuredSession &&
      (input.configuredPid === null || s.pid === input.configuredPid) ? 'NO' : null;
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
                session="c3", nonce=NONCE, subject=None, action=None, **options):
        payload = {
            "source": authority.deny_rule(user, lease, pid=pid, session=session, nonce=nonce).decode(),
            "subject": subject,
            "configuredUser": user, "configuredSession": session, "configuredPid": pid,
            "action": action or {"id": authority.ACTION, "program": authority.PROGRAM, "user": "root"},
            **options,
        }
        completed = subprocess.run(
            [self.node, "-e", NODE_HARNESS], input=json.dumps(payload), text=True,
            capture_output=True, check=True, timeout=5,
            env={"PATH": os.defpath, "LC_ALL": "C"},
        )
        self.assertEqual(completed.stderr, "")
        result = json.loads(completed.stdout)
        if "answer" in result:
            self.assertEqual(result["answer"], result["originalAnswer"], "diagnostic changed original authorization semantics")
        return result

    def subject(self, **overrides):
        return {"user": "fixture-user", "pid": 123, "session": "c3",
                "local": True, "active": True, **overrides}

    def candidate(self, result):
        candidates = [argv for argv in result["delivered"]
                      if argv[-1].startswith("campus1057-deny-candidate ")]
        self.assertEqual(len(candidates), 1)
        argv = candidates[0]
        self.assertEqual(argv[:-1], LOGGER_PREFIX)
        self.assertTrue(argv[-1].isascii())
        self.assertLessEqual(len(argv[-1].encode()), 2048)
        header, payload = argv[-1].split(" {", 1)
        self.assertRegex(header, r"^campus1057-deny-candidate lease=[A-Za-z0-9_.:-]+ nonce=" + NONCE + "$")
        return json.loads("{" + payload)

    def test_fixed_argv_and_exact_single_message_operand(self):
        result = self.execute(subject=self.subject())
        self.assertEqual(result["events"], ["register", "spawn", "spawn", "spawn"])
        self.assertEqual([result["attempted"][0], result["attempted"][-1]], [
            LOGGER_PREFIX + ["campus1057-deny-loaded lease=lease:1057.1 nonce=0123456789abcdef0123456789abcdef"],
            LOGGER_PREFIX + ["campus1057-deny lease=lease:1057.1 nonce=0123456789abcdef0123456789abcdef pid=123 user=fixture-user session=c3 active=true"],
        ])
        self.assertEqual(result["delivered"], result["attempted"])
        self.assertEqual(result["answer"], "NO")
        candidate = self.candidate(result)
        self.assertEqual(candidate["status"], "observed")
        self.assertEqual(candidate["subject_pid"], {"present": True, "type": "number", "value": 123})
        self.assertEqual(candidate["expected_pid"], {"present": False, "type": "undefined"})
        self.assertEqual(set(candidate), {"status", "action_id", "program", "target_user", "subject_pid",
            "subject_user", "subject_local", "subject_active", "subject_session", "expected_session", "expected_pid"})

    def test_valid_punctuation_and_maximum_lengths_stay_one_literal_operand(self):
        user = "_" + "a" * 60 + "_.-"
        lease = "L" + "a" * 122 + "_.:-0"
        session = "s" + "a" * 58 + "_.:-0"
        self.assertEqual((len(user), len(lease), len(session)), (64, 128, 64))
        result = self.execute(user=user, lease=lease, session=session,
                              subject=self.subject(user=user, session=session))
        self.assertEqual(result["answer"], "NO")
        self.assertEqual(result["delivered"][-1], LOGGER_PREFIX + [
            f"campus1057-deny lease={lease} nonce={NONCE} pid=123 user={user} session={session} active=true"])

    def test_untrusted_marker_values_rejected_before_javascript_generation(self):
        for field, values in {
            "user": ["", "0user", "user name", "user\nforged", 'user";throw 1;//',
                     "user$(id)", "user`id`", "user\\escape", "u" * 65, None],
            "lease": ["", "-lease", "lease\nforged", 'lease";throw 1;//',
                      "lease$(id)", "lease`id`", "lease\\escape", "l" * 129, None],
            "session": [None, "", "-session", "session name", "session\nforged",
                        'session";throw 1;//', "session$(id)", "session`id`",
                        "session\\escape", "s" * 65],
            "nonce": [None, "", "0" * 31, "0" * 33, "A" * 32, [NONCE]],
            "pid": [True, False, 0, 1, -1, 2.5, "123", 2147483648],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    arguments = {"user": "fixture-user", "lease": "lease:1057.1", "session": "c3", "nonce": NONCE}
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
        result = self.execute(spawnFailsAt=3, subject=self.subject())
        self.assertEqual(result["answer"], "NO")
        self.assertNotIn("callbackError", result)
        self.assertEqual(len(result["attempted"]), 3)
        self.assertEqual(result["delivered"], result["attempted"][:2])
        self.assertFalse(any(argv[-1].startswith("campus1057-deny ") for argv in result["delivered"]))

    def test_scope_mismatch_has_no_deny_or_rejecting_marker(self):
        for change in ({"user": "other-user"}, {"session": "c4"},
                       {"local": False}, {"active": False}, {"pid": 124}):
            with self.subTest(change=change):
                result = self.execute(pid=123, subject=self.subject(**change))
                self.assertIsNone(result["answer"])
                self.assertEqual(len(result["attempted"]), 1 if "user" in change else 2)
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
                self.assertEqual(len(result["attempted"]), 2)

    def test_pid_boundaries_preserve_exact_subject_marker(self):
        for pid in (2, 2147483647):
            with self.subTest(pid=pid):
                result = self.execute(pid=pid, subject=self.subject(pid=pid))
                self.assertEqual(result["answer"], "NO")
                self.assertEqual(result["delivered"][-1], LOGGER_PREFIX + [
                    f"campus1057-deny lease=lease:1057.1 nonce=0123456789abcdef0123456789abcdef pid={pid} user=fixture-user session=c3 active=true"])


    def test_candidate_records_distinct_false_null_empty_and_wrong_values(self):
        cases = [("local", False, "boolean"), ("active", False, "boolean"),
                 ("session", None, "null"), ("session", "", "string"),
                 ("session", "wrong", "string"), ("pid", 124, "number")]
        for key, value, kind in cases:
            with self.subTest(key=key, value=value):
                result = self.execute(pid=123, subject=self.subject(**{key: value}))
                self.assertIsNone(result["answer"])
                expected = {"present": True, "type": kind}
                if value is not None:
                    expected["value"] = value
                self.assertEqual(self.candidate(result)["subject_" + key], expected)
                self.assertFalse(any(argv[-1].startswith("campus1057-deny ") for argv in result["attempted"]))

    def test_candidate_distinguishes_explicit_undefined_and_absent_property(self):
        for kind, present in (("undefined", True), ("absent", False)):
            with self.subTest(kind=kind):
                result = self.execute(subject=self.subject(), runtimeField=["session", kind])
                self.assertIsNone(result["answer"])
                self.assertEqual(self.candidate(result)["subject_session"],
                                 {"present": present, "type": "undefined"})

    def test_unsupported_nonfinite_and_absent_pid_keep_both_original_scope_results(self):
        for kind in ("nan", "infinity", "function", "symbol", "hostile-object", "undefined", "absent"):
            for configured in (None, 123):
                with self.subTest(kind=kind, configured=configured):
                    result = self.execute(pid=configured, subject=self.subject(), runtimeField=["pid", kind])
                    self.assertEqual(result["answer"], "NO" if configured is None else None)
                    self.assertNotIn("callbackError", result)
                    payload = self.candidate(result)
                    if kind not in ("undefined", "absent"):
                        self.assertEqual(payload["status"], "diagnostic-invalid")
                        self.assertEqual(payload["subject_pid"]["status"], "diagnostic-invalid")
                        self.assertNotIn("value", payload["subject_pid"])

    def test_oversized_and_unsupported_session_cannot_turn_into_a_match(self):
        result = self.execute(subject=self.subject(session="c3" + "x" * 10000))
        self.assertIsNone(result["answer"])
        self.assertEqual(self.candidate(result)["subject_session"],
                         {"present": True, "type": "string", "status": "diagnostic-invalid", "reason": "string-too-long"})
        for kind in ("hostile-object", "function", "symbol"):
            with self.subTest(kind=kind):
                result = self.execute(subject=self.subject(), runtimeField=["session", kind])
                self.assertIsNone(result["answer"])
                self.assertNotIn("callbackError", result)
                self.assertEqual(self.candidate(result)["status"], "diagnostic-invalid")

    def test_complete_message_byte_bound_includes_escaping_and_fixed_scope(self):
        value = '\\"\n' + "\u00e9" * 61
        result = self.execute(subject=self.subject(session=value, command_line="NEVER_CAPTURE_THIS"))
        self.assertIsNone(result["answer"])
        self.assertEqual(self.candidate(result)["subject_session"]["value"], value)
        self.assertNotIn("NEVER_CAPTURE_THIS", json.dumps(result["delivered"]))
        result = self.execute(user="u" * 64, lease="l" * 128, session="s" * 64,
                              subject=self.subject(user="u" * 64, session="\u00e9" * 64,
                                                   local="\u00e9" * 64, active="\u00e9" * 64))
        self.assertIsNone(result["answer"])
        self.assertEqual(self.candidate(result), {"status": "diagnostic-invalid", "reason": "message-size-exceeded"})

    def test_candidate_logger_or_construction_failure_never_changes_original_results(self):
        for failure in ({"spawnFailsAt": 2}, {"constructionFails": True}):
            for change in ({}, {"local": False}, {"active": False}, {"session": None},
                           {"session": ""}, {"session": "wrong"}, {"pid": 124}):
                with self.subTest(failure=failure, change=change):
                    result = self.execute(pid=123, subject=self.subject(**change), **failure)
                    self.assertEqual(result["answer"], None if change else "NO")
                    self.assertNotIn("callbackError", result)
                    self.assertFalse(any(argv[-1].startswith("campus1057-deny-candidate ")
                                         for argv in result["delivered"]))
                    self.assertEqual(any(argv[-1].startswith("campus1057-deny ")
                                         for argv in result["delivered"]), not bool(change))

    def test_throwing_field_diagnostic_is_unavailable_and_original_result_remains(self):
        for local, expected in ((False, None), (True, "NO")):
            with self.subTest(local=local):
                result = self.execute(subject=self.subject(local=local), runtimeField=["pid", "throwing-getter"])
                self.assertEqual(result["answer"], expected)
                self.assertNotIn("callbackError", result)
                self.assertEqual(len(result["attempted"]), 1)

    def test_allowed_scope_literals_cannot_be_reinterpreted_as_template_tokens(self):
        user = "__SESSION____PREFIX__"
        lease = "L__PID____PID_PRESENT__"
        session = "s__SCOPE____CANDIDATE__"
        result = self.execute(user=user, lease=lease, session=session,
                              subject=self.subject(user=user, session=session))
        self.assertEqual(result["answer"], "NO")
        candidate = self.candidate(result)
        self.assertEqual(candidate["subject_user"]["value"], user)
        self.assertEqual(candidate["subject_session"]["value"], session)
        self.assertEqual(candidate["expected_session"]["value"], session)
        self.assertIn("lease=" + lease, result["delivered"][1][-1])


if __name__ == "__main__":
    unittest.main()
