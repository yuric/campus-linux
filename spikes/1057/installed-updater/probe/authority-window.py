#!/usr/bin/env python3
"""Leased, root-operated GDM negative-evidence window; never acquires privilege.

Prepared source only: this helper must not run before the coordinator grants the
exclusive VM lease. Run from an existing independent root control session, while
the real installed fixture is launched by its existing GDM user session.

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
PROPERTIES = "Id,LoadState,ActiveState,SubState,UnitFileState,FragmentPath,DropInPaths"


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


def deny_rule(user, lease, pid=None, session=None):
    # Polkit 124 exposes subject.user, not subject.uid. The caller validates the
    # exact UID/name mapping through NSS before creating this deny-only rule.
    checks = [f"action.id === {json.dumps(ACTION)}",
              f"action.lookup('program') === {json.dumps(PROGRAM)}",
              "action.lookup('user') === 'root'",
              f"subject.user === {json.dumps(user)}", "subject.local === true",
              "subject.active === true"]
    if pid is not None:
        checks.append(f"subject.pid === {pid}")
    if session is not None:
        checks.append(f"subject.session === {json.dumps(session)}")
    marker = json.dumps("campus1057-deny lease=" + lease)
    loaded = json.dumps("campus1057-deny-loaded lease=" + lease)
    return (f"polkit.log({loaded});\n"
            "polkit.addRule(function(action, subject) {\n"
            "  if (" + " && ".join(checks) + ") {\n"
            f"    polkit.log({marker} + ' pid=' + subject.pid + ' user=' + subject.user"
            " + ' session=' + subject.session + ' active=' + subject.active);\n"
            "    return polkit.Result.NO;\n  }\n});\n").encode()


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

    def run(self, argv, ok=True, restoring=False):
        timeout = 2.0 if restoring else 5.0
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

    def begin(self):
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
            self.rule_bytes = deny_rule(account.pw_name, self.args.lease,
                                        self.args.subject_pid, self.args.session_id)
            self.arm_deadline()
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
            self.record["ready_caveat"] = "Wait for matching deny-loaded journal marker before launching; require deny marker for actual refusal evidence"
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
        self.record["status"] = "ready"
        self.record["remaining_seconds"] = max(0, self.deadline - time.monotonic())
        self.save()
        print(json.dumps({"event": "authority_window_ready", "mode": self.args.mode,
                          "receipt": str(self.args.receipt),
                          "remaining_seconds": self.record["remaining_seconds"]}), flush=True)

    def restore(self):
        if self.owned is None:
            return
        path = RULE if self.args.mode == "deny" else MASK
        info = path.lstat()
        require((info.st_dev, info.st_ino) == self.owned, "owned path changed; manual recovery required")
        if self.args.mode == "deny":
            require(path.read_bytes() == self.rule_bytes, "deny rule changed; refusing removal")
            path.unlink()
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
    parser.add_argument("--subject-pid", type=int)
    parser.add_argument("--session-id")
    parser.add_argument("--allow-shared-authority-window", action="store_true")
    args = parser.parse_args()
    require(sys.platform == "linux" and os.getuid() == 0 and os.geteuid() == 0,
            "requires an existing Linux root control session")
    require("PKEXEC_UID" not in os.environ, "must not be launched through pkexec")
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
