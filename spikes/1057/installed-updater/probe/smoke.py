#!/usr/bin/env python3
"""Real installed-artifact smoke inside the dedicated disposable hosted container.

This script must never run on the owner's workstation or unleased VM. Root provisions
only this container; all updater calls run as fixture1057 through the real polkit seam.
An explicit per-action test allow rule supplies authority, not a graphical prompt.
"""
import argparse
import base64
import contextlib
import hashlib
import http.server
import json
import os
from pathlib import Path
import platform
import pwd
import select
import shutil
import subprocess
import threading
import time
import traceback
from urllib.parse import urlsplit


APP = "/usr/bin/campus-updater-1057"
HELPER = "/usr/lib/campus-updater-1057/inert-helper.txt"
ADAPTER = "/usr/lib/campus-updater-1057/install-deb.py"
ACTION = "dev.campus.updater1057.install"
USER = "fixture1057"
VERSIONS = ("1.0.0", "2.0.0", "3.0.0")
BEHAVIORS = {"1.0.0": "v1-baseline", "2.0.0": "v2-changed", "3.0.0": "v1-baseline"}


def require_negative_evidence(kind, fmt, target, events, requests, *, selected_url=None,
                              package_sha256=None, package_bytes=None, max_deb_bytes=None):
    """Assert this fixture's precise rejection boundary, never just nonzero exit.

    Error strings here are exact observations of the pinned test implementation, not
    product error interpretation. A changed upstream diagnostic requires review.
    """
    names = [event.get("event") for event in events]
    expected_names = ["installed_identity"]
    expected_requests = ["/stable/linux.json"]
    if kind != "missing-exact-target":
        expected_names.append("selected")
        expected_requests.append(urlsplit(selected_url).path)
    if kind in ("wrong-format", "wrong-architecture"):
        expected_names.append("verified_download")
    if kind == "wrong-format" and fmt == "deb":
        expected_names.extend(["polkit_adapter_result", "refusal_bytes"])
    expected_names.append("refused")
    if names != expected_names or [row.get("path") for row in requests] != expected_requests:
        raise RuntimeError("negative did not traverse its exact request/event sequence")
    identity = events[0]
    if identity.get("exact_target") != target or identity.get("format") != fmt or identity.get("version") != "1.0.0":
        raise RuntimeError("negative ran from a different installed fixture identity")
    if kind != "missing-exact-target":
        selected = events[1]
        if any(selected.get(key) != wanted for key, wanted in
               {"exact_target": target, "version": "2.0.0", "url": selected_url}.items()):
            raise RuntimeError("negative selected the wrong target/version/artifact")
    errors = {
        "missing-exact-target": f"the platform `{target}` was not found in the response `platforms` object",
        "bad-signature": "Invalid encoding in minisign data",
        "signed-version-mismatch": "The update was signed for version 1.0.0 but the update endpoint announced version 2.0.0. The endpoint response may have been tampered with to force installing a different release.",
        "wrong-format": "signed payload is not a native type-2 AppImage",
        "wrong-architecture": "signed payload is not a native type-2 AppImage",
    }
    if kind in ("wrong-format", "wrong-architecture"):
        verified = events[2]
        if any(verified.get(key) != wanted for key, wanted in
               {"sha256": package_sha256, "bytes": package_bytes, "version": "2.0.0"}.items()):
            raise RuntimeError("negative did not authenticate the intended bytes")
    if kind == "wrong-format" and fmt == "deb":
        outer = events[3]
        if outer.get("success") is not False or outer.get("exit_status") != 1:
            raise RuntimeError("wrong-format negative did not reach a refusing privileged adapter")
        adapter = json.loads(outer["stdout"])
        boundary = (adapter.get("phase"), adapter.get("reason"))
        if package_bytes > max_deb_bytes:
            expected_boundary = ("root_staging", "source_size_outside_measured_bound")
            if "package_sha256" in adapter or "package_bytes" in adapter:
                raise RuntimeError("oversized negative unexpectedly passed root staging")
        else:
            expected_boundary = ("signature_and_schema", "package_not_in_exact_fixture_admission")
            if adapter.get("package_sha256") != package_sha256 or adapter.get("package_bytes") != package_bytes:
                raise RuntimeError("adapter staged different wrong-format bytes")
        if boundary != expected_boundary or adapter.get("status") != "refused" or "dpkg_exit" in adapter or "authenticated_version" in adapter:
            raise RuntimeError("wrong-format package was not refused at its bounded fixture seam")
        if adapter.get("installed_version") != "1.0.0" or adapter.get("app_helper_unchanged") is not True:
            raise RuntimeError("adapter did not preserve the installed fixture")
        if set(adapter.get("before", {})) != {"app", "helper"} or adapter.get("before") != adapter.get("after"):
            raise RuntimeError("adapter hashes changed on wrong-format refusal")
        if events[4].get("app_unchanged") is not True or events[4].get("helper_unchanged") is not True:
            raise RuntimeError("app observed changed bytes after adapter refusal")
        errors[kind] = "polkit adapter did not install the fixture; inspect its receipt"
    if events[-1].get("error") != errors[kind]:
        raise RuntimeError("negative failed for an unrelated reason")


