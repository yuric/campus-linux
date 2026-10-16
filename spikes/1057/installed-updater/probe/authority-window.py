#!/usr/bin/env python3
"""Leased, root-operated GDM negative-evidence window; never acquires privilege.

Prepared source only: this helper must not run before the coordinator grants the
execution lease. Stage the reviewed SHA-bound bytes in a fresh root-owned,
nonwritable directory and invoke /usr/bin/python3 -I -B from an existing independent
root control session. The installed fixture runs in its existing GDM user session.

A killed process cannot execute finally. Recovery from that independent root
session: inspect the receipt; remove ONLY the recorded matching fixture deny rule,
or, for a recorded owned /run/systemd/system/polkit.service -> /dev/null mask, run
systemctl --runtime unmask polkit.service; systemctl start polkit.service. Verify
active state and the org.freedesktop.PolicyKit1 bus owner. Never remove a preexisting
mask or rule. No sudo, authentication agent, password input or allow rule is used.
"""

import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import shlex
import signal
import stat
import subprocess
import sys
import time


RULE = Path("/etc/polkit-1/rules.d/00-campus-updater-1057-deny.rules")
MASK = Path("/run/systemd/system/polkit.service")
ACTION = "dev.campus.updater1057.install"
PROGRAM = "/usr/lib/campus-updater-1057/install-deb.py"
BUS_NAME = "org.freedesktop.PolicyKit1"
LOGGER = "/usr/bin/logger"
LOGGER_TAG = "campus-updater-1057"
LOGGER_ARGV = [LOGGER, "--socket-errors=on", "--priority", "user.notice",
               "--tag", LOGGER_TAG, "--"]
PROPERTIES = "Id,LoadState,ActiveState,SubState,UnitFileState,FragmentPath,DropInPaths"
SERVICE_PROPERTIES = PROPERTIES + ",MainPID,ControlGroup"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def safe_root_parent(path, private=False):
    require(path.is_absolute(), "absolute path required")
    require(path.resolve(strict=True) == path, "symlinked parent refused")
    for component in (path, *path.parents):
        info = component.stat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0
                and not info.st_mode & 0o022, "parent is not root-controlled")
    if private:
        require(not path.stat().st_mode & 0o077, "receipt parent must be root-private")


def staged_source(path, expected_sha256):
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha256), "invalid reviewed source SHA-256")
    require(path.is_absolute() and path.resolve(strict=True) == path,
            "authority helper must have an absolute nonsymlinked path")
    safe_root_parent(path.parent, private=True)
    require(not path.parent.stat().st_mode & 0o222, "staged helper directory must be nonwritable")
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o222,
            "staged helper must be a root-owned nonwritable regular file")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    require(digest == expected_sha256, "staged helper differs from reviewed source SHA-256")
    return {"path": str(path), "sha256": digest, "uid": info.st_uid,
            "mode": oct(stat.S_IMODE(info.st_mode)), "isolated_python": True,
            "bytecode_disabled": True}


def decimal(value, minimum=0, maximum=2**63 - 1):
    return (type(value) is str and len(value) <= len(str(maximum))
            and re.fullmatch(r"0|[1-9][0-9]*", value) is not None
            and minimum <= int(value) <= maximum)


def require_service_binding(binding):
    require(type(binding) is dict and decimal(binding.get("uid"), 1)
            and decimal(binding.get("gid"), 1) and binding.get("account") == "polkitd"
            and binding.get("nss_users") == ["polkitd"]
            and binding.get("logger_exe") == LOGGER and binding.get("unit") == "polkit.service",
            "missing reliable service binding")
    uid, gid = binding["uid"], binding["gid"]
    require(type(binding.get("account_primary_gid")) is int and binding["account_primary_gid"] > 0
            and type(binding.get("account_groups")) is list
            and all(type(value) is int and value > 0 for value in binding["account_groups"])
            and int(gid) in binding["account_groups"], "missing dedicated account GID membership")
    process, state = binding.get("process"), binding.get("service_state")
    require(type(process) is dict and type(state) is dict, "missing service process context")
    require(type(binding.get("main_pid")) is int and 1 < binding["main_pid"] <= 2147483647
            and decimal(binding.get("starttime"), 1) and process.get("pid") == binding["main_pid"]
            and process.get("starttime") == binding["starttime"]
            and process.get("uids") == [uid] * 4 and process.get("gids") == [gid] * 4
            and binding.get("same_uid_processes") == [process], "invalid dedicated service process identity")
    require(type(binding.get("exe")) is str and binding["exe"].startswith("/")
            and process.get("exe") == binding["exe"] and type(binding.get("cgroup")) is str
            and process.get("cgroup") == binding["cgroup"]
            and state.get("Id") == "polkit.service" and state.get("LoadState") == "loaded"
            and state.get("ActiveState") == "active" and state.get("SubState") == "running"
            and not state.get("DropInPaths") and state.get("MainPID") == str(binding["main_pid"])
            and type(state.get("ControlGroup")) is str and state["ControlGroup"].startswith("/")
            and any(len(parts) == 3 and parts[2] == state["ControlGroup"]
                    for parts in (line.split(":", 2) for line in binding["cgroup"].splitlines())),
            "invalid service executable/cgroup context")
    for name, path in (("logger", LOGGER), ("executable", binding["exe"])):
        receipt = binding.get(name)
        require(type(receipt) is dict and receipt.get("path") == path and receipt.get("uid") == 0
                and type(receipt.get("mode")) is int and not receipt["mode"] & 0o6022
                and receipt["mode"] & 0o111 and type(receipt.get("sha256")) is str
                and re.fullmatch(r"[0-9a-f]{64}", receipt["sha256"]), "missing trusted " + name + " receipt")
    require(type(binding.get("boot_id")) is str and re.fullmatch(r"[0-9a-f]{32}", binding["boot_id"]),
            "missing service boot identity")


