#!/usr/bin/env python3
"""Check the imported bundle; optionally compare it with its merged server ref."""
import argparse
import hashlib
import json
import pathlib
import posixpath
import re
import stat
import subprocess
from urllib.parse import urlsplit

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = "api/docs/openapi.yaml"


def leaves(root):
    result = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"non-regular contract entry: {path.relative_to(root)}")
        result[path.relative_to(root).as_posix()] = (
            "100755" if mode & 0o111 else "100644", path.read_bytes())
    return result


def external_targets(value):
    targets = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "externalValue":
                if not isinstance(child, str) or not child:
                    raise ValueError("invalid externalValue")
                url = urlsplit(child)
                if url.scheme or url.netloc or url.query or url.fragment:
                    raise ValueError("externalValue must name a bundled local file")
                target = posixpath.normpath(posixpath.join(posixpath.dirname(SPEC), child))
                if target.startswith(("/", "../")) or target == "..":
                    raise ValueError("externalValue escapes contract bundle")
                targets.add(target)
            else:
                targets.update(external_targets(child))
    elif isinstance(value, list):
        for child in value:
            targets.update(external_targets(child))
    return targets


def check(root, server=None, reexport=None):
    files = leaves(root)
    source = files[".source"][1].decode("ascii")
    match = re.fullmatch(r"yuric/campus-server@([0-9a-f]{40})\n", source)
    if not match:
        raise ValueError("invalid contract/.source provenance")
    sha = match[1]
    spec = yaml.safe_load(files[SPEC][1])
    if not isinstance(spec, dict) or not spec.get("openapi") or not spec.get("paths"):
        raise ValueError("OpenAPI snapshot missing/empty")
    targets = external_targets(spec)
    for target in sorted(targets):
        if target not in files:
            raise ValueError(f"missing externalValue target: {target}")
    for name, (_, data) in files.items():
        if name.endswith(".json"):
            json.loads(data)
    if server is not None:
        def git(*args):
            return subprocess.check_output(["git", "-C", str(server), *args])
        git("merge-base", "--is-ancestor", sha, "origin/main")
        entries = {}
        for entry in git("ls-tree", "-rz", sha).split(b"\0"):
            if entry:
                meta, name = entry.split(b"\t", 1)
                mode, kind, oid = meta.decode().split()
                entries[name.decode()] = (mode, kind, oid)
        expected = {SPEC, *targets, *(p for p in entries if p.startswith("contracts/"))}
        if set(files) != expected | {".source"}:
            raise ValueError("contract leaf paths differ from server bundle")
        for name in sorted(expected):
            mode, kind, oid = entries[name]
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ValueError(f"non-regular server entry: {name}")
            if files[name] != (mode, git("cat-file", "blob", oid)):
                raise ValueError(f"contract mode/bytes differ from server: {name}")
    if reexport is not None and files != leaves(reexport):
        raise ValueError("fresh re-export differs in leaf paths, modes or bytes")
    # Stable digest: sorted path/mode/content-hash records, including .source.
    records = [[name, mode, hashlib.sha256(data).hexdigest()]
               for name, (mode, data) in sorted(files.items())]
    digest = hashlib.sha256(json.dumps(records, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    return {"source": source.strip(), "files": len(files), "paths": len(spec["paths"]),
            "external_targets": len(targets), "tree_sha256": digest,
            "server_comparison": server is not None, "reexport_comparison": reexport is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", type=pathlib.Path, help="isolated server repo with recorded ref and origin/main")
    parser.add_argument("--reexport", type=pathlib.Path, help="freshly exported contract directory")
    args = parser.parse_args()
    print(json.dumps(check(ROOT / "contract", args.server, args.reexport), indent=2))


if __name__ == "__main__":
    main()
