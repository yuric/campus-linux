#!/usr/bin/env python3
"""Bounded Docker verification, identical entry point locally and on public hosted CI."""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def run(args, timeout=60, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, timeout=timeout, **kwargs)


def output(args):
    return run(args, capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", choices=["amd64", "arm64"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform == "darwin" and shutil.disk_usage(ROOT).free < 35 * 1024**3:
        raise RuntimeError("coordinator free-space floor: need at least 35 GiB before Docker work")
    head = output(["git", "rev-parse", "HEAD"])
    # No host credentials, Docker socket or home directory enter the test container.
    # A tar export keeps ignored/private host files out and tests the committed head.
    args.output.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / "ci/toolchain-lock.json").read_text())
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="campus-981-") as tmp:
        staging = Path(tmp)
        # Only public committed source lives here. Container root has no DAC override
        # after cap-drop=ALL and must be able to traverse the host-owned export.
        staging.chmod(0o755)
        archive = run(["git", "archive", "HEAD"], capture_output=True).stdout
        run(["tar", "-xf", "-", "-C", str(staging)], input=archive)
        tag = f"campus-linux-verify:{head[:12]}-{args.arch}"
        run(["docker", "build", "--platform", "linux/" + args.arch, "-f",
             str(staging / "ci/Dockerfile.verify"), "-t", tag, str(staging)], timeout=900)
        image = output(["docker", "image", "inspect", tag, "--format", "{{.Id}}"])
        name = f"campus-981-verify-{args.arch}-{os.getpid()}"
        command = ["docker", "run", "--rm", "--name", name, "--platform", "linux/" + args.arch,
                   "--cpus=2", "--memory=2g", "--pids-limit=128", "--network=none",
                   "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                   "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m", "-v",
                   f"{staging}:/workspace:ro", image]
        try:
            result = run(command, timeout=600, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            log = (error.stdout or "") + (error.stderr or "")
            (args.output / f"failure-{args.arch}.log").write_text(log)
            print(log, end="")
            raise
        finally:
            # Timeout kills the Docker client; explicitly remove only our named container.
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30)
        log = result.stdout + result.stderr
        print(log, end="")
        packages = output(["docker", "run", "--rm", "--network=none", "--entrypoint=cat", image,
                           "/usr/local/share/campus-verification-packages.tsv"])
        arch = output(["docker", "run", "--rm", "--network=none", "--entrypoint=uname", image, "-m"])
        if arch != {"amd64": "x86_64", "arm64": "aarch64"}[args.arch]:
            raise ValueError("container architecture mismatch")
        log_name = f"verification-{args.arch}.log"
        packages_name = f"packages-{args.arch}.tsv"
        (args.output / log_name).write_text(log)
        (args.output / packages_name).write_text(packages)
        receipt = {"version": 1, "repository": "yuric/campus-linux", "head": head,
                   "archive_sha256": hashlib.sha256(archive).hexdigest(), "arch": args.arch,
                   "base": lock["verification_base"], "image_id": image,
                   "dockerfile_sha256": hashlib.sha256((staging / "ci/Dockerfile.verify").read_bytes()).hexdigest(),
                   "command": f"python3 scripts/verify-linux.py --arch {args.arch} --output RECEIPTS",
                   "container_command": "python3 -B scripts/verify_repository.py",
                   "result": "success", "scope": "repository-policy", "product_runtime": "not-run",
                   "desktop": "not-run", "elapsed_seconds": round(time.time()-started, 2),
                   "log": log_name, "log_sha256": hashlib.sha256(log.encode()).hexdigest(),
                   "packages": packages_name, "packages_sha256": hashlib.sha256(packages.encode()).hexdigest()}
        (args.output / f"receipt-{args.arch}.json").write_text(json.dumps(receipt, indent=2)+"\n")


if __name__ == "__main__":
    main()