def validate_marker_rows(rows, expected_message, nonce, lease, binding, boot_id, start_ns, end_ns):
    """Pure receipt validation. The nonce correlates an attempt; it is not secret.

    Missing optional process metadata establishes account attribution only, not
    kernel proof of executable/parent service. Root and the dedicated service
    account remain trusted in this controlled disposable guest.
    """
    require(type(nonce) is str and re.fullmatch(r"[0-9a-f]{32}", nonce), "invalid marker nonce")
    require(type(lease) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", lease),
            "invalid marker lease")
    require(type(expected_message) is str and " lease=" + lease + " nonce=" + nonce in expected_message,
            "expected marker does not bind lease and nonce")
    require_service_binding(binding)
    require(type(boot_id) is str and re.fullmatch(r"[0-9a-f]{32}", boot_id), "invalid boot binding")
    require(binding["boot_id"] == boot_id, "service boot disagrees with journal window")
    require(type(start_ns) is int and type(end_ns) is int and 0 < start_ns <= end_ns,
            "invalid marker receipt time window")
    evidence = {"accepted": [], "rejected": [], "missing_optional_fields": [], "anomalies": []}
    for index, row in enumerate(rows):
        reasons = []
        candidate = nonce in json.dumps(row.get("MESSAGE") if type(row) is dict else row)
        if type(row) is not dict:
            reasons.append("journal row is not an object")
        else:
            for field, expected in (("MESSAGE", expected_message), ("SYSLOG_IDENTIFIER", LOGGER_TAG),
                                    ("_UID", binding["uid"]), ("_GID", binding["gid"]),
                                    ("_TRANSPORT", "syslog"), ("_BOOT_ID", boot_id)):
                if type(row.get(field)) is not str or row[field] != expected:
                    reasons.append("missing/malformed/mismatched " + field)
            if not decimal(row.get("_PID"), 2, 2147483647):
                reasons.append("missing/malformed kernel sender _PID")
            # Realtime reception clocks are bounded; boot-bound monotonic time
            # is retained for independent correlation when available.
            if not decimal(row.get("__REALTIME_TIMESTAMP"), 1):
                reasons.append("missing/malformed __REALTIME_TIMESTAMP")
            elif not start_ns <= int(row["__REALTIME_TIMESTAMP"]) * 1000 <= end_ns:
                reasons.append("journal reception time outside window")
            for field in ("__MONOTONIC_TIMESTAMP", "_SOURCE_REALTIME_TIMESTAMP"):
                if field in row:
                    if not decimal(row[field], 1):
                        reasons.append("malformed " + field)
                    elif field == "_SOURCE_REALTIME_TIMESTAMP" and not start_ns <= int(row[field]) * 1000 <= end_ns:
                        reasons.append("source reception time outside window")
            missing = []
            for field, expected in (("_EXE", binding["logger_exe"]), ("_SYSTEMD_UNIT", binding["unit"])):
                if field not in row:
                    missing.append(field)
                elif type(row[field]) is not str or row[field] != expected:
                    reasons.append("contradictory/malformed optional " + field)
            evidence["missing_optional_fields"].append({"row_index": index, "fields": missing})
        if reasons:
            rejection = {"row": row, "reasons": reasons, "current_nonce": candidate}
            evidence["rejected"].append(rejection)
            if candidate:
                evidence["anomalies"].append(rejection)
        else:
            evidence["accepted"].append(row)
    return evidence


def root_executable(path):
    require(path.is_absolute() and path.resolve(strict=True) == path, "noncanonical service executable")
    safe_root_parent(path.parent)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o6022
            and info.st_mode & 0o111, "service executable is not root-controlled")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "uid": info.st_uid, "mode": stat.S_IMODE(info.st_mode)}


def process_identity(pid):
    proc = Path("/proc") / str(pid)
    status = dict(line.split(":", 1) for line in (proc / "status").read_text().splitlines() if ":" in line)
    ids = {name: status.get(name, "").split() for name in ("Uid", "Gid")}
    require(all(len(values) == 4 and all(decimal(v) for v in values) for values in ids.values()),
            "missing process real/effective/saved/filesystem credentials")
    raw_stat = (proc / "stat").read_text()
    tail = raw_stat.rsplit(")", 1)[1].split()
    require(len(tail) > 19 and decimal(tail[19], 1), "missing process starttime")
    exe = os.readlink(proc / "exe")
    cgroup = (proc / "cgroup").read_text()
    require(cgroup.strip(), "missing process cgroup")
    return {"pid": pid, "starttime": tail[19], "exe": exe, "cgroup": cgroup,
            "uids": ids["Uid"], "gids": ids["Gid"]}


