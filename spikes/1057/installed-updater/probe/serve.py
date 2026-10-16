#!/usr/bin/env python3
"""Unprivileged, fixed-file loopback server for a later explicitly leased desktop run."""
import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import threading
import time

import gated


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True, type=Path, help="hosted output receipts/package-index.json")
    parser.add_argument("--version", required=True, choices=("1", "2", "3"))
    parser.add_argument("--missing-target", help="omit this exact key and retain a cross-format generic trap")
    parser.add_argument("--port", type=int, default=17857)
    parser.add_argument("--log", type=Path, help="append request/manifest JSON lines here as well as stdout")
    parser.add_argument("--gate-directory", type=Path, help="optional root-controlled one-shot denial manifest gate")
    args = parser.parse_args()
    if args.gate_directory and (args.version != "2" or args.missing_target or args.port != 17857):
        parser.error("gated denial uses only the fixed v2 endpoint, without missing-target mode")
    if os.geteuid() == 0:
        parser.error("run as the unprivileged desktop fixture user")
    if not 1024 <= args.port <= 65535:
        parser.error("port must be in 1024..65535")
    index_path = args.index.resolve(strict=True)
    packages = index_path.parent.parent / "packages"
    index = json.loads(index_path.read_text())
    artifacts = {}
    for artifact in index["artifacts"]:
        filename = artifact["filename"]
        path = packages / filename
        if Path(filename).name != filename or path.is_symlink() or not path.is_file():
            parser.error("index must reference only regular files directly inside packages/")
        if path.stat().st_size != artifact["bytes"] or digest(path) != artifact["sha256"]:
            parser.error("indexed package size/hash mismatch: " + filename)
        expected_arch = {"arm64": "aarch64", "amd64": "x86_64"}.get(artifact["architecture"])
        if artifact["format"] not in ("deb", "appimage") or artifact["target"] != "linux-" + str(expected_arch) + "-" + artifact["format"]:
            parser.error("invalid package target identity")
        if filename in artifacts:
            parser.error("duplicate indexed filename")
        artifacts[filename] = dict(artifact, path=path)
    version = args.version + ".0.0"
    manifest = {"version": version, "platforms": {}}
    endpoint = "http://127.0.0.1:" + str(args.port)
    for filename, artifact in artifacts.items():
        if artifact["version"] == version:
            if artifact["target"] in manifest["platforms"]:
                parser.error("duplicate version/target entry")
            manifest["platforms"][artifact["target"]] = {
                "url": endpoint + "/packages/" + filename, "signature": artifact["signature"]}
    if not manifest["platforms"]:
        parser.error("selected version has no indexed packages")
    if args.missing_target:
        if not re.fullmatch(r"linux-(aarch64|x86_64)-(deb|appimage)", args.missing_target):
            parser.error("missing target must be one of the four exact Linux format/architecture keys")
        if args.missing_target not in manifest["platforms"]:
            parser.error("cannot remove a target that has no real indexed artifact")
        generic, fmt = args.missing_target.rsplit("-", 1)
        alternate = generic + "-" + ("appimage" if fmt == "deb" else "deb")
        if alternate not in manifest["platforms"]:
            parser.error("missing-target probe needs the real opposite-format entry")
        del manifest["platforms"][args.missing_target]
        manifest["platforms"][generic] = dict(manifest["platforms"][alternate])
    log_lock = threading.Lock()

    def record(value):
        value["time_ns"] = time.time_ns()
        encoded = json.dumps(value, sort_keys=True)
        with log_lock:
            print(encoded, flush=True)
            if args.log:
                with args.log.open("a") as stream:
                    stream.write(encoded + "\n")

    gate = gated.ManifestGate(args.gate_directory, record) if args.gate_directory else None

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, unused, *values):
            pass

        def do_GET(self):
            if self.path == "/stable/linux.json":
                if gate:
                    try:
                        gate.manifest(self.connection)
                    except Exception as error:
                        gate.fail(error)
                        self.send_error(409)
                        return
                body = json.dumps(manifest).encode()
                record({"event": "request", "path": self.path, "status": 200, "bytes": len(body)})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                    self.wfile.flush()
                    if gate:
                        gate.delivered()
                except OSError as error:
                    if gate:
                        gate.fail(error)
                    raise
                return
            artifact = artifacts.get(self.path.removeprefix("/packages/")) if self.path.startswith("/packages/") else None
            if artifact is None:
                record({"event": "request", "path": self.path, "status": 404})
                self.send_error(404)
                return
            if gate:
                try:
                    gate.package(artifact)
                except Exception as error:
                    gate.fail(error)
                    self.send_error(409)
                    return
            # Refuse replacement since startup instead of serving bytes under a stale receipt.
            if artifact["path"].stat().st_size != artifact["bytes"] or digest(artifact["path"]) != artifact["sha256"]:
                record({"event": "request", "path": self.path, "status": 409, "reason": "package_changed"})
                self.send_error(409)
                return
            record({"event": "request", "path": self.path, "status": 200, "bytes": artifact["bytes"], "sha256": artifact["sha256"]})
            self.send_response(200)
            self.send_header("Content-Length", str(artifact["bytes"]))
            self.end_headers()
            with artifact["path"].open("rb") as stream:
                shutil.copyfileobj(stream, self.wfile, 1024 * 1024)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    record({"event": "serving", "endpoint": endpoint + "/stable/linux.json", "index_sha256": digest(index_path),
            "source_head": index.get("source_head"), "manifest": manifest,
            "scope": "only real indexed targets; absent architectures are not claimed"})
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
