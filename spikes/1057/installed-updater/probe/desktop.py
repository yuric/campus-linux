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


APP = "/usr/bin/campus-updater-1057"
HELPER = "/usr/lib/campus-updater-1057/inert-helper.txt"
POLICY = Path("/usr/share/polkit-1/actions/dev.projectcampus.updater1057.policy")
HOSTED_RULE = Path("/etc/polkit-1/rules.d/49-campus-updater-1057-headless.rules")
CAPTURE_LIMIT = 128 * 1024


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


class Recorder:
    def __init__(self, args):
        self.args = args
        descriptor = os.open(args.receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        self.output = os.fdopen(descriptor, "w")
        self.receipt = {"schema": 1, "status": "recording", "acceptance": "pending_coordinator_review",
                        "case": args.case, "lease_reference": args.lease_reference,
                        "authority_reference": args.authority_reference, "source_head_claim": args.source_head,
                        "recorder": file_record(__file__, 128 * 1024), "commands": [],
                        "observer_statement": {"observer": args.observer, "observation": args.observation},
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

    def command(self, argv, timeout=10, bind=False):
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
                                                    "limitation": "bounded sampling cannot prove child absence; quick refusals may finish before sampling"}
            self.save()
        return record

    def properties(self, object_type, identifier):
        record = self.command(["/usr/bin/loginctl", "show-" + object_type, str(identifier), "--no-pager"])
        require(record["returncode"] == 0, "loginctl observation failed")
        return dict(line.split("=", 1) for line in record["stdout"].splitlines() if "=" in line)

    def bind_session(self):
        require(platform.system() == "Linux" and platform.machine() == "aarch64", "recorder requires the leased native arm64 Linux guest")
        require(os.getuid() == os.geteuid() != 0, "recorder must be the unprivileged desktop user")
        require(not HOSTED_RULE.exists(), "hosted automatic-allow rule must not exist during GDM evidence")
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
            if "before" in self.receipt and "after" not in self.receipt:
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
    parser.add_argument("--case", required=True, choices=("prompt", "cancel", "deny", "missing-authority"))
    parser.add_argument("--lease-reference", required=True, help="explicit coordinator lease comment/receipt reference; not a grant of authority")
    parser.add_argument("--authority-reference", required=True, help="coordinator's actual authority-window preparation receipt")
    parser.add_argument("--source-head", required=True, help="full reviewed source SHA; recorder hash is independently retained")
    parser.add_argument("--index", required=True, type=Path, help="reviewed native hosted receipts/package-index.json")
    parser.add_argument("--inventory", required=True, type=Path, help="matching hosted receipts/payload-inventory.json")
    parser.add_argument("--endpoint", default="http://127.0.0.1:17857/stable/linux.json")
    parser.add_argument("--observer", required=True)
    parser.add_argument("--observation", required=True, help="actual observed GUI outcome; never enter any password or secret")
    parser.add_argument("--screenshot", type=Path, help="fresh compositor PNG captured during this invocation; mandatory for prompt/cancel")
    parser.add_argument("--receipt", required=True, type=Path, help="new receipt path in an existing user-owned evidence directory")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    endpoint = urlsplit(args.endpoint)
    if endpoint.scheme != "http" or endpoint.hostname != "127.0.0.1" or endpoint.username or endpoint.password or endpoint.path != "/stable/linux.json" or endpoint.query or endpoint.fragment:
        parser.error("endpoint must be the literal loopback fixture /stable/linux.json")
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_head) or not 15 <= args.timeout <= 300:
        parser.error("requires a full source SHA and timeout between 15 and 300 seconds")
    if any(not value.strip() or len(value) > 2048 for value in
           (args.lease_reference, args.authority_reference, args.observer, args.observation)):
        parser.error("lease/authority references and observer statements must be nonempty and bounded")
    if args.case in ("prompt", "cancel") and args.screenshot is None:
        parser.error("prompt/cancel requires the actual compositor screenshot destination")
    if os.getuid() == 0 or args.receipt.parent.stat().st_uid != os.getuid():
        parser.error("use the unprivileged desktop user and its existing evidence directory")
    raise SystemExit(Recorder(args).run())


if __name__ == "__main__":
    main()