def require_null_binding(binding, user, lease, pid, session, nonce):
    require(type(binding) is dict and binding.get("mode") == "root-correlated-user-manager",
            "explicit complete root binding required")
    require(binding.get("lease") == lease and binding.get("nonce") == nonce
            and type(pid) is int and binding.get("app", {}).get("pid") == pid,
            "null denial requires exact app PID/lease/nonce")
    app, recorder = binding["app"], binding.get("recorder", {})
    require(decimal(app.get("starttime"), 1) and app.get("exe") == "/usr/bin/campus-updater-1057"
            and type(app.get("exe_identity")) is list and len(app["exe_identity"]) == 4
            and len(app.get("uids", [])) == 4 and len(set(app["uids"])) == 1
            and decimal(app["uids"][0], 1) and len(app.get("gids", [])) == 4 and len(set(app["gids"])) == 1
            and app.get("ppid") == recorder.get("pid") and decimal(recorder.get("starttime"), 1),
            "incomplete app/retaining parent lifetime")
    custody = binding.get("custody", {})
    selected = custody.get("session", {})
    require(selected.get("Id") == session and selected.get("User") == app["uids"][0]
            and selected.get("Active") == "yes" and selected.get("Remote") == "no"
            and selected.get("State") == "active" and selected.get("Class") == "user"
            and selected.get("Type") in ("wayland", "x11") and selected.get("Service", "").startswith("gdm-")
            and selected.get("Seat") and custody.get("leader_logind", {}).get("session") == session,
            "missing selected GDM custody")
    direct = binding.get("direct_logind", {})
    require(direct.get("session") is None and type(direct.get("session_result")) is int
            and direct["session_result"] < 0 and direct.get("owner_uid") == int(app["uids"][0]),
            "missing actual null user-manager observation")
    require(type(binding.get("boot_id")) is str and re.fullmatch(r"[0-9a-f]{32}", binding["boot_id"])
            and type(binding.get("app_sha256")) is str and re.fullmatch(r"[0-9a-f]{64}", binding["app_sha256"])
            and all(type(binding.get(key)) is dict and binding[key].get("pid", 0) > 1
                    for key in ("driver", "server", "terminal"))
            and type(binding.get("ancestry")) is list and 0 < len(binding["ancestry"]) <= 8
            and type(binding.get("sources")) is dict and binding["sources"], "incomplete root custody/source binding")
    times = [binding.get("app_started_ns"), binding.get("request", {}).get("waiting_ns"), binding.get("bound_ns")]
    require(all(type(t) is int and t > 0 for t in times) and times == sorted(times)
            and binding.get("app_deadline_ns") == times[0] + 20_000_000_000
            and type(binding.get("gate_deadline_ns")) is int
            and times[-1] < binding["gate_deadline_ns"] <= times[0] + 8_000_000_000,
            "incomplete bounded root binding timing")


