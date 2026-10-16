#!/usr/bin/env python3
"""Disposable Lima setup recovery over its local serial console, never updater code.

Prompts are checked before private credential entry. Never prints console login
traffic or secret input. Public command output starts only after successful sudo.
"""
import argparse
import os
from pathlib import Path
import socket
import time

p = argparse.ArgumentParser()
p.add_argument('--password-file', required=True)
p.add_argument('--command', required=True, help='Public guest administration command only')
a = p.parse_args()
fd = os.open(a.password_file, os.O_RDONLY | os.O_NOFOLLOW)
st = os.fstat(fd)
if st.st_uid != os.getuid() or st.st_mode & 0o077: raise SystemExit('Unsafe private file')
with os.fdopen(fd, 'rb') as f: password = f.read().strip()
if not password or b'\n' in password: raise SystemExit('Invalid credential encoding')
s = socket.socket(socket.AF_UNIX)
s.settimeout(1)
s.connect(str(Path.home()/'.lima/campus-linux-d5-noble-arm64/serial.sock'))
def until(marker, timeout=20):
    buf = b''
    end = time.monotonic()+timeout
    while time.monotonic()<end:
        try: buf += s.recv(65536)
        except TimeoutError: continue
        if marker in buf: return buf
    raise SystemExit('Expected console prompt unavailable; input/output omitted')
s.sendall(b'\n')
until(b'login:')
s.sendall(b'campusqa\n')
until(b'Password:')
s.sendall(password+b'\n')
until(b'$ ')
# The TTY echoes this command before sudo switches echo off. Do not place the
# contiguous marker in that echo: only the actual sudo prompt may match it.
auth_marker = b'CAMPUS982_AUTH:'
auth_command = b"sudo -k; sudo -S -p 'CAMPUS982_''AUTH:' -v\n"
assert auth_marker not in auth_command
s.sendall(auth_command)
until(auth_marker)
s.sendall(password+b'\n')
until(b'$ ')
password = None
s.sendall(('sudo -n sh -c ' + __import__('shlex').quote(a.command) + "; printf '\\nCAMPUS982_DONE\\n'\n").encode())
out = until(b'\r\nCAMPUS982_DONE', timeout=45)
print(out.decode(errors='replace'))
s.sendall(b'sudo -k; exit\n')
