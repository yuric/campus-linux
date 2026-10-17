#!/usr/bin/python3 -I
"""Root provisioning only, inside an explicitly leased disposable Linux environment.

This is not the app update entry point. It neither installs a deb nor acquires root.
The coordinator reviews the hosted artifact digest before running this bootstrap.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat

parser = argparse.ArgumentParser()
parser.add_argument("--bundle", type=Path, required=True)
args = parser.parse_args()
if os.geteuid() != 0 or os.environ.get("PKEXEC_UID") is not None:
    raise SystemExit("bootstrap requires a root provisioning session, never app elevation")
if not args.bundle.is_absolute():
    raise SystemExit("bootstrap bundle path must be absolute")

spec = importlib.util.spec_from_file_location("adapter", args.bundle / "install-deb.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

destinations = {
    "install-deb.py": (adapter.LIB / "install-deb.py", 0o755, 65536),
    "verify-signature": (adapter.LIB / "verify-signature", 0o755, 64 * 1024 * 1024),
    "public-key.txt": (adapter.TRUST / "public-key.txt", 0o644, adapter.SIGNATURE_LIMIT),
    "admission.json": (adapter.TRUST / "admission.json", 0o644, adapter.ADMISSION_LIMIT),
    "dev.projectcampus.updater1057.policy":
        (Path("/usr/share/polkit-1/actions/dev.projectcampus.updater1057.policy"), 0o644, 8192),
}
content = {name: adapter.read_limited((args.bundle / name).resolve(strict=True), limit)
           for name, (_, _, limit) in destinations.items()}
admission = adapter.validate_admission(json.loads(content["admission.json"]))
# The separate public key and verifier are outside all permitted package payload paths.
# Updates cannot replace the admission, root-owned key, verifier, adapter, or polkit action.
for destination, _, _ in destinations.values():
    if destination.exists() or destination.is_symlink():
        raise SystemExit("bootstrap refuses existing trust; review/remove only in disposable provisioning")
for directory, mode in ((adapter.LIB, 0o755), (adapter.TRUST, 0o755), (adapter.STATE, 0o700),
                        (Path("/usr/share/polkit-1/actions"), 0o755)):
    directory.mkdir(mode=mode, parents=True, exist_ok=True)
    adapter.root_path(directory, directory=True)
    if stat.S_IMODE(directory.stat().st_mode) != mode:
        raise SystemExit("bootstrap directory has unexpected permissions")
written = []
try:
    for name, (destination, mode, _) in destinations.items():
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
        with os.fdopen(fd, "wb") as output:
            output.write(content[name])
            output.flush()
            os.fsync(output.fileno())
        os.chmod(destination, mode)
        written.append(destination)
except BaseException:
    for destination in written:
        destination.unlink()
    raise
print(json.dumps({"status": "trust_provisioned", "architecture": admission["architecture"],
    "files": {str(destination): {"sha256": hashlib.sha256(content[name]).hexdigest(), "mode": oct(mode), "uid": 0}
              for name, (destination, mode, _) in destinations.items()}}, sort_keys=True))