def deny_rule(user, lease, pid=None, session=None, *, nonce, null_binding=None):
    # Restrict each diagnostic operand independently; JSON serialization remains
    # mandatory for JavaScript literals. No shell or caller-selected executable.
    require(isinstance(user, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,63}", user),
            "invalid fixture subject user")
    require(isinstance(lease, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", lease),
            "invalid explicit lease identifier")
    require(isinstance(session, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", session),
            "deny requires a bounded explicit subject session")
    require(pid is None or (type(pid) is int and 1 < pid <= 2147483647), "invalid subject PID")
    require(type(nonce) is str and re.fullmatch(r"[0-9a-f]{32}", nonce), "invalid marker nonce")
    # Polkit 124 exposes subject.user, not subject.uid. The caller validates the
    # exact UID/name mapping through NSS before creating this deny-only rule.
    checks = [f"action.id === {json.dumps(ACTION)}",
              f"action.lookup('program') === {json.dumps(PROGRAM)}",
              "action.lookup('user') === 'root'",
              f"subject.user === {json.dumps(user)}", "subject.local === true",
              "subject.active === true",
              f"subject.session === {json.dumps(session)}"]
    if null_binding is not None:
        require_null_binding(null_binding, user, lease, pid, session, nonce)
        checks[-1] = "subject.session === null"
    if pid is not None:
        checks.append(f"subject.pid === {pid}")
    marker = json.dumps("campus1057-deny lease=" + lease + " nonce=" + nonce)
    suffix = ""
    if null_binding is not None:
        binding_hash = hashlib.sha256((json.dumps(null_binding, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
        suffix = " mode=root-correlated-user-manager binding=" + binding_hash
    loaded = json.dumps("campus1057-deny-loaded lease=" + lease + " nonce=" + nonce)
    prefix = json.dumps(LOGGER_ARGV)
    # Diagnostic-only callback snapshot: its narrower outer gate grants nothing.
    # Keep the original predicate/return paths below intact, including NO for an
    # otherwise matching subject whose PID fails the existing marker validation.
    candidate = json.dumps("campus1057-deny-candidate lease=" + lease + " nonce=" + nonce)
    diagnostic = r"""  try {
    if (__SCOPE__) {
      var diagnosticValid = true;
      var typed = function(value, present, kind, limit) {
        var type = value === null ? 'null' : typeof value;
        var field = {present: present, type: type};
        function invalid(reason) {
          diagnosticValid = false;
          field.status = 'diagnostic-invalid';
          field.reason = reason;
          return field;
        }
        if (type === 'undefined' || type === 'null') return field;
        if (type === 'string') {
          if (value.length > limit) return invalid('string-too-long');
          field.value = value;
          return kind === 'string' ? field : invalid('unexpected-type');
        }
        if (type === 'boolean') {
          field.value = value;
          return kind === 'boolean' ? field : invalid('unexpected-type');
        }
        if (type === 'number') {
          if (kind !== 'pid' || !isFinite(value) || value < 2 ||
              value > 2147483647 || Math.floor(value) !== value)
            return invalid('invalid-number');
          field.value = value;
          return field;
        }
        // Do not coerce, inspect or serialize unsupported objects/functions.
        return invalid('unsupported-type');
      };
      var subjectField = function(key, kind, limit) {
        return typed(subject[key], Object.prototype.hasOwnProperty.call(subject, key), kind, limit);
      };
      var payload = {
        action_id: typed(action.id, true, 'string', 128),
        program: typed(action.lookup('program'), true, 'string', 128),
        target_user: typed(action.lookup('user'), true, 'string', 64),
        subject_pid: subjectField('pid', 'pid', 64),
        subject_user: subjectField('user', 'string', 64),
        subject_local: subjectField('local', 'boolean', 64),
        subject_active: subjectField('active', 'boolean', 64),
        subject_session: subjectField('session', 'string', 64),
        expected_session: typed(__SESSION__, true, 'string', 64),
        expected_pid: typed(__PID__, __PID_PRESENT__, 'pid', 64)
      };
      payload.status = diagnosticValid ? 'observed' : 'diagnostic-invalid';
      // ASCII-escape non-ASCII UTF-16 units so length bounds the actual UTF-8
      // bytes, including JSON escaping and the complete lease/nonce prefix.
      var encoded = JSON.stringify(payload).replace(/[\u007f-\uffff]/g, function(character) {
        return '\\u' + ('0000' + character.charCodeAt(0).toString(16)).slice(-4);
      });
      var candidatePrefix = __CANDIDATE__;
      var message = candidatePrefix + ' ' + encoded;
      if (message.length > 2048)
        message = candidatePrefix + ' {"status":"diagnostic-invalid","reason":"message-size-exceeded"}';
      polkit.spawn(__PREFIX__.concat([message]));
    }
  } catch (diagnosticError) {
    // Unavailable diagnostics never alter the original authorization result.
  }
"""
    substitutions = {"__SCOPE__": " && ".join(checks[:4]), "__SESSION__": json.dumps(session),
                     "__PID__": "undefined" if pid is None else str(pid),
                     "__PID_PRESENT__": "false" if pid is None else "true",
                     "__CANDIDATE__": candidate, "__PREFIX__": prefix}
    # Replace template tokens once; permitted literal scope values may themselves
    # contain these strings and must never be reinterpreted as template syntax.
    diagnostic = re.sub("|".join(map(re.escape, substitutions)),
                        lambda match: substitutions[match.group()], diagnostic)
    return ("polkit.addRule(function(action, subject) {\n"
            + diagnostic +
            "  if (" + " && ".join(checks) + ") {\n"
            "    try {\n"
            "      if (typeof subject.pid !== 'number' || subject.pid < 2 ||\n"
            "          subject.pid > 2147483647 || Math.floor(subject.pid) !== subject.pid)\n"
            "        throw new Error('invalid fixture subject PID');\n"
            f"      polkit.spawn({prefix}.concat([{marker} + ' pid=' + subject.pid"
            " + ' user=' + subject.user + ' session=' + subject.session"
            " + ' active=' + subject.active" + (" + " + json.dumps(suffix) if suffix else "") + "]));\n"
            "    } catch (error) {\n"
            "      // Never fall through to authentication on a logging failure.\n"
            "      // Absence of the exact rejecting marker invalidates evidence.\n"
            "      return polkit.Result.NO;\n"
            "    }\n"
            "    return polkit.Result.NO;\n  }\n});\n"
            # Registration must succeed before its loaded marker can be emitted.
            f"polkit.spawn({prefix}.concat([{loaded}]));\n").encode()


class Window:
    def __init__(self, args, receipt_fd):
        self.args, self.fd = args, receipt_fd
        self.deadline = None
        self.started_at = None
        self.total_deadline = None
        self.owned = None
        self.rule_bytes = None
        self.initial = None
        self.record = {"scope": "leased GDM negative preparation only", "mode": args.mode,
                       "lease": args.lease, "uid": args.uid,
                       "authority_helper": args.source_receipt,
                       "shared_authority_window_acknowledged": args.allow_shared_authority_window,
                       "requested_seconds": args.duration_seconds, "commands": [],
                       "status": "preparing", "cleanup": "not_needed"}
        self.save()

    def save(self):
        data = (json.dumps(self.record, indent=2) + "\n").encode()
        os.lseek(self.fd, 0, os.SEEK_SET)
        os.write(self.fd, data)
        os.ftruncate(self.fd, len(data))
        os.fsync(self.fd)

    def run(self, argv, ok=True, restoring=False, timeout_seconds=5.0):
        timeout = 2.0 if restoring else min(5.0, timeout_seconds)
        if self.deadline is not None and not restoring:
            timeout = min(timeout, self.deadline - time.monotonic())
            require(timeout > 0, "authority window deadline reached")
        try:
            result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                    text=True, timeout=timeout, check=False,
                                    env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C"})
        except subprocess.TimeoutExpired:
            self.record["commands"].append({"argv": argv, "timeout": timeout})
            self.save()
            raise RuntimeError("bounded command timed out") from None
        self.record["commands"].append({"argv": argv, "exit": result.returncode,
                                        "stdout": result.stdout[:8192],
                                        "stderr": result.stderr[:8192],
                                        "output_truncated": max(len(result.stdout), len(result.stderr)) > 8192})
        self.save()
        if ok:
            require(result.returncode == 0, "required command failed: " + argv[0])
        return result

    def arm_deadline(self):
        self.started_at = time.monotonic()
        self.total_deadline = self.started_at + self.args.duration_seconds
        # Four bounded restoration commands fit inside this reserve. If the OS
        # delays them anyway, report an overrun and still attempt restoration.
        self.deadline = self.total_deadline - 10
        self.record["cleanup_reserve_seconds"] = 10
        self.record["window_started_unix_ns"] = time.time_ns()

    def state(self, restoring=False):
        result = self.run(["/usr/bin/systemctl", "show", "polkit.service",
                           "--property=" + PROPERTIES], restoring=restoring)
        return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)

    def owner(self, restoring=False):
        result = self.run(["/usr/bin/busctl", "--system", "--timeout=3", "call",
                           "org.freedesktop.DBus", "/org/freedesktop/DBus",
                           "org.freedesktop.DBus", "NameHasOwner", "s", BUS_NAME],
                          restoring=restoring)
        require(result.stdout.strip() in ("b true", "b false"), "unexpected bus owner response")
        return result.stdout.strip() == "b true"

    def bind_service(self, restoring=False):
        context_deadline = time.monotonic() + (2 if restoring else 5)
        if self.total_deadline is not None:
            context_deadline = min(context_deadline, self.total_deadline if restoring else self.deadline)
        result = self.run(["/usr/bin/systemctl", "show", "polkit.service",
                           "--property=" + SERVICE_PROPERTIES], restoring=restoring)
        state = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        observed = {"restoring": restoring, "state": state}
        self.record.setdefault("service_context_observations", []).append(observed)
        require(state.get("Id") == "polkit.service" and state.get("LoadState") == "loaded"
                and state.get("ActiveState") == "active" and state.get("SubState") == "running"
                and not state.get("DropInPaths") and decimal(state.get("MainPID"), 2, 2147483647)
                and state.get("ControlGroup", "").startswith("/"), "unreliable polkit service context")
        account = pwd.getpwnam("polkitd")
        require(account.pw_name == "polkitd" and account.pw_uid > 0
                and account.pw_uid != self.args.uid
                and pwd.getpwuid(account.pw_uid).pw_name == account.pw_name,
                "polkit requires a distinct dedicated NSS identity")
        nss_users = [entry.pw_name for entry in pwd.getpwall() if entry.pw_uid == account.pw_uid]
        require(nss_users == [account.pw_name], "polkit UID has another NSS identity")
        process = process_identity(int(state["MainPID"]))
        observed["process"] = process
        require(process["uids"] == [str(account.pw_uid)] * 4,
                "polkit process credentials disagree with dedicated NSS account")
        gid = process["gids"][0]
        account_groups = sorted(os.getgrouplist(account.pw_name, account.pw_gid))
        require(decimal(gid, 1) and process["gids"] == [gid] * 4
                and int(gid) in account_groups,
                "polkit process real GID is not a dedicated account group")
        groups = [line.split(":", 2) for line in process["cgroup"].splitlines()]
        require(any(len(row) == 3 and row[2] == state["ControlGroup"] for row in groups),
                "polkit MainPID cgroup does not match service")
        executable = root_executable(Path(process["exe"]))
        logger = root_executable(Path(LOGGER))
        inventory = []
        observed["same_uid_processes"] = inventory
        for count, proc in enumerate(Path("/proc").iterdir(), 1):
            require(count <= 4096, "service process inventory exceeds controlled-guest bound")
            require(time.monotonic() < context_deadline, "service identity collection deadline reached")
            if not proc.name.isdecimal():
                continue
            if self.deadline is not None and not restoring:
                require(time.monotonic() < self.deadline, "service inventory deadline reached")
            try:
                raw = (proc / "status").read_text()
            except FileNotFoundError:
                continue  # A vanished unrelated PID cannot supply a marker.
            status = dict(line.split(":", 1) for line in raw.splitlines() if ":" in line)
            if str(account.pw_uid) in status.get("Uid", "").split():
                inventory.append(process_identity(int(proc.name)))
        inventory.sort(key=lambda row: row["pid"])
        require(inventory == [process], "unexplained same-UID process or changing polkit identity")
        require(process_identity(process["pid"]) == process, "polkit process changed during binding")
        require(time.monotonic() < context_deadline, "service identity collection deadline reached")
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip().replace("-", "")
        require(re.fullmatch(r"[0-9a-f]{32}", boot_id), "missing service boot identity")
        binding = {"uid": str(account.pw_uid), "gid": gid, "account": account.pw_name,
                "account_primary_gid": account.pw_gid, "unit": "polkit.service", "logger_exe": LOGGER,
                "account_groups": account_groups, "nss_users": nss_users,
                "main_pid": process["pid"], "starttime": process["starttime"],
                "exe": process["exe"], "cgroup": process["cgroup"], "process": process,
                "same_uid_processes": inventory, "service_state": state, "boot_id": boot_id,
                "executable": executable, "logger": logger}
        require_service_binding(binding)
        return binding

    def recheck_service(self, label, restoring=False):
        try:
            binding = self.bind_service(restoring=restoring)
            self.record[label] = binding
            require(binding == self.record.get("service_binding"), "polkit service identity changed")
        except Exception as error:
            self.record["service_identity_valid"] = False
            self.record[label + "_error"] = str(error)
            self.save()
            raise
        self.save()

    def check_owned_rule(self):
        info = RULE.lstat()
        require((info.st_dev, info.st_ino) == self.owned and not stat.S_ISLNK(info.st_mode),
                "owned rule identity changed; refusing removal/acceptance")
        require(RULE.read_bytes() == self.rule_bytes, "deny rule changed; refusing removal/acceptance")

    def wait_loaded_marker(self):
        # Read actual journal evidence, not polkit.log's discarded stderr or a
        # rule count. This wait consumes the existing observation budget.
        nonce = self.record["marker_nonce"]
        expected = "campus1057-deny-loaded lease=" + self.args.lease + " nonce=" + nonce
        binding, boot_id = self.record["service_binding"], self.record["boot_id"]
        self.record["marker_bridge"] = {
            "argv_prefix": LOGGER_ARGV, "expected_loaded_message": expected,
            "daemon_uid": binding["uid"], "daemon_gid": binding["gid"], "boot_id": boot_id,
            "systemd_unit": "polkit.service", "loaded_wait_max_seconds": 5,
            "rejecting_marker_required_for_case_acceptance": True,
            "attribution": "trusted dedicated polkit account and owned rule in controlled guest; "
                           "no executable/parent proof when optional metadata is absent; "
                           "no claim against root or same-account compromise",
        }
        self.record["loaded_marker_observations"] = []
        self.save()
        until = min(self.deadline, (self.started_at if getattr(self, "gated_context", None) else time.monotonic()) + 5)
        argv = ["/usr/bin/journalctl", "--no-pager", "--output=json", "--lines=65",
                "--since=@" + str(self.record["window_started_unix_ns"] // 1_000_000_000),
                "_UID=" + binding["uid"], "_GID=" + binding["gid"],
                "_TRANSPORT=syslog", "_BOOT_ID=" + boot_id,
                # Also retain tag candidates with missing/contradictory trusted
                # fields, so a good row cannot conceal a current-nonce anomaly.
                "+", "SYSLOG_IDENTIFIER=" + LOGGER_TAG]
        while time.monotonic() < until:
            result = self.run(argv, timeout_seconds=until - time.monotonic())
            observed = time.time_ns()
            rows = []
            for line in result.stdout.splitlines():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    rows.append(line)  # Preserve malformed current-nonce candidates too.
            evidence = validate_marker_rows(rows, expected, nonce, self.args.lease, binding, boot_id,
                                            self.record["window_started_unix_ns"], observed)
            self.record["loaded_marker_observations"].append({"observed_unix_ns": observed,
                                                              "evidence": evidence})
            self.record["loaded_marker_evidence"] = evidence
            self.save()
            require(len(json.dumps(self.record).encode()) < 768 * 1024,
                    "loaded marker receipt exceeds bounded evidence budget")
            require(len(rows) < 65, "loaded journal candidate limit reached; complete evidence unavailable")
            require(time.monotonic() <= until, "loaded marker observation exceeded bounded wait")
            require(not evidence["anomalies"], "contradictory current-nonce loaded marker candidate")
            if evidence["accepted"]:
                self.record["loaded_marker"] = evidence["accepted"][0]
                self.record["loaded_marker_observed_unix_ns"] = observed
                self.record["loaded_marker_observed_monotonic_ns"] = time.monotonic_ns()
                self.save()
                return
            time.sleep(max(0, min(0.1, until - time.monotonic())))
        raise RuntimeError("required exact loaded logger marker absent; logging/registration prerequisite failed")

    def begin(self):
        gated_context = getattr(self, "gated_context", None)
        if gated_context:
            gate, config, hint, request = gated_context
            require(self.args.mode == "deny" and self.args.uid == config["uid"]
                    and self.args.session_id == config["session_id"] and self.args.lease == config["lease"],
                    "gated mode is denial only and must match root scope")
            require(gate.config_read(self.args.gate_directory) == config, "gate config changed")
            binding = gate.actual_binding(config, hint, request)
            self.record["user_manager_binding"] = binding
            self.args.subject_pid = binding["app"]["pid"]
        account = pwd.getpwuid(self.args.uid)
        require(pwd.getpwnam(account.pw_name).pw_uid == self.args.uid, "ambiguous NSS identity")
        self.record["user"] = account.pw_name
        if self.args.subject_pid is not None:
            proc = Path("/proc") / str(self.args.subject_pid)
            require(proc.stat().st_uid == self.args.uid, "subject PID does not belong to UID")
            self.record["subject_pid"] = self.args.subject_pid
            self.record["subject_stat"] = (proc / "stat").read_text()[:4096]
        self.record["subject_session"] = self.args.session_id
        if self.args.mode == "deny":
            safe_root_parent(RULE.parent)
            require(not os.path.lexists(RULE), "fixture deny rule already exists")
            self.arm_deadline()
            self.record["service_binding"] = self.bind_service()
            require_service_binding(self.record["service_binding"])
            self.record["boot_id"] = self.record["service_binding"]["boot_id"]
            require(re.fullmatch(r"[0-9a-f]{32}", self.record["boot_id"]), "invalid current boot")
            self.record["marker_nonce"] = config["nonce"] if gated_context else secrets.token_hex(16)
            self.record["service_identity_valid"] = False
            # Persist the fresh helper-generated nonce and binding before the
            # first owned rule byte can become visible to polkit.
            self.save()
            self.rule_bytes = deny_rule(account.pw_name, self.args.lease,
                                        self.args.subject_pid, self.args.session_id,
                                        nonce=self.record["marker_nonce"],
                                        null_binding=self.record.get("user_manager_binding"))
            if gated_context:
                gate.recheck(binding, config, min(binding["gate_deadline_ns"], int(self.deadline * 1e9)))
                gate.no_pkexec(binding["app"]["pid"])
            fd = os.open(RULE, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
            try:
                os.fchmod(fd, 0o644)
                self.owned = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
                self.record["owned_device_inode"] = list(self.owned)
                self.record["owned_path"] = str(RULE)
                self.record["rule_sha256"] = hashlib.sha256(self.rule_bytes).hexdigest()
                self.save()
                os.write(fd, self.rule_bytes)
                os.fsync(fd)
            finally:
                os.close(fd)
            self.wait_loaded_marker()
            self.recheck_service("service_binding_before_ready")
            self.check_owned_rule()
            self.record["ready_caveat"] = "Loaded marker verified; require exact rejecting subject/session logger marker for actual refusal evidence"
        else:
            require(self.args.allow_shared_authority_window,
                    "missing mode requires explicit shared-authority-window acknowledgement")
            safe_root_parent(MASK.parent)
            for path in (MASK, Path("/etc/systemd/system/polkit.service")):
                require(not os.path.lexists(path), "existing polkit unit override or mask")
            self.initial = self.state()
            require(self.initial.get("Id") == "polkit.service"
                    and self.initial.get("LoadState") == "loaded"
                    and self.initial.get("ActiveState") == "active"
                    and self.initial.get("SubState") == "running"
                    and not self.initial.get("DropInPaths"), "polkit must initially be active without overrides")
            require(self.owner(), "initial authority has no bus owner")
            service = None
            for directory in ("/etc/dbus-1/system-services", "/run/dbus-1/system-services",
                              "/usr/local/share/dbus-1/system-services", "/usr/share/dbus-1/system-services"):
                candidate = Path(directory) / (BUS_NAME + ".service")
                if candidate.exists():
                    service = candidate
                    break
            require(service is not None, "polkit D-Bus activation file missing")
            content = service.read_text()
            config = configparser.ConfigParser(interpolation=None)
            config.read_string(content)
            require(config.get("D-BUS Service", "Name") == BUS_NAME
                    and config.get("D-BUS Service", "SystemdService") == "polkit.service",
                    "D-Bus activation does not target polkit.service")
            features = self.run(["/usr/bin/busctl", "--system", "--timeout=3", "get-property",
                                 "org.freedesktop.DBus", "/org/freedesktop/DBus",
                                 "org.freedesktop.DBus", "Features"])
            require("SystemdActivation" in shlex.split(features.stdout), "systemd bus activation unavailable")
            self.record.update(initial_state=self.initial, activation_file=str(service),
                               activation_sha256=hashlib.sha256(content.encode()).hexdigest())
            self.arm_deadline()
            # Record ownership even if systemctl succeeds in masking but times out
            # waiting for stop; finally must still attempt restoration.
            try:
                self.run(["/usr/bin/systemctl", "--runtime", "--now", "mask", "polkit.service"])
            finally:
                if MASK.is_symlink() and os.readlink(MASK) == "/dev/null":
                    info = MASK.lstat()
                    self.owned = (info.st_dev, info.st_ino)
                    self.record["owned_device_inode"] = list(self.owned)
                    self.record["owned_path"] = str(MASK)
                    self.save()
            require(self.owned is not None, "runtime mask was not created")
            state = self.state()
            require(state.get("LoadState") == "masked" and state.get("ActiveState") == "inactive",
                    "authority did not become masked and inactive")
            require(not self.owner(), "authority still owns system bus name")
            activation = self.run(["/usr/bin/busctl", "--system", "--timeout=3", "call",
                                   "org.freedesktop.DBus", "/org/freedesktop/DBus",
                                   "org.freedesktop.DBus", "StartServiceByName", "su", BUS_NAME, "0"], ok=False)
            require(activation.returncode != 0 and "polkit.service" in activation.stderr
                    and "masked" in activation.stderr, "activation was not rejected at the runtime mask")
            require(not self.owner(), "authority appeared after activation attempt")
        require(time.monotonic() < self.deadline, "authority observation deadline reached before readiness")
        self.record["status"] = "ready"
        self.record["ready_unix_ns"] = time.time_ns()
        if gated_context:
            gate.recheck(binding, config, min(binding["gate_deadline_ns"], int(self.deadline * 1e9)))
            gate.no_pkexec(binding["app"]["pid"])
            rechecked = time.monotonic_ns()
            gate.publish(self.args.gate_directory, "binding.json", binding)
            release = {"schema": 1, "lease": config["lease"], "nonce": config["nonce"],
                       "boot_id": binding["boot_id"], "app_pid": binding["app"]["pid"],
                       "app_starttime": binding["app"]["starttime"], "binding_sha256": gate.sha(gate.encode(binding)),
                       "window_started_ns": int(self.started_at * 1e9),
                       "loaded_ns": self.record["loaded_marker_observed_monotonic_ns"],
                       "rechecked_ns": rechecked, "released_ns": time.monotonic_ns()}
            require(release["released_ns"] < binding["gate_deadline_ns"], "gate expired before publication")
            gate.publish(self.args.gate_directory, "release.json", release)
            self.record["gate_release"] = release
        self.record["remaining_seconds"] = max(0, self.deadline - time.monotonic())
        self.save()
        print(json.dumps({"event": "authority_window_ready", "mode": self.args.mode,
                          "receipt": str(self.args.receipt),
                          "remaining_seconds": self.record["remaining_seconds"]}), flush=True)

    def restore(self):
        self.record["restore_started_monotonic_ns"] = time.monotonic_ns()
        self.record["restore_started_unix_ns"] = time.time_ns()
        try:
            self.save()
        except OSError as error:
            # Receipt I/O failure must not prevent removal of our own authority
            # change. Preserve the error if a later receipt write succeeds.
            self.record["restore_start_persist_error"] = type(error).__name__
        if self.owned is None:
            return
        path = RULE if self.args.mode == "deny" else MASK
        info = path.lstat()
        require((info.st_dev, info.st_ino) == self.owned, "owned path changed; manual recovery required")
        if self.args.mode == "deny":
            identity_error = None
            try:
                self.recheck_service("service_binding_before_restore", restoring=True)
            except Exception as error:
                # Context failure invalidates evidence, never restoration of
                # this exact owned unchanged rule.
                identity_error = error
            self.check_owned_rule()
            path.unlink()
            self.record["cleanup"] = "restored"
            try:
                self.recheck_service("service_binding_after_restore", restoring=True)
            except Exception as error:
                identity_error = identity_error or error
            if identity_error is not None:
                self.record["status"] = "failed"
                self.record["error"] = "polkit identity changed; owned rule restored: " + str(identity_error)
            else:
                self.record["service_identity_valid"] = True
        else:
            require(path.is_symlink() and os.readlink(path) == "/dev/null", "runtime mask changed")
            self.run(["/usr/bin/systemctl", "--runtime", "unmask", "polkit.service"], restoring=True)
            require(not os.path.lexists(MASK), "runtime mask remains after unmask")
            self.run(["/usr/bin/systemctl", "start", "polkit.service"], restoring=True)
            after = self.state(restoring=True)
            require(after == self.initial and self.owner(restoring=True), "original authority configuration/state not restored")
            self.record["restored_state"] = after
        self.record["cleanup"] = "restored"
        self.save()


def interrupted(signum, _frame):
    raise RuntimeError("interrupted by signal " + str(signum))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("deny", "missing"))
    parser.add_argument("--lease", required=True, help="explicit coordinator lease identifier")
    parser.add_argument("--uid", required=True, type=int)
    parser.add_argument("--duration-seconds", type=int, default=20)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--source-sha256", required=True,
                        help="SHA-256 of independently reviewed, root-staged authority helper")
    parser.add_argument("--subject-pid", type=int)
    parser.add_argument("--session-id")
    parser.add_argument("--allow-shared-authority-window", action="store_true")
    args = parser.parse_args()
    require(sys.platform == "linux" and os.getuid() == 0 and os.geteuid() == 0,
            "requires an existing Linux root control session")
    require("PKEXEC_UID" not in os.environ, "must not be launched through pkexec")
    require(sys.flags.isolated and sys.dont_write_bytecode, "invoke /usr/bin/python3 -I -B")
    args.source_receipt = staged_source(Path(__file__), args.source_sha256)
    require(args.uid > 0 and 15 <= args.duration_seconds <= 45, "invalid nonroot UID or duration (15..45 seconds)")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", args.lease), "invalid explicit lease identifier")
    require(args.subject_pid is None or args.subject_pid > 1, "invalid subject PID")
    safe_root_parent(args.receipt.parent, private=True)
    fd = os.open(args.receipt, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    window = Window(args, fd)
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, interrupted)
    try:
        window.begin()
        while time.monotonic() < window.deadline:
            time.sleep(max(0, min(0.1, window.deadline - time.monotonic())))
        window.record["status"] = "window_elapsed"
    except Exception as error:
        window.record["status"] = "failed"
        window.record["error"] = str(error)[:2048]
    finally:
        # Restoration continues after the observation deadline: never abandon a
        # mask merely because a failed command consumed the remaining budget.
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(signum, signal.SIG_IGN)
        try:
            window.restore()
        except Exception as error:
            window.record["cleanup"] = "manual_recovery_required"
            window.record["cleanup_error"] = str(error)[:2048]
        if window.started_at is not None:
            window.record["elapsed_seconds_including_cleanup"] = time.monotonic() - window.started_at
            window.record["window_finished_unix_ns"] = time.time_ns()
            window.record["deadline_exceeded"] = time.monotonic() > window.total_deadline
            if window.record["deadline_exceeded"]:
                window.record["status"] = "failed"
                window.record["error"] = "observation/restoration exceeded requested deadline"
        window.save()
        os.close(fd)
    print(json.dumps({"event": "authority_window_finished", "status": window.record["status"],
                      "cleanup": window.record["cleanup"], "receipt": str(args.receipt)}), flush=True)
    return 0 if window.record["status"] == "window_elapsed" and window.record["cleanup"] == "restored" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(json.dumps({"event": "authority_window_refused", "error": str(error)[:2048]}), file=sys.stderr)
        sys.exit(1)