def require_privileged_signature_refusal(response, package_sha256):
    for key, wanted in {"status": "refused", "phase": "signature_and_schema",
                        "reason": "signature_verification_failed", "installed_version": "1.0.0",
                        "package_sha256": package_sha256, "app_helper_unchanged": True}.items():
        if response.get(key) != wanted:
            raise RuntimeError("privileged signature negative failed at a different boundary: " + key)
    if ("dpkg_exit" in response or "authenticated_version" in response
            or set(response.get("before", {})) != {"app", "helper"} or response.get("before") != response.get("after")):
        raise RuntimeError("privileged signature refusal installed/authenticated bytes or changed installed hashes")


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def patched_chunks(path, offset, replacement):
    with open(path, "rb") as stream:
        prefix = stream.read(offset)
        if len(prefix) != offset or len(stream.read(len(replacement))) != len(replacement):
            raise RuntimeError("negative fixture patch exceeds source bytes")
        yield prefix
        yield replacement
        yield from iter(lambda: stream.read(1024 * 1024), b"")


class Smoke:
    def __init__(self, source, output):
        self.source, self.output = source, output
        output.mkdir(parents=True, exist_ok=True)
        self.receipt = {"scope": "native installed hosted headless, not GDM", "cases": [], "commands": [], "requests": [],
                        "desktop": {"outcome": "not_run", "reason": "actual GDM/polkit prompt requires explicit later coordinator VM lease"},
                        "cross_architecture": "other architecture manifest entries are deliberate trap URLs; native jobs prove their own real targets"}
        self.children = []
        self.current = None
        self.index = json.loads((source / "receipts/package-index.json").read_text())
        self.receipt["build_index_sha256"] = digest(source / "receipts/package-index.json")
        self.receipt["source_head"] = self.index.get("source_head")
        self.arch = {"aarch64": "arm64", "x86_64": "amd64"}[platform.machine()]
        self.target_arch = {"arm64": "aarch64", "amd64": "x86_64"}[self.arch]
        self.packages = {}
        for artifact in self.index["artifacts"]:
            if artifact["architecture"] != self.arch:
                raise RuntimeError("artifact/native architecture mismatch")
            path = source / "packages" / artifact["filename"]
            if path.parent != source / "packages" or not path.is_file():
                raise RuntimeError("invalid artifact filename")
            if path.stat().st_size != artifact["bytes"] or digest(path) != artifact["sha256"]:
                raise RuntimeError("artifact checksum/size mismatch")
            artifact = dict(artifact, path=str(path))
            self.packages[artifact["version"], artifact["format"]] = artifact
        if set(self.packages) != {(version, fmt) for version in VERSIONS for fmt in ("deb", "appimage")}:
            raise RuntimeError("expected exactly v1/v2/v3 deb and AppImage")
        self.negative = json.loads((source / "receipts/signed-negative.json").read_text())
        original = self.packages["2.0.0", "appimage"]
        expected_machine = "3e00" if self.arch == "arm64" else "b700"
        for key, wanted in {"version": "2.0.0", "format": "appimage", "filename": original["filename"],
                            "offset": 18, "replacement_hex": expected_machine, "bytes": original["bytes"]}.items():
            if self.negative.get(key) != wanted:
                raise RuntimeError("signed wrong-architecture fixture schema mismatch: " + key)
        negative_hash = hashlib.sha256()
        for block in patched_chunks(original["path"], 18, bytes.fromhex(expected_machine)):
            negative_hash.update(block)
        if negative_hash.hexdigest() != self.negative["sha256"] or not self.negative.get("signature"):
            raise RuntimeError("signed wrong-architecture fixture checksum/signature missing")
        self.receipt["signed_wrong_architecture_negative"] = self.negative
        self.receipt["architecture"] = self.arch
        self.receipt["uname"] = list(platform.uname())
        self.receipt["os_release"] = Path("/etc/os-release").read_text()
        self.receipt["runtime_packages"] = Path("/usr/local/share/campus-updater-1057-smoke-packages.tsv").read_text()
        self.user = pwd.getpwnam(USER)
        self.home = Path(self.user.pw_dir)
        self.work = self.home / "installed-updater-1057"
        self.work.mkdir(mode=0o700)
        os.chown(self.work, self.user.pw_uid, self.user.pw_gid)
        self.expected = {}

    def save(self):
        (self.output / "installed-smoke.json").write_text(json.dumps(self.receipt, indent=2) + "\n")

    def command(self, args, *, user=False, check=True, timeout=90, cwd=None):
        if user:
            args = ["runuser", "-u", USER, "--", "env", "DISPLAY=:99", "XDG_RUNTIME_DIR=/run/user/1057",
                    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1057/bus", *map(str, args)]
        args = list(map(str, args))
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        except subprocess.TimeoutExpired as error:
            def rendered(value):
                return value.decode(errors="replace") if isinstance(value, bytes) else value
            self.receipt["commands"].append({"case": self.current, "argv": args, "returncode": None,
                                              "timeout_seconds": timeout, "stdout": rendered(error.stdout),
                                              "stderr": rendered(error.stderr)})
            self.save()
            raise
        record = {"case": self.current, "argv": args, "returncode": result.returncode,
                  "stdout": result.stdout, "stderr": result.stderr}
        self.receipt["commands"].append(record)
        self.save()
        if check and result.returncode:
            raise RuntimeError("command failed: " + args[0] + " (see receipt)")
        return result

    def case(self, name, operation):
        self.current = name
        try:
            evidence = operation()
            self.receipt["cases"].append({"name": name, "outcome": "passed", "evidence": evidence})
            self.save()
            return True
        except Exception as error:
            self.receipt["cases"].append({"name": name, "outcome": "failed", "error": str(error),
                                          "traceback": traceback.format_exc()})
            self.save()
            return False

    def start(self, args, logfile):
        stream = open(self.output / logfile, "w")
        child = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT)
        self.children.append((child, stream))
        return child

    def bootstrap(self):
        if os.geteuid() or not Path("/.dockerenv").exists():
            raise RuntimeError("requires the dedicated disposable Docker root context")
        self.command(["python3", "-B", "/opt/fixture/adapter/bootstrap.py", "--bundle", self.source / "bootstrap"])
        # Initial installation is explicit root provisioning; updates below use only pkexec.
        admission = json.loads(Path("/etc/campus-updater-1057/admission.json").read_text())
        self.max_deb_bytes = admission["max_package_bytes"]
        self.receipt["admission_sha256"] = digest("/etc/campus-updater-1057/admission.json")
        if not admission:
            raise RuntimeError("missing fixture admission")
        initial = self.packages["1.0.0", "deb"]
        initial_record = next(record for record in admission["packages"] if record["version"] == "1.0.0")
        if initial_record["sha256"] != initial["sha256"] or initial_record["size"] != initial["bytes"]:
            raise RuntimeError("initial deb differs from exact root fixture admission")
        self.command(["dpkg", "--install", initial["path"]])
        Path("/run/dbus").mkdir(parents=True, exist_ok=True)
        runtime = Path("/run/user/1057")
        runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
        runtime.chmod(0o700)
        os.chown(runtime, self.user.pw_uid, self.user.pw_gid)
        self.command(["dbus-daemon", "--system", "--fork"])
        rule = Path("/etc/polkit-1/rules.d/49-campus-updater-1057-headless.rules")
        rule.write_text('polkit.addRule(function(action, subject) {\n'
                        '  if (action.id === "' + ACTION + '" && subject.user === "' + USER + '")\n'
                        '    return polkit.Result.YES;\n});\n')
        rule.chmod(0o644)
        self.receipt["headless_polkit_rule_sha256"] = digest(rule)
        authority = self.start(["/usr/lib/polkit-1/polkitd", "--no-debug"], "polkit.log")
        self.start(["Xvfb", ":99", "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-ac"], "xvfb.log")
        self.command(["dbus-daemon", "--session", "--address=unix:path=/run/user/1057/bus", "--fork"], user=True)
        for unused in range(30):
            if Path("/tmp/.X11-unix/X99").exists() and self.command(["pkaction", "--action-id", ACTION], check=False).returncode == 0:
                break
            if authority.poll() is not None:
                raise RuntimeError("polkit authority exited")
            time.sleep(0.1)
        else:
            raise RuntimeError("headless display/authority not ready")
        return {"authority": "temporary exact-action exact-user allow rule", "graphical_prompt": "not_run"}

    def inventory(self):
        # Extraction here is byte inventory only; every execution uses installed deb/outer AppImage.
        for version in VERSIONS:
            for fmt in ("deb", "appimage"):
                artifact = self.packages[version, fmt]
                destination = Path("/tmp") / ("inventory-" + version + "-" + fmt)
                destination.mkdir()
                if fmt == "deb":
                    self.command(["dpkg-deb", "--extract", artifact["path"], destination])
                    root = destination
                else:
                    # The real AppImage runtime handles this inspection; it is never the smoke launch.
                    local = self.work / ("inventory-" + version + ".AppImage")
                    shutil.copyfile(artifact["path"], local)
                    local.chmod(0o755)
                    self.command([local, "--appimage-extract", "usr/bin/campus-updater-1057"], cwd=destination)
                    self.command([local, "--appimage-extract", "usr/lib/campus-updater-1057/inert-helper.txt"], cwd=destination)
                    local.unlink()
                    root = destination / "squashfs-root"
                self.expected[version, fmt] = {"app_sha256": digest(root / APP.lstrip("/")),
                                               "helper_sha256": digest(root / HELPER.lstrip("/"))}
                shutil.rmtree(destination)
        self.receipt["expected_payloads"] = [dict(version=v, format=f, **value) for (v, f), value in self.expected.items()]
        return self.receipt["expected_payloads"]

    def serve(self):
        fixture = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, unused, *args):
                pass

            def do_GET(self):
                fixture.receipt["requests"].append({"case": fixture.current, "path": self.path})
                if self.path == "/stable/linux.json":
                    body = json.dumps(fixture.manifest).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if self.path == "/negative/wrong-architecture":
                    self.send_response(200)
                    self.send_header("Content-Length", str(fixture.negative["bytes"]))
                    self.end_headers()
                    source = fixture.packages["2.0.0", "appimage"]["path"]
                    for block in patched_chunks(source, fixture.negative["offset"], bytes.fromhex(fixture.negative["replacement_hex"])):
                        self.wfile.write(block)
                    return
                match = next((a for a in fixture.packages.values() if self.path == "/packages/" + a["filename"]), None)
                if not match:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(match["bytes"]))
                self.end_headers()
                with open(match["path"], "rb") as stream:
                    shutil.copyfileobj(stream, self.wfile, 1024 * 1024)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = "http://127.0.0.1:" + str(self.server.server_port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def signature(self, artifact):
        signature = artifact["signature"]
        candidate = self.source / "packages" / signature
        if len(signature) < 255 and candidate.is_file():
            return candidate.read_text().strip()
        return signature.strip()

    def release(self, version):
        self.manifest = {"version": version, "platforms": {}}
        for fmt in ("deb", "appimage"):
            artifact = self.packages[version, fmt]
            self.manifest["platforms"][artifact["target"]] = {
                "url": self.url + "/packages/" + artifact["filename"], "signature": self.signature(artifact)}
        other = "x86_64" if self.target_arch == "aarch64" else "aarch64"
        for fmt in ("deb", "appimage"):
            target = "linux-" + other + "-" + fmt
            self.manifest["platforms"][target] = {"url": self.url + "/unavailable/" + target, "signature": "deliberate-other-architecture-trap"}

    def invoke(self, executable, mode, *, success=True):
        args = [executable, mode]
        if mode != "--diagnose":
            args.append(self.url + "/stable/linux.json")
        result = self.command(args, user=True, check=False, timeout=120)
        if (result.returncode == 0) != success:
            raise RuntimeError("unexpected installed command result")
        events = []
        for line in result.stdout.splitlines():
            if line.startswith("{"):
                events.append(json.loads(line))
        if not events:
            raise RuntimeError("installed process emitted no diagnostic events")
        return events

    def identity(self, executable, version, fmt):
        events = self.invoke(executable, "--diagnose")
        value = next(event for event in events if event.get("event") == "installed_identity")
        expected = self.expected[version, fmt]
        for key, wanted in dict(expected, version=version, behavior=BEHAVIORS[version], format=fmt,
                                architecture=self.target_arch, exact_target="linux-" + self.target_arch + "-" + fmt).items():
            if value.get(key) != wanted:
                raise RuntimeError("installed identity mismatch: " + key)
        if fmt == "appimage" and value.get("outer_sha256") != self.packages[version, fmt]["sha256"]:
            raise RuntimeError("outer AppImage does not match expected package")
        return value

    def unchanged(self, before, executable, version, fmt):
        after = self.identity(executable, version, fmt)
        for field in ("app_sha256", "helper_sha256", "outer_sha256"):
            if before.get(field) != after.get(field):
                raise RuntimeError("refusal changed installed bytes: " + field)
        return {"before": before, "after": after}

    def missing_target(self, executable, fmt):
        before = self.identity(executable, "1.0.0", fmt)
        self.release("2.0.0")
        target = "linux-" + self.target_arch + "-" + fmt
        alternate = "linux-" + self.target_arch + "-" + ("appimage" if fmt == "deb" else "deb")
        del self.manifest["platforms"][target]
        self.manifest["platforms"]["linux-" + self.target_arch] = self.manifest["platforms"][alternate]
        offset = len(self.receipt["requests"])
        events = self.invoke(executable, "--update", success=False)
        require_negative_evidence("missing-exact-target", fmt, target, events, self.receipt["requests"][offset:])
        return dict(self.unchanged(before, executable, "1.0.0", fmt), manifest=self.manifest)

    def tampered(self, executable, fmt, kind):
        before = self.identity(executable, "1.0.0", fmt)
        self.release("2.0.0")
        target = "linux-" + self.target_arch + "-" + fmt
        selected = self.manifest["platforms"][target]
        payload = self.packages["2.0.0", fmt]
        if kind == "bad-signature":
            selected["signature"] = base64.b64encode(b"invalid disposable fixture signature").decode()
        elif kind == "signed-version-mismatch":
            older = self.packages["1.0.0", fmt]
            selected.update(url=self.url + "/packages/" + older["filename"], signature=self.signature(older))
        elif kind == "wrong-format":
            wrong = self.packages["2.0.0", "appimage" if fmt == "deb" else "deb"]
            selected.update(url=self.url + "/packages/" + wrong["filename"], signature=self.signature(wrong))
            payload = wrong
        elif kind == "wrong-architecture":
            if fmt != "appimage":
                raise RuntimeError("signed ELF negative applies only to AppImage")
            selected.update(url=self.url + "/negative/wrong-architecture", signature=self.negative["signature"])
            payload = self.negative
        offset = len(self.receipt["requests"])
        events = self.invoke(executable, "--update", success=False)
        require_negative_evidence(kind, fmt, target, events, self.receipt["requests"][offset:],
                                  selected_url=selected["url"], package_sha256=payload["sha256"],
                                  package_bytes=payload["bytes"], max_deb_bytes=self.max_deb_bytes)
        return self.unchanged(before, executable, "1.0.0", fmt)

    def privileged_bad_signature(self):
        before = self.identity(APP, "1.0.0", "deb")
        artifact = self.packages["2.0.0", "deb"]
        package = self.work / "signature-negative.deb"
        signature = self.work / "signature-negative.sig"
        shutil.copyfile(artifact["path"], package)
        signature.write_text(self.signature(self.packages["1.0.0", "deb"]))
        for path in (package, signature):
            os.chown(path, self.user.pw_uid, self.user.pw_gid)
            path.chmod(0o600)
        try:
            result = self.command(["pkexec", "--disable-internal-agent", ADAPTER, package, signature], user=True, check=False)
            if result.returncode != 1:
                raise RuntimeError("signature negative did not reach adapter refusal")
            response = json.loads(result.stdout.strip())
            require_privileged_signature_refusal(response, artifact["sha256"])
            return dict(self.unchanged(before, APP, "1.0.0", "deb"), adapter=response)
        finally:
            package.unlink(missing_ok=True)
            signature.unlink(missing_ok=True)

    def update(self, executable, old, new, fmt):
        self.identity(executable, old, fmt)
        self.release(new)
        events = self.invoke(executable, "--check")
        selected = next(event for event in events if event.get("event") == "selected")
        if selected.get("exact_target") != "linux-" + self.target_arch + "-" + fmt:
            raise RuntimeError("selected a different installed target")
        events = self.invoke(executable, "--update")
        return {"events": events, "relaunch_identity": self.identity(executable, new, fmt)}

    def replay(self, version):
        before = self.identity(APP, "2.0.0", "deb")
        artifact = self.packages[version, "deb"]
        package = self.work / ("replay-" + version + ".deb")
        signature = self.work / ("replay-" + version + ".sig")
        shutil.copyfile(artifact["path"], package)
        signature.write_text(self.signature(artifact))
        for path in (package, signature):
            os.chown(path, self.user.pw_uid, self.user.pw_gid)
            path.chmod(0o600)
        result = self.command(["pkexec", "--disable-internal-agent", ADAPTER, package, signature], user=True, check=False)
        if result.returncode == 0:
            raise RuntimeError("privileged signed replay was accepted")
        response = json.loads(result.stdout.strip())
        for key, expected in {"status": "refused", "phase": "forward_version",
                              "reason": "signed_same_or_lower_version", "authenticated_version": version,
                              "installed_version": "2.0.0", "app_helper_unchanged": True,
                              "package_sha256": artifact["sha256"]}.items():
            if response.get(key) != expected:
                raise RuntimeError("refusal did not prove authenticated privileged replay: " + key)
        if "dpkg_exit" in response:
            raise RuntimeError("privileged replay invoked dpkg")
        package.unlink()
        signature.unlink()
        return dict(self.unchanged(before, APP, "2.0.0", "deb"), adapter=response)

    def caller_substitution(self):
        before = self.identity(APP, "2.0.0", "deb")
        artifact = self.packages["1.0.0", "deb"]
        package = self.work / "caller-substitution.deb"
        replacement = self.work / "caller-substitution-replacement.deb"
        signature = self.work / "caller-substitution.sig"
        invalid = b"invalid caller replacement: fixture 1057\n"
        shutil.copyfile(artifact["path"], package)
        replacement.write_bytes(invalid)
        signature.write_text(self.signature(artifact))
        for path in (package, replacement, signature):
            os.chown(path, self.user.pw_uid, self.user.pw_gid)
            path.chmod(0o600)
        watcher_command = ["runuser", "-u", USER, "--", "python3", "-B",
                           "/opt/fixture/probe/replace-on-open.py", "--source", str(package),
                           "--replacement", str(replacement)]
        watcher = subprocess.Popen(watcher_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        first_line = ""
        try:
            if not select.select([watcher.stdout], [], [], 5)[0]:
                raise RuntimeError("caller substitution watcher did not arm")
            first_line = watcher.stdout.readline()
            ready = json.loads(first_line)
            if ready.get("event") != "watch_ready" or ready.get("uid") != self.user.pw_uid:
                raise RuntimeError("caller substitution watcher is not armed as fixture user")
            started = time.monotonic_ns()
            result = self.command(["pkexec", "--disable-internal-agent", ADAPTER, package, signature], user=True, check=False)
            finished = time.monotonic_ns()
            stdout, stderr = watcher.communicate(timeout=35)
            self.receipt["commands"].append({"case": self.current, "argv": watcher_command,
                                              "returncode": watcher.returncode, "stdout": first_line + stdout, "stderr": stderr})
            self.save()
            if watcher.returncode:
                raise RuntimeError("caller replacement timing was not proven; see ordered inotify receipt")
            observed = next(json.loads(line) for line in stdout.splitlines()
                            if json.loads(line).get("event") == "caller_path_replaced")
            if not observed.get("replacement_before_original_reader_close"):
                raise RuntimeError("replacement did not occur before original source closed")
            if not all(started <= event["monotonic_ns"] <= finished for event in observed["events"]):
                raise RuntimeError("caller replacement observations fall outside privileged invocation")
            expected_replacement = hashlib.sha256(invalid).hexdigest()
            if observed.get("replacement_sha256") != expected_replacement or digest(package) != expected_replacement:
                raise RuntimeError("caller path was not replaced with expected invalid bytes")
            response = json.loads(result.stdout.strip())
            if result.returncode == 0:
                raise RuntimeError("substituted lower version unexpectedly installed")
            for key, wanted in {"status": "refused", "phase": "forward_version", "reason": "signed_same_or_lower_version",
                                "authenticated_version": "1.0.0", "installed_version": "2.0.0",
                                "package_sha256": artifact["sha256"], "app_helper_unchanged": True}.items():
                if response.get(key) != wanted:
                    raise RuntimeError("root did not authenticate original staged v1 after substitution: " + key)
            if "dpkg_exit" in response:
                raise RuntimeError("caller substitution replay invoked dpkg")
            return dict(self.unchanged(before, APP, "2.0.0", "deb"), adapter=response,
                        watcher=observed, invocation_started_ns=started, invocation_finished_ns=finished,
                        caller_before_sha256=artifact["sha256"], caller_after_sha256=expected_replacement)
        finally:
            if watcher.poll() is None:
                watcher.kill()
                stdout, stderr = watcher.communicate()
                self.receipt["commands"].append({"case": self.current, "argv": watcher_command,
                                                  "returncode": watcher.returncode, "stdout": first_line + stdout, "stderr": stderr})
            for path in (package, replacement, signature):
                path.unlink(missing_ok=True)

    def run_format(self, fmt):
        if fmt == "deb":
            executable = APP
        else:
            if not Path("/dev/fuse").exists():
                raise RuntimeError("actual AppImage FUSE device unavailable; no extraction fallback")
            executable = self.work / "installed.AppImage"
            shutil.copyfile(self.packages["1.0.0", fmt]["path"], executable)
            executable.chmod(0o755)
            os.chown(executable, self.user.pw_uid, self.user.pw_gid)
        if not self.case(fmt + "/installed-v1", lambda: self.identity(executable, "1.0.0", fmt)):
            return
        self.case(fmt + "/missing-exact-target", lambda: self.missing_target(executable, fmt))
        for kind in ("bad-signature", "signed-version-mismatch", "wrong-format"):
            self.case(fmt + "/" + kind, lambda kind=kind: self.tampered(executable, fmt, kind))
        if fmt == "appimage":
            self.case("appimage/wrong-architecture", lambda: self.tampered(executable, fmt, "wrong-architecture"))
        else:
            self.case("deb/privileged-bad-signature", self.privileged_bad_signature)
        if not self.case(fmt + "/v1-to-v2", lambda: self.update(executable, "1.0.0", "2.0.0", fmt)):
            return
        if fmt == "deb":
            for version in ("1.0.0", "2.0.0"):
                self.case("deb/privileged-replay-" + version, lambda version=version: self.replay(version))
            self.case("deb/live-caller-substitution", self.caller_substitution)
        for version in ("1.0.0", "2.0.0"):
            def no_newer(version=version):
                before = self.identity(executable, "2.0.0", fmt)
                self.release(version)
                events = self.invoke(executable, "--check")
                if not any(event.get("event") == "no_newer_release" for event in events):
                    raise RuntimeError("updater offered non-increasing version")
                return self.unchanged(before, executable, "2.0.0", fmt)
            self.case(fmt + "/updater-replay-" + version, no_newer)
        self.case(fmt + "/forward-version-rollback-v3", lambda: self.update(executable, "2.0.0", "3.0.0", fmt))

    def run(self):
        try:
            if not self.case("bootstrap", self.bootstrap) or not self.case("package-byte-inventory", self.inventory):
                return 1
            self.serve()
            for fmt in ("deb", "appimage"):
                def group(fmt=fmt):
                    first = len(self.receipt["cases"])
                    self.run_format(fmt)
                    if any(case["outcome"] == "failed" for case in self.receipt["cases"][first:]):
                        raise RuntimeError("installed integration has failed cases; remaining dependent cases are not proven")
                    return {"format": fmt}
                self.case(fmt + "/integration", group)
            return int(any(case["outcome"] == "failed" for case in self.receipt["cases"]))
        finally:
            if hasattr(self, "server"):
                self.server.shutdown()
            for child, stream in reversed(self.children):
                child.terminate()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    child.wait(timeout=5)
                stream.close()
            self.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if os.geteuid() or not Path("/.dockerenv").exists():
        parser.error("this probe runs only as root in its disposable hosted Docker container")
    try:
        smoke = Smoke(args.input.resolve(), args.output.resolve())
    except Exception as error:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "installed-smoke.json").write_text(json.dumps({
            "scope": "native installed hosted headless, not GDM",
            "cases": [{"name": "input-validation", "outcome": "failed", "error": str(error),
                       "traceback": traceback.format_exc()}]}, indent=2) + "\n")
        raise SystemExit(1)
    raise SystemExit(smoke.run())


if __name__ == "__main__":
    main()
