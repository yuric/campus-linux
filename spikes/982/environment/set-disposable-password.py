#!/usr/bin/env python3
"""Set only this run's disposable guest account without credentials in argv/logs."""
from pathlib import Path
import os
import stat
import subprocess

private = Path(__file__).resolve().parent / "private" / "campusqa.password"
fd = os.open(private, os.O_RDONLY | os.O_NOFOLLOW)
metadata = os.fstat(fd)
if metadata.st_uid != os.getuid() or metadata.st_mode & 0o077 or not stat.S_ISREG(metadata.st_mode):
    os.close(fd)
    raise SystemExit("Refusing credential file without private regular owner-controlled bytes")
with os.fdopen(fd) as stream:
    password = stream.read(4097).strip()
if len(password) > 4096:
    raise SystemExit("Credential file exceeds disposable input bound")
if not password or "\n" in password or ":" in password:
    raise SystemExit("Invalid private credential encoding")
result = subprocess.run(
    ["/opt/homebrew/bin/limactl", "shell", "campus-linux-d5-noble-arm64", "sudo", "chpasswd"],
    input=("campusqa:" + password + "\n").encode(),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
)
if result.returncode:
    raise SystemExit("Guest password setup failed; inspect status without logging input")
print("Disposable campusqa password set over private stdin; value omitted.")
