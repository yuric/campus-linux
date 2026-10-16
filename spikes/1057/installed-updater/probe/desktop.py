#!/usr/bin/env python3
"""Record one arm64 GDM deb/polkit observation after an explicit coordinator lease.

This recorder does not grant a lease, change authority, enter a password or certify a
screenshot. Run from the real desktop user context. Root provisioning/authority windows
and compositor capture belong to the coordinator's separate leased procedure.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import signal
import stat
import struct
import subprocess
import time
from urllib.parse import urlsplit

import gated


APP = "/usr/bin/campus-updater-1057"
HELPER = "/usr/lib/campus-updater-1057/inert-helper.txt"
POLICY = Path("/usr/share/polkit-1/actions/dev.projectcampus.updater1057.policy")
HOSTED_RULE = Path("/etc/polkit-1/rules.d/49-campus-updater-1057-headless.rules")
CAPTURE_LIMIT = 128 * 1024
RECEIPT_LIMIT = 1024 * 1024


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def file_record(path, maximum=16 * 1024 * 1024):
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_size <= maximum, "evidence must be a bounded regular file")
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            value.update(block)
    return {"path": str(path.absolute()), "bytes": info.st_size, "sha256": value.hexdigest(),
            "uid": info.st_uid, "mode": oct(stat.S_IMODE(info.st_mode)), "mtime_ns": info.st_mtime_ns}


def root_preflight(path, expected_sha256, lease_reference, uid):
    """Bind an exported read-only root observation to the coordinator's digest.

    Exported copies need not retain root ownership. The supplied digest is the
    coordinator's provenance binding, not a signature or a grant of authority.
    Refresh the observation after provisioning and before the desktop cases.
    """
    record = file_record(path, RECEIPT_LIMIT)
    require(record["sha256"] == expected_sha256, "root preflight digest differs from coordinator binding")
    with path.open("rb") as stream:
        content = stream.read(RECEIPT_LIMIT + 1)
    require(len(content) <= RECEIPT_LIMIT and hashlib.sha256(content).hexdigest() == expected_sha256,
            "root preflight changed while reading coordinator-bound evidence")
    value = json.loads(content)
    require(value.get("schema") == 1 and value.get("kind") == "campus1057-root-preflight"
            and value.get("lease_reference") == lease_reference and value.get("graphical_uid") == uid,
            "root preflight does not match this lease and graphical user")
    require(type(value.get("observed_unix_ns")) is int and 0 < value["observed_unix_ns"] <= time.time_ns(),
            "root preflight lacks its actual observation time")
    require(value.get("hosted_allow_rule") == {"path": str(HOSTED_RULE), "exists": False},
            "root preflight must explicitly observe absence of this fixture's headless allow rule")
    require(isinstance(value.get("rules"), list) and len(value["rules"]) <= 128,
            "root preflight requires a bounded rules inventory")
    return {"file": record, "observation": value,
            "provenance": "coordinator-supplied digest binds exported root observation; independent review required",
            "freshness": "refresh after fixture provisioning and before actual desktop cases"}


def hosted_rule_observation(verified_preflight=None):
    try:
        HOSTED_RULE.lstat()
    except FileNotFoundError:
        return {"path": str(HOSTED_RULE), "exists": False, "source": "desktop lstat"}
    except PermissionError:
        require(verified_preflight is not None,
                "desktop cannot inspect protected rule path; provide coordinator-bound root preflight absence evidence")
        return {"path": str(HOSTED_RULE), "exists": None, "unreadable": "PermissionError",
                "absence_source": "root_preflight.observation.hosted_allow_rule"}
    raise RuntimeError("hosted automatic-allow rule must not exist during GDM evidence")


def bound_export(path, digest):
    """Read the bytes the coordinator actually bound, without privileged reads."""
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
            "export requires a coordinator-verified SHA-256")
    record = file_record(path, RECEIPT_LIMIT)
    with path.open("rb") as stream:
        content = stream.read(RECEIPT_LIMIT + 1)
    require(len(content) <= RECEIPT_LIMIT and record["sha256"] == digest
            and hashlib.sha256(content).hexdigest() == digest,
            "export differs from coordinator binding or changed while reading")
    return record, content


def validate_denial_evidence(desktop, authority, rows, validate_rows, derive_rule):
    """Pure post-run correlation. A pass remains subject to coordinator review."""
    result = {"status": "incomplete", "acceptance": "pending_coordinator_review",
              "journal_rows": rows,
              "trust_boundary": "Exact fresh marker from the verified dedicated polkit service account, "
              "correlated with the owned rule and controlled guest service context. Absent optional metadata "
              "does not prove executable or parent service; no protection against malicious root or "
              "same-account compromise. Nonce is correlation, not a secret."}
    try:
        require(desktop.get("schema") == 1 and desktop.get("case") == "deny"
                and desktop.get("status") == "observation_recorded"
                and desktop.get("session_binding") == "exact_logind_session",
                "only a completed exact-session deny observation can be correlated")
        require(authority.get("mode") == "deny" and authority.get("status") == "window_elapsed"
                and authority.get("cleanup") == "restored" and authority.get("deadline_exceeded") is False,
                "authority window did not finish with clean bounded restoration")
        require(authority.get("lease") == desktop.get("lease_reference"), "authority lease differs")
        binding = authority.get("service_binding")
        require(isinstance(binding, dict) and authority.get("service_identity_valid") is True
                and all(authority.get(key) == binding for key in
                        ("service_binding_before_ready", "service_binding_before_restore", "service_binding_after_restore")),
                "dedicated polkit service context was not stable through restoration")
        require(binding.get("uid") != str(authority.get("uid")), "fixture and daemon account must differ")
        nonce = authority.get("marker_nonce")
        require(isinstance(nonce, str) and re.fullmatch(r"[0-9a-f]{32}", nonce), "missing fresh helper nonce")
        require(desktop.get("boot_id") == desktop.get("boot_id_after") == authority.get("boot_id")
                and isinstance(desktop.get("boot_id"), str)
                and re.fullmatch(r"[0-9a-f]{32}", desktop["boot_id"]), "actual app and authority boot binding differs")
        expected_rule = derive_rule(authority.get("user"), authority.get("lease"), authority.get("subject_pid"),
                                    authority.get("subject_session"), nonce=nonce)
        result["expected_rule_sha256"] = hashlib.sha256(expected_rule).hexdigest()
        inode = authority.get("owned_device_inode")
        require(authority.get("rule_sha256") == result["expected_rule_sha256"]
                and authority.get("owned_path") == "/etc/polkit-1/rules.d/00-campus-updater-1057-deny.rules"
                and isinstance(inode, list) and len(inode) == 2
                and all(type(value) is int and value > 0 for value in inode),
                "missing exact helper-derived owned rule hash/path/inode provenance")
        commands = [row for row in desktop.get("commands", []) if row.get("argv", [])[:2] == [APP, "--update"]]
        require(len(commands) == 1, "requires one actual updater invocation")
        update = commands[0]
        process, session = update.get("process", {}), desktop.get("session", {})
        pid, uid = process.get("pid"), authority.get("uid")
        require(type(pid) is int and 1 < pid <= 2147483647
                and type(process.get("starttime_ticks")) is int and process["starttime_ticks"] > 0
                and process.get("uids", [])[:2] == [uid, uid] and type(uid) is int and uid > 0
                and process.get("logind_owner_uid") == uid
                and process.get("session") == session.get("Id") == authority.get("subject_session")
                and session.get("User") == str(uid) and session.get("Active") == "yes"
                and session.get("Remote") == "no", "actual app PID/starttime/user/session binding is incomplete")
        require(authority.get("subject_pid") in (None, pid), "rule subject differs from actual app PID")
        if authority.get("subject_pid") is not None:
            subject_stat = authority.get("subject_stat", "").rsplit(")", 1)[-1].split()
            require(len(subject_stat) > 19 and subject_stat[19] == str(process["starttime_ticks"]),
                    "root subject starttime differs from actual app lifetime")
        require(all(desktop.get("session_after", {}).get(key) == session.get(key) for key in
                    ("Id", "User", "Leader", "Type", "Class", "Service", "Remote", "Active", "State", "Scope", "Seat")),
                "actual app session changed")
        times = [authority.get("window_started_unix_ns"), authority.get("loaded_marker_observed_unix_ns"),
                 authority.get("ready_unix_ns"), update.get("started_ns"), update.get("finished_ns"),
                 authority.get("restore_started_unix_ns"), authority.get("window_finished_unix_ns")]
        require(all(type(value) is int and value > 0 for value in times)
                and times == sorted(times), "invocation was outside loaded, effective authority window")
        require(times[-1] - times[0] <= 45_000_000_000
                and times[4] - times[3] <= 20_000_000_000
                and times[-1] - times[-2] <= 10_000_000_000,
                "45-second window, 20-second invocation or 10-second restoration budget exceeded")
        events = desktop.get("updater_events", [])
        require([event.get("event") for event in events] == ["installed_identity", "selected", "verified_download",
                "polkit_adapter_result", "refusal_bytes", "refused"]
                and type(update.get("returncode")) is int and update["returncode"] != 0,
                "observation does not contain the actual refused updater path")
        require(events[3].get("success") is False and events[3].get("stdout", "").strip() == ""
                and events[4].get("app_unchanged") is True and events[4].get("helper_unchanged") is True
                and events[-1].get("error") == "polkit adapter did not install the fixture; inspect its receipt"
                and isinstance(desktop.get("before"), dict) and desktop["before"] == desktop.get("after")
                and events[0] == desktop["before"], "adapter entry or changed bytes prevents denial evidence")
        require(isinstance(rows, list) and 0 < len(rows) <= 64, "journal export must contain 1..64 full rows")
        loaded, rejecting, other = [], [], []
        for row in rows:
            message = row.get("MESSAGE") if isinstance(row, dict) else None
            if isinstance(message, str) and message.startswith("campus1057-deny-loaded "):
                loaded.append(row)
            elif isinstance(message, str) and message.startswith("campus1057-deny "):
                rejecting.append(row)
            else:
                other.append(row)
        common = {"nonce": nonce, "lease": authority["lease"], "binding": binding, "boot_id": authority.get("boot_id")}
        result["loaded"] = validate_rows(loaded,
            "campus1057-deny-loaded lease=" + authority["lease"] + " nonce=" + nonce,
            start_ns=times[0], end_ns=times[1], **common)
        result["rejecting"] = validate_rows(rejecting,
            "campus1057-deny lease=" + authority["lease"] + " nonce=" + nonce + " pid=" + str(pid)
            + " user=" + authority.get("user", "") + " session=" + session["Id"] + " active=true",
            start_ns=times[3], end_ns=times[4], **common)
        result["other_rows"] = other
        require(not any(nonce in json.dumps(row) for row in other), "unrecognized current-nonce journal candidate")
        require(all(result[key]["accepted"] and not result[key]["anomalies"] for key in ("loaded", "rejecting")),
                "loaded or rejecting marker lacks complete provenance, or has contradictory current-nonce rows")
        require(all(int(row["_PID"]) != pid for row in result["rejecting"]["accepted"]),
                "logger sender PID cannot be the actual app subject PID")
        result.update(status="correlated_pending_coordinator_review",
                      app_subject={"pid": pid, "starttime_ticks": process["starttime_ticks"], "session": session["Id"]},
                      logger_sender_pids=[row["_PID"] for row in result["rejecting"]["accepted"]])
    except (RuntimeError, ValueError, TypeError, KeyError) as error:
        result["error"] = str(error)
    return result


def validate_denial_exports(args):
    """Create new evidence; never rewrite or promote the original observation."""
    output = {"schema": 1, "kind": "campus1057-denial-correlation", "status": "incomplete",
              "acceptance": "pending_coordinator_review", "exports": {}}
    descriptor = os.open(args.validation_receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        try:
            values = {}
            for key, path, digest in (("desktop", args.validate_denial, args.desktop_receipt_sha256),
                                      ("authority", args.authority_receipt, args.authority_receipt_sha256),
                                      ("journal", args.journal, args.journal_sha256)):
                record, content = bound_export(path, digest)
                output["exports"][key] = record
                values[key] = ([json.loads(line) for line in content.splitlines() if line.strip()]
                               if key == "journal" else json.loads(content))
                if key == "journal":
                    output["journal_rows"] = values[key]
            output["recorder_source"] = file_record(__file__, RECEIPT_LIMIT)
            output["observed_recorder_source"] = values["desktop"].get("recorder")
            require(isinstance(output["observed_recorder_source"], dict)
                    and output["observed_recorder_source"].get("sha256") == output["recorder_source"]["sha256"],
                    "desktop invocation did not use these reviewed recorder bytes")
            helper = Path(__file__).with_name("authority-window.py")
            record, source = bound_export(helper, args.authority_helper_sha256)
            output["validator_source"] = record
            require(values["authority"].get("authority_helper", {}).get("sha256") == args.authority_helper_sha256,
                    "authority window did not run these reviewed helper bytes")
            namespace = {"__name__": "campus1057_marker_validation", "__file__": str(helper)}
            exec(compile(source, str(helper), "exec"), namespace)
            if getattr(args, "validate_user_manager", None):
                for name in ("gated.py", "serve.py", "desktop.py", "gated-driver.py"):
                    actual = file_record(Path(__file__).with_name(name), RECEIPT_LIMIT)
                    require(values["authority"].get("gated_control_sources", {}).get("gui_sources", {}).get(name, {}).get("sha256") == actual["sha256"],
                            "gated source/export hash differs: " + name)
                output["kind"] = "campus1057-root-correlated-user-manager"
                output.update(gated.correlate(values["desktop"], values["authority"], values["journal"],
                                               namespace["validate_marker_rows"], namespace["deny_rule"]))
            else:
                output.update(validate_denial_evidence(values["desktop"], values["authority"], values["journal"],
                                                       namespace["validate_marker_rows"], namespace["deny_rule"]))
        except Exception as error:
            output["error"] = str(error)
        json.dump(output, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if output["status"] in ("correlated_pending_coordinator_review", "root_correlated_user_manager_pending_coordinator_review") else 1


def record_outcome(path, observer, observation):
    """Attach an actual human observation only after the recorded invocation ends."""
    descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "r+") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and not info.st_mode & 0o077 and info.st_size <= RECEIPT_LIMIT,
                "outcome requires this user's private bounded receipt")
        value = json.load(stream)
        require(value.get("schema") == 1 and value.get("status") in
                ("observation_recorded", "not_certified", "incomplete"), "recorder has not finished")
        updates = [command for command in value.get("commands", [])
                   if command.get("argv", [])[:2] == [APP, "--update"]]
        require(len(updates) == 1 and type(updates[0].get("finished_ns")) is int,
                "receipt lacks a completed updater invocation")
        require(value.get("observer_statement") is None, "actual outcome is already recorded")
        now = time.time_ns()
        require(now >= updates[0]["finished_ns"], "outcome time precedes invocation completion")
        value["observer_statement"] = {"observer": observer, "observation": observation,
                                       "recorded_unix_ns": now, "invocation_finished_ns": updates[0]["finished_ns"],
                                       "review": "actual operator statement; independent coordinator review required"}
        value["acceptance"] = "pending_coordinator_review"
        encoded = json.dumps(value, indent=2) + "\n"
        require(len(encoded.encode()) <= RECEIPT_LIMIT, "outcome would exceed bounded receipt")
        stream.seek(0)
        stream.write(encoded)
        stream.truncate()
        stream.flush()
        os.fsync(stream.fileno())


def logind_process(pid):
    library = ctypes.CDLL("libsystemd.so.0")
    libc = ctypes.CDLL(None)
    library.sd_pid_get_session.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
    library.sd_pid_get_session.restype = ctypes.c_int
    library.sd_pid_get_owner_uid.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
    library.sd_pid_get_owner_uid.restype = ctypes.c_int
    libc.free.argtypes = [ctypes.c_void_p]
    pointer = ctypes.c_void_p()
    result = library.sd_pid_get_session(pid, ctypes.byref(pointer))
    try:
        session = ctypes.string_at(pointer).decode() if result >= 0 else None
    finally:
        if pointer:
            libc.free(pointer)
    owner = ctypes.c_uint()
    owner_result = library.sd_pid_get_owner_uid(pid, ctypes.byref(owner))
    status = Path(f"/proc/{pid}/status").read_text()
    values = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
              for line in status.splitlines() if ":" in line}
    proc_stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "ppid": int(values["PPid"]), "name": values.get("Name"), "uids": list(map(int, values["Uid"].split())),
            "starttime_ticks": int(proc_stat[19]), "cgroup": Path(f"/proc/{pid}/cgroup").read_text(),
            "session": session, "session_api_result": result,
            "logind_owner_uid": owner.value if owner_result >= 0 else None, "owner_api_result": owner_result}


def boot_id():
    value = Path("/proc/sys/kernel/random/boot_id").read_text().strip().replace("-", "")
    require(re.fullmatch(r"[0-9a-f]{32}", value), "missing actual boot identity")
    return value


class Recorder:
    def __init__(self, args):
        self.args = args
        descriptor = os.open(args.receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        self.output = os.fdopen(descriptor, "w")
        self.receipt = {"schema": 1, "status": "recording", "acceptance": "pending_coordinator_review",
                        "case": args.case, "lease_reference": args.lease_reference,
                        "authority_reference": args.authority_reference, "source_head_claim": args.source_head,
                        "recorder": file_record(__file__, 128 * 1024), "commands": [],
                        "planned_scenario": {"observer": args.observer, "description": args.planned_observation},
                        "observer_statement": None,
                        "limits": {"capture_bytes_per_command": CAPTURE_LIMIT, "update_timeout_seconds": args.timeout},
                        "gui_evidence": "not automatically certified; coordinator must inspect actual compositor capture"}
        self.save()

    def save(self):
        self.output.seek(0)
        json.dump(self.receipt, self.output, indent=2)
        self.output.write("\n")
        self.output.truncate()
        self.output.flush()
        os.fsync(self.output.fileno())

    def sample_children(self, app_pid, record):
        """Observe bounded direct children only; never read process argv or environment."""
        observations = record.setdefault("child_process_observations", [])
        seen = record.setdefault("child_pids_sampled", [])
        try:
            tasks = list(Path(f"/proc/{app_pid}/task").iterdir())
            if len(tasks) > 64:
                record["child_sampling_limit"] = "more than 64 app tasks; incomplete observation"
                return
            children = set()
            for task in tasks:
                content = (task / "children").read_text()
                if len(content) > 512:
                    record["child_sampling_limit"] = "unbounded task child list; incomplete observation"
                    return
                children.update(int(pid) for pid in content.split())
            if len(set(seen) | children) > 16:
                record["child_sampling_limit"] = "more than 16 child PIDs; incomplete observation"
                return
        except OSError as error:
            record["child_sampling_unavailable"] = type(error).__name__
            return
        for pid in sorted(children):
            if pid not in seen:
                seen.append(pid)
            observed = {"pid": pid}
            try:
                observed.update(logind_process(pid))
            except (OSError, ValueError, KeyError) as error:
                observed["process_details_unavailable"] = type(error).__name__
            try:
                observed["executable"] = os.readlink(f"/proc/{pid}/exe")
            except OSError as error:
                observed["executable_unavailable"] = type(error).__name__
            previous = [item for item in observations if item["pid"] == pid]
            comparable = {key: value for key, value in previous[-1].items() if key != "observed_monotonic_ns"} if previous else None
            if observed != comparable and len(previous) < 4:
                observations.append({**observed, "observed_monotonic_ns": time.monotonic_ns()})
                self.save()

    def gated_command(self, argv):
        """Observe without reaping until root removes the exact owned NO rule.

        No poll/wait/communicate is permitted before the trusted restoration
        acknowledgment. A dead controller makes evidence incomplete; it never
        extends the 20-second invocation or silently frees the subject PID.
        """
        config = gated.config_read(self.args.gate_directory)
        require(self.args.case == "deny" and self.args.timeout == 20
                and config["lease"] == self.args.lease_reference, "gated recorder scope differs")
        record = {"argv": argv, "started_ns": time.time_ns(), "monotonic_started_ns": time.monotonic_ns()}
        deadline = record["monotonic_started_ns"] + gated.APP_NS
        cleanup_deadline = record["monotonic_started_ns"] + gated.GATE_NS + 45_000_000_000
        self.receipt["commands"].append(record)
        self.receipt["gated_mode"] = gated.MODE
        self.receipt["session_binding"] = "coordinator_review_required"
        self.save()
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        # Retain the Popen object too: its destructor must not poll/reap on error.
        self._unreaped = [child]
        selector = selectors.DefaultSelector()
        captured = {"stdout": bytearray(), "stderr": bytearray()}
        failure, completed, restored = None, None, False
        try:
            record["process"] = logind_process(child.pid)
            require(record["process"]["session"] is None, "gated mode requires actual null session")
            gated.hint_write(Path(config["hints"]) / "app.json", {
                "lease": config["lease"], "nonce": config["nonce"], "app_pid": child.pid,
                "server_pid": self.args.gate_server_pid, "monotonic_started_ns": record["monotonic_started_ns"]})
            self.save()
            for name, pipe in (("stdout", child.stdout), ("stderr", child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            while completed is None or selector.get_map():
                require(time.monotonic_ns() < deadline, "original 20-second app deadline exceeded")
                self.sample_children(child.pid, record)
                completed = gated.child_exit(child)
                for key, unused in selector.select(min(0.02, max(0, (deadline - time.monotonic_ns()) / 1e9))):
                    block = os.read(key.fileobj.fileno(), 8192)
                    if not block:
                        selector.unregister(key.fileobj)
                        continue
                    remaining = CAPTURE_LIMIT - sum(map(len, captured.values()))
                    captured[key.data].extend(block[:remaining])
                    require(len(block) <= remaining, "command exceeded bounded capture")
                if completed is not None and "finished_ns" not in record:
                    record.update(returncode=completed, finished_ns=time.time_ns(), monotonic_finished_ns=time.monotonic_ns())
            require(record["monotonic_finished_ns"] <= deadline, "late app completion")
        except Exception as error:
            failure = error
            record["gated_error"] = str(error)
            try:
                gated.hint_write(Path(config["hints"]) / "abort.json", {"error": str(error)[:1024]})
            except FileExistsError:
                pass
            # Killing is not reaping. The retaining parent stays alive through
            # restoration, including for a zombie caused by this timeout.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        finally:
            record.update({name: bytes(value).decode(errors="replace") for name, value in captured.items()})
            record.setdefault("finished_ns", time.time_ns())
            record.setdefault("monotonic_finished_ns", time.monotonic_ns())
            self.save()
            try:
                while time.monotonic_ns() < cleanup_deadline:
                    try:
                        acknowledgment = gated.root_read(self.args.gate_directory / "restored.json")
                    except FileNotFoundError:
                        time.sleep(0.02)
                        continue
                    require(acknowledgment.get("lease") == config["lease"]
                            and acknowledgment.get("nonce") == config["nonce"]
                            and acknowledgment.get("boot_id") == config["boot_id"]
                            and acknowledgment.get("rule_absent") is True
                            and type(acknowledgment.get("restored_ns")) is int
                            and record["monotonic_started_ns"] <= acknowledgment["restored_ns"] <= time.monotonic_ns(),
                            "invalid root restoration acknowledgment")
                    restored = True
                    record["root_restoration"] = acknowledgment
                    break
                require(restored, "root restoration unavailable; child deliberately not reaped, manual recovery required")
                # Only now can the numeric PID be released. If root aborted
                # before app completion, terminate it without claiming success.
                if gated.child_exit(child) is None:
                    os.killpg(child.pid, signal.SIGKILL)
                    failure = failure or RuntimeError("authority restored before app completed")
                actual_returncode = child.wait(timeout=1)
                record.setdefault("returncode", actual_returncode)
                require(record["returncode"] == actual_returncode, "exit observation changed")
                record["reaped_monotonic_ns"] = time.monotonic_ns()
                self._unreaped = []
            except Exception as error:
                failure = failure or error
                record["retention_error"] = str(error)
            selector.close()
            child.stdout.close()
            child.stderr.close()
            self.save()
        if failure:
            raise failure
        return record

    def command(self, argv, timeout=10, bind=False):
        if bind and getattr(self.args, "gate_directory", None):
            return self.gated_command(argv)
        record = {"argv": argv, "started_ns": time.time_ns(), "monotonic_started_ns": time.monotonic_ns()}
        self.receipt["commands"].append(record)
        self.save()
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        selector = selectors.DefaultSelector()
        captured = {"stdout": bytearray(), "stderr": bytearray()}
        deadline = time.monotonic() + timeout
        try:
            if bind:
                record["process"] = logind_process(child.pid)
                process = record["process"]
                require(process["uids"][0] == process["uids"][1] == os.getuid(), "updater UID differs from desktop user")
                require(process["logind_owner_uid"] == os.getuid(), "updater lacks this user's logind ownership")
                require(process["session"] in (None, self.session["Id"]), "updater belongs to another logind session")
                if process["session"] is None:
                    self.receipt["session_binding"] = "coordinator_review_required"
            for name, pipe in (("stdout", child.stdout), ("stderr", child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            while selector.get_map():
                require(time.monotonic() < deadline, "command timeout; authority/install state needs coordinator inspection")
                if bind:
                    self.sample_children(child.pid, record)
                for key, unused in selector.select(min(0.25, max(0, deadline - time.monotonic()))):
                    block = os.read(key.fileobj.fileno(), 8192)
                    if not block:
                        selector.unregister(key.fileobj)
                        continue
                    remaining = CAPTURE_LIMIT - sum(map(len, captured.values()))
                    captured[key.data].extend(block[:remaining])
                    require(len(block) <= remaining, "command exceeded bounded capture")
            child.wait(timeout=max(0.01, deadline - time.monotonic()))
        finally:
            if child.poll() is None:
                # This cannot stop a root installer; never report completion after a timeout.
                for operation in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(child.pid, operation)
                    except ProcessLookupError:
                        break
                    try:
                        child.wait(timeout=1)
                        break
                    except subprocess.TimeoutExpired:
                        continue
            selector.close()
            child.stdout.close()
            child.stderr.close()
            record.update({"returncode": child.poll(), "finished_ns": time.time_ns(),
                           "monotonic_finished_ns": time.monotonic_ns(),
                           **{name: bytes(value).decode(errors="replace") for name, value in captured.items()}})
            if bind:
                observations = record.get("child_process_observations", [])
                executable_pids = sorted({item["pid"] for item in observations
                                          if Path(item.get("executable", "")).name == "pkexec"})
                name_only_pids = sorted({item["pid"] for item in observations if item.get("name") == "pkexec"
                                         and item["pid"] not in executable_pids})
                record["pkexec_pid_observation"] = {"executable_observed_pids": executable_pids,
                                                    "name_only_pids": name_only_pids,
                                                    "status": "observed" if executable_pids else "not_verified_coordinator_review_required",
                                                    "limitation": "unprivileged /proc pkexec executable lookup may be denied after setuid; name-only is not executable verification; bounded sampling may miss quick refusals"}
            self.save()
        return record

    def properties(self, object_type, identifier):
        record = self.command(["/usr/bin/loginctl", "show-" + object_type, str(identifier), "--no-pager"])
        require(record["returncode"] == 0, "loginctl observation failed")
        return dict(line.split("=", 1) for line in record["stdout"].splitlines() if "=" in line)

    def bind_session(self):
        require(platform.system() == "Linux" and platform.machine() == "aarch64", "recorder requires the leased native arm64 Linux guest")
        require(os.getuid() == os.geteuid() != 0, "recorder must be the unprivileged desktop user")
        self.receipt["boot_id"] = boot_id()
        preflight = None
        if self.args.root_preflight is not None:
            preflight = root_preflight(self.args.root_preflight, self.args.root_preflight_sha256,
                                       self.args.lease_reference, os.getuid())
            self.receipt["root_preflight"] = preflight
        self.receipt["hosted_rule_observation"] = hosted_rule_observation(preflight)
        self.save()
        user = self.properties("user", os.getuid())
        sessions = user.get("Sessions", "").split()
        require(0 < len(sessions) <= 8, "cannot bound this user's actual logind sessions")
        observed = [self.properties("session", session) for session in sessions]
        graphical = [session for session in observed
                     if session.get("User") == str(os.getuid()) and session.get("Type") in ("wayland", "x11")
                     and session.get("Class") == "user" and session.get("Service", "").startswith("gdm-")
                     and session.get("Remote") == "no" and session.get("Active") == "yes" and session.get("State") == "active"]
        require(len(graphical) == 1, "requires exactly one active local GDM graphical session for this UID")
        self.session = graphical[0]
        own = logind_process(os.getpid())
        require(own["logind_owner_uid"] == os.getuid(), "recorder lacks this user's logind ownership")
        require(own["session"] in (None, self.session["Id"]), "recorder is in another session, such as SSH")
        declared = os.environ.get("XDG_SESSION_ID")
        require(declared in (None, "", self.session["Id"]), "XDG_SESSION_ID contradicts actual GDM session")
        runtime = Path("/run/user") / str(os.getuid())
        require(os.environ.get("XDG_RUNTIME_DIR") == str(runtime) == user.get("RuntimePath"), "runtime does not match logind user")
        info = runtime.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
                "runtime must be the actual private user directory")
        bus = runtime / "bus"
        bus_info = bus.lstat()
        require(stat.S_ISSOCK(bus_info.st_mode) and bus_info.st_uid == os.getuid(), "user bus socket owner/type mismatch")
        address = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
        require(re.fullmatch(re.escape("unix:path=" + str(bus)) + r"(?:,guid=[0-9a-f]+)?", address),
                "requires the actual user bus, not a private substitute")
        display = os.environ.get("DISPLAY", "")
        wayland = os.environ.get("WAYLAND_DISPLAY", "")
        socket_evidence = {"user_bus": {"path": str(bus), "uid": bus_info.st_uid}}
        if self.session["Type"] == "wayland":
            require(wayland and Path(wayland).name == wayland, "Wayland display must name a socket in the user runtime")
            compositor = runtime / wayland
            compositor_info = compositor.lstat()
            require(stat.S_ISSOCK(compositor_info.st_mode) and compositor_info.st_uid == os.getuid(), "Wayland socket owner/type mismatch")
            socket_evidence["compositor"] = {"path": str(compositor), "uid": compositor_info.st_uid}
        else:
            require(re.fullmatch(r":[0-9]+(?:\.[0-9]+)?", display), "requires a local X11 display")
            require(self.session.get("Display", "").split(".")[0] == display.split(".")[0], "X11 display contradicts logind session")
            x_socket = Path("/tmp/.X11-unix/X" + display[1:].split(".")[0])
            x_info = x_socket.lstat()
            require(stat.S_ISSOCK(x_info.st_mode) and x_info.st_uid in (0, os.getuid()), "X11 socket owner/type mismatch")
            socket_evidence["compositor"] = {"path": str(x_socket), "uid": x_info.st_uid}
        self.receipt.update({"session_binding": "exact_logind_session" if own["session"] else "coordinator_review_required",
                             "session": self.session, "user": user, "recorder_process": own,
                             "session_leader": logind_process(int(self.session["Leader"])),
                             "environment_observations": {"XDG_SESSION_ID": declared, "XDG_RUNTIME_DIR": str(runtime),
                                                          "DISPLAY": display, "WAYLAND_DISPLAY": wayland,
                                                          "DBUS_SESSION_BUS_ADDRESS": address}, "sockets": socket_evidence})
        rules = []
        for directory in (Path("/etc/polkit-1/rules.d"), Path("/usr/share/polkit-1/rules.d")):
            try:
                paths = sorted(path for path in directory.iterdir() if path.suffix == ".rules")
                require(len(paths) <= 64, "unbounded polkit rule inventory")
                for path in paths:
                    try:
                        rules.append(file_record(path, 65536))
                    except (OSError, RuntimeError) as error:
                        rules.append({"path": str(path), "unreadable": str(error)})
            except OSError as error:
                rules.append({"path": str(directory), "unreadable": str(error)})
        self.receipt["authority_file_observations"] = {"fixture_policy": file_record(POLICY, 8192), "rules": rules,
                                                       "interpretation": "hash inventory only; coordinator must inspect effective authority"}
        self.save()

    def expected_packages(self):
        index_record = file_record(self.args.index, 1024 * 1024)
        inventory_record = file_record(self.args.inventory)
        index = json.loads(self.args.index.read_text())
        inventory = json.loads(self.args.inventory.read_text())
        require(index.get("source_head") == self.args.source_head and index.get("architecture") == "arm64",
                "artifact index does not match the reviewed native source head")
        self.expected = {}
        for version, behavior in (("1.0.0", "v1-baseline"), ("2.0.0", "v2-changed")):
            artifacts = [row for row in index["artifacts"] if row.get("version") == version and row.get("format") == "deb"
                         and row.get("architecture") == "arm64" and row.get("target") == "linux-aarch64-deb"]
            require(len(artifacts) == 1, "index lacks a unique reviewed deb version")
            package = artifacts[0]
            inventories = [row for row in inventory if row.get("artifact") == package["filename"]]
            require(len(inventories) == 1, "payload inventory lacks this exact deb")
            selected = {}
            for key, filename in (("app_sha256", APP), ("helper_sha256", HELPER)):
                files = [row for row in inventories[0]["files"] if row.get("path") == filename.lstrip("/")]
                require(len(files) == 1 and isinstance(files[0].get("bytes"), int) and files[0]["bytes"] > 0
                        and re.fullmatch(r"[0-9a-f]{64}", files[0].get("sha256", "")), "invalid expected payload hash/size")
                selected[key] = files[0]["sha256"]
            self.expected[version] = {"identity": {**selected, "version": version, "behavior": behavior,
                                                   "format": "deb", "architecture": "aarch64", "exact_target": "linux-aarch64-deb"},
                                      "package": {key: package[key] for key in ("filename", "bytes", "sha256", "target", "version")}}
        self.receipt["expected_artifact_evidence"] = {"index": index_record, "inventory": inventory_record,
                                                     "versions": self.expected,
                                                     "review": "coordinator must bind these public receipts to the exact hosted run"}
        self.save()

    def identity(self, version, slot):
        result = self.command([APP, "--diagnose"])
        require(result["returncode"] == 0, "installed diagnostic failed")
        value = json.loads(result["stdout"])
        self.receipt[slot] = value
        self.save()
        require(value.get("event") == "installed_identity" and value.get("exact_target") == "linux-aarch64-deb"
                and value.get("executable") == APP and value.get("helper_path") == HELPER, "not the genuine installed arm64 deb")
        require(value["app_sha256"] == file_record(APP, 256 * 1024 * 1024)["sha256"]
                and value["helper_sha256"] == file_record(HELPER, 65536)["sha256"], "installed diagnostic hashes disagree with current files")
        require(all(value.get(key) == expected for key, expected in self.expected[version]["identity"].items()),
                "installed fixture does not match the independently recorded expected version/payload hashes")
        return value

    def screenshot(self, started, finished):
        if self.args.screenshot is None:
            require(self.args.case not in ("prompt", "cancel"), "prompt/cancel evidence requires an actual fresh compositor PNG")
            return None
        record = file_record(self.args.screenshot)
        require(started <= record["mtime_ns"] <= finished, "screenshot is not fresh within this updater invocation")
        with self.args.screenshot.open("rb") as stream:
            header = stream.read(24)
        require(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR", "screenshot must be a real PNG file")
        width, height = struct.unpack(">II", header[16:24])
        require(width > 0 and height > 0, "PNG has no image dimensions")
        return {**record, "width": width, "height": height,
                "review": "requires visual confirmation of actual session/prompt/action; hash does not authenticate GUI content"}

    def run(self):
        try:
            self.bind_session()
            self.expected_packages()
            before = self.identity("1.0.0", "before")
            self.receipt["before"] = before
            self.save()
            update = self.command([APP, "--update", self.args.endpoint], timeout=self.args.timeout, bind=True)
            self.receipt["boot_id_after"] = boot_id()
            require(self.receipt["boot_id_after"] == self.receipt["boot_id"], "boot identity changed during invocation")
            after = self.identity("2.0.0" if self.args.case == "prompt" else "1.0.0", "after")
            self.receipt["after"] = after
            events = [json.loads(line) for line in update["stdout"].splitlines() if line.startswith("{")]
            self.receipt["updater_events"] = events
            names = [event.get("event") for event in events]
            require(events and events[0] == before, "updater did not run the observed installed fixture")
            selected = next(event for event in events if event.get("event") == "selected")
            verified = next(event for event in events if event.get("event") == "verified_download")
            package = self.expected["2.0.0"]["package"]
            download = urlsplit(selected.get("url", ""))
            endpoint = urlsplit(self.args.endpoint)
            require(selected.get("exact_target") == "linux-aarch64-deb" and selected.get("version") == "2.0.0"
                    and verified.get("version") == "2.0.0" and verified.get("sha256") == package["sha256"]
                    and verified.get("bytes") == package["bytes"] and download.scheme == "http"
                    and download.hostname == "127.0.0.1" and download.port == endpoint.port
                    and download.path == "/packages/" + package["filename"] and not download.query and not download.fragment
                    and not download.username and not download.password,
                    "updater did not reach the intended authenticated deb download")
            session_after = self.properties("session", self.session["Id"])
            self.receipt["session_after"] = session_after
            require(all(session_after.get(key) == self.session.get(key) for key in
                        ("Id", "User", "Leader", "Type", "Class", "Service", "Remote", "Active", "State", "Scope", "Seat")),
                    "logind session identity/activity changed during the observation")
            if self.args.case in ("cancel", "deny", "missing-authority"):
                require(update["returncode"] != 0 and names == ["installed_identity", "selected", "verified_download",
                        "polkit_adapter_result", "refusal_bytes", "refused"], "case did not reach a polkit refusal")
                elevation = events[3]
                require(elevation.get("success") is False and elevation.get("stdout", "").strip() == "",
                        "privileged adapter entered or elevation did not refuse")
                require(events[4].get("app_unchanged") is True and events[4].get("helper_unchanged") is True,
                        "app did not report unchanged bytes on refusal")
                require(events[-1].get("error") == "polkit adapter did not install the fixture; inspect its receipt",
                        "unrelated failure cannot count as this authority observation")
                require(before == after, "authority refusal changed installed fixture identity/bytes")
                self.receipt["technical_observation"] = "polkit refusal; adapter did not emit an entry receipt; installed bytes unchanged"
            else:
                require(update["returncode"] == 0 and names == ["installed_identity", "selected", "verified_download",
                        "polkit_adapter_result", "deb_adapter_completed"], "prompt success case did not complete actual pkexec update")
                elevation = events[3]
                require(elevation.get("success") is True and elevation.get("exit_status") == 0, "prompt update was not accepted")
                adapter = json.loads(elevation["stdout"])
                require(all(adapter.get(key) == value for key, value in {"status": "accepted", "phase": "complete",
                        "authenticated_version": "2.0.0", "installed_version": "1.0.0", "dpkg_exit": 0,
                        "package_sha256": package["sha256"], "package_bytes": package["bytes"]}.items()),
                        "privileged result does not match the authenticated v1 to v2 update")
                require(adapter.get("before") == {"app": before["app_sha256"], "helper": before["helper_sha256"]}
                        and adapter.get("after") == {"app": after["app_sha256"], "helper": after["helper_sha256"]},
                        "privileged result hashes disagree with independently expected installed files")
                self.receipt["technical_observation"] = "signed v1 to v2 installed through pkexec; actual prompt still requires fresh screenshot review"
            self.receipt["screenshot"] = self.screenshot(update["started_ns"], update["finished_ns"])
            self.receipt["status"] = "observation_recorded" if self.receipt["session_binding"] == "exact_logind_session" else "not_certified"
            self.receipt["case_distinction"] = "cancel/deny/missing-authority labels are operator observations plus authority-window evidence, not inferred from pkexec exit codes"
            return 0
        except Exception as error:
            self.receipt.update(status="incomplete", error=str(error))
            if "before" in self.receipt and "after" not in self.receipt and not getattr(self, "_unreaped", []):
                try:
                    observed = self.command([APP, "--diagnose"], timeout=5)
                    self.receipt["after_incomplete_observation"] = json.loads(observed["stdout"])
                except Exception as after_error:
                    self.receipt["after_incomplete_observation"] = {"unavailable": str(after_error)}
            return 1
        finally:
            self.save()
            self.output.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--case", choices=("prompt", "cancel", "deny", "missing-authority"))
    mode.add_argument("--record-outcome", type=Path, help="completed receipt to append the actual observation to, after the recorder exits")
    mode.add_argument("--validate-user-manager", type=Path, help="separate pending root correlation; never upgrades raw null-session evidence")
    mode.add_argument("--validate-denial", type=Path, help="post-run completed deny receipt; produces a separate correlation receipt")
    parser.add_argument("--desktop-receipt-sha256", help="coordinator binding for the completed desktop receipt")
    parser.add_argument("--authority-receipt", type=Path, help="exported final root authority receipt, after restoration")
    parser.add_argument("--authority-receipt-sha256", help="coordinator binding for the final root receipt")
    parser.add_argument("--journal", type=Path, help="exported full journal JSONL rows from the bounded authority window")
    parser.add_argument("--journal-sha256", help="coordinator binding for the exported full journal rows")
    parser.add_argument("--authority-helper-sha256", help="reviewed SHA-256 of adjacent authority-window.py and actual root helper")
    parser.add_argument("--validation-receipt", type=Path, help="new private post-run correlation receipt; originals stay unchanged")
    parser.add_argument("--lease-reference", help="explicit coordinator lease comment/receipt reference; not a grant of authority")
    parser.add_argument("--authority-reference", help="coordinator's actual authority-window preparation receipt")
    parser.add_argument("--source-head", help="full reviewed source SHA; recorder hash is independently retained")
    parser.add_argument("--index", type=Path, help="reviewed native hosted receipts/package-index.json")
    parser.add_argument("--inventory", type=Path, help="matching hosted receipts/payload-inventory.json")
    parser.add_argument("--root-preflight", type=Path, help="exported root rule inventory/absence receipt refreshed after provisioning")
    parser.add_argument("--root-preflight-sha256", help="coordinator-verified SHA-256 binding for the exported root receipt")
    parser.add_argument("--endpoint", default="http://127.0.0.1:17857/stable/linux.json")
    parser.add_argument("--observer")
    parser.add_argument("--planned-observation", help="planned scenario only; not a claim about an outcome")
    parser.add_argument("--observation", help="actual observed GUI outcome, only with --record-outcome; never enter any password or secret")
    parser.add_argument("--screenshot", type=Path, help="fresh compositor PNG captured during this invocation; mandatory for prompt/cancel")
    parser.add_argument("--receipt", type=Path, help="new receipt path in an existing user-owned evidence directory")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--gate-directory", type=Path, help="optional separately leased root-correlated user-manager denial")
    parser.add_argument("--gate-server-pid", type=int)
    args = parser.parse_args()
    if args.gate_directory and (args.case != "deny" or args.timeout != 20 or not args.gate_server_pid
                               or args.endpoint != "http://127.0.0.1:17857/stable/linux.json"):
        parser.error("gated mode requires deny, original 20 seconds, actual server PID and fixed endpoint")
    if args.validate_user_manager is not None:
        args.validate_denial = args.validate_user_manager
    if args.validate_denial is not None:
        if any(getattr(args, name) is None for name in ("desktop_receipt_sha256", "authority_receipt",
                "authority_receipt_sha256", "journal", "journal_sha256", "authority_helper_sha256", "validation_receipt")):
            parser.error("--validate-denial requires desktop/authority/journal SHA-256 bindings, helper SHA-256 and new validation receipt")
        if args.validation_receipt.parent.stat().st_uid != os.getuid():
            parser.error("validation receipt requires this user's existing evidence directory")
        raise SystemExit(validate_denial_exports(args))
    if not args.observer or not args.observer.strip() or len(args.observer) > 2048:
        parser.error("observer must be nonempty and bounded")
    if args.record_outcome is not None:
        if not args.observation or not args.observation.strip() or len(args.observation) > 2048:
            parser.error("--record-outcome requires a nonempty bounded --observation")
        record_outcome(args.record_outcome, args.observer, args.observation)
        return
    if any(getattr(args, name) is None for name in
           ("lease_reference", "authority_reference", "source_head", "index", "inventory", "receipt", "planned_observation")):
        parser.error("--case requires lease/authority references, source head, index, inventory, receipt and planned observation")
    if args.observation is not None:
        parser.error("actual --observation is accepted only after the run, using --record-outcome")
    if (args.root_preflight is None) != (args.root_preflight_sha256 is None) or (
            args.root_preflight_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", args.root_preflight_sha256)):
        parser.error("--root-preflight and its coordinator-verified --root-preflight-sha256 must be supplied together")
    endpoint = urlsplit(args.endpoint)
    if endpoint.scheme != "http" or endpoint.hostname != "127.0.0.1" or endpoint.username or endpoint.password or endpoint.path != "/stable/linux.json" or endpoint.query or endpoint.fragment:
        parser.error("endpoint must be the literal loopback fixture /stable/linux.json")
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_head) or not 15 <= args.timeout <= 300:
        parser.error("requires a full source SHA and timeout between 15 and 300 seconds")
    if any(not value.strip() or len(value) > 2048 for value in
           (args.lease_reference, args.authority_reference, args.planned_observation)):
        parser.error("lease/authority references and observer statements must be nonempty and bounded")
    if args.case in ("prompt", "cancel") and args.screenshot is None:
        parser.error("prompt/cancel requires the actual compositor screenshot destination")
    if os.getuid() == 0 or args.receipt.parent.stat().st_uid != os.getuid():
        parser.error("use the unprivileged desktop user and its existing evidence directory")
    raise SystemExit(Recorder(args).run())


if __name__ == "__main__":
    main()
