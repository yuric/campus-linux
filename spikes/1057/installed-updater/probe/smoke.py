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
import shutil
import subprocess
import threading
import time
import traceback


APP = "/usr/bin/campus-updater-1057"
HELPER = "/usr/lib/campus-updater-1057/inert-helper.txt"
ADAPTER = "/usr/lib/campus-updater-1057/install-deb.py"
ACTION = "dev.campus.updater1057.install"
USER = "fixture1057"
VERSIONS = ("1.0.0", "2.0.0", "3.0.0")
BEHAVIORS = {"1.0.0": "v1-baseline", "2.0.0": "v2-changed", "3.0.0": "v1-baseline"}


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


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
        self.invoke(executable, "--update", success=False)
        if any(row["path"] != "/stable/linux.json" for row in self.receipt["requests"][offset:]):
            raise RuntimeError("missing exact target downloaded another artifact")
        return dict(self.unchanged(before, executable, "1.0.0", fmt), manifest=self.manifest)

    def tampered(self, executable, fmt, kind):
        before = self.identity(executable, "1.0.0", fmt)
        self.release("2.0.0")
        target = "linux-" + self.target_arch + "-" + fmt
        selected = self.manifest["platforms"][target]
        if kind == "bad-signature":
            selected["signature"] = base64.b64encode(b"invalid disposable fixture signature").decode()
        elif kind == "signed-version-mismatch":
            older = self.packages["1.0.0", fmt]
            selected.update(url=self.url + "/packages/" + older["filename"], signature=self.signature(older))
        elif kind == "wrong-format":
            wrong = self.packages["2.0.0", "appimage" if fmt == "deb" else "deb"]
            selected.update(url=self.url + "/packages/" + wrong["filename"], signature=self.signature(wrong))
        self.invoke(executable, "--update", success=False)
        return self.unchanged(before, executable, "1.0.0", fmt)

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
        if not self.case(fmt + "/v1-to-v2", lambda: self.update(executable, "1.0.0", "2.0.0", fmt)):
            return
        if fmt == "deb":
            for version in ("1.0.0", "2.0.0"):
                self.case("deb/privileged-replay-" + version, lambda version=version: self.replay(version))
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
