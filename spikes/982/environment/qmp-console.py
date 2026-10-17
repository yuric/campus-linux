#!/usr/bin/env python3
"""Owned Lima console only. Password bytes stay in memory and QMP's local socket.

Use capture and inspect the actual password field before password input. Never
capture while entering secrets. QMP docs: https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html
"""
import argparse
import json
import os
from pathlib import Path
import socket
import time

p = argparse.ArgumentParser()
p.add_argument('action', choices=['capture', 'key', 'password'])
p.add_argument('value', help='capture path, qcode, or mode-0600 password-file path')
p.add_argument('--no-enter', action='store_true', help='Do not submit after typing a password; use for a confirmed first field')
a = p.parse_args()
sock = socket.socket(socket.AF_UNIX)
sock.settimeout(10)
sock.connect(str(Path.home() / '.lima/campus-linux-d5-noble-arm64/qmp.sock'))
stream = sock.makefile('rwb', buffering=0)
json.loads(stream.readline())

def command(name, args=None):
    stream.write((json.dumps({'execute': name, 'arguments': args or {}}) + '\n').encode())
    while True:
        response = json.loads(stream.readline())
        if 'error' in response:
            raise SystemExit('QMP operation failed (input omitted)')
        if 'return' in response:
            return response['return']

def key(codes):
    command('send-key', {'keys': [{'type': 'qcode', 'data': c} for c in codes], 'hold-time': 40})
    time.sleep(.09)

command('qmp_capabilities')
if a.action == 'capture':
    command('screendump', {'filename': str(Path(a.value).resolve()), 'format': 'png'})
elif a.action == 'key':
    key(a.value.split('+'))
else:
    fd = os.open(a.value, os.O_RDONLY | os.O_NOFOLLOW)
    st = os.fstat(fd)
    if st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise SystemExit('Unsafe credential file permissions')
    with os.fdopen(fd) as f:
        password = f.read().rstrip('\n')
    normal = dict(zip('0123456789-=[];\',./`\\', ['0','1','2','3','4','5','6','7','8','9','minus','equal','bracket_left','bracket_right','semicolon','apostrophe','comma','dot','slash','grave_accent','backslash']))
    shifted = dict(zip('!@#$%^&*()_+{}:"<>?~|', ['1','2','3','4','5','6','7','8','9','0','minus','equal','bracket_left','bracket_right','semicolon','apostrophe','comma','dot','slash','grave_accent','backslash']))
    events = []
    for c in password:
        if c.isascii() and c.isalpha(): events.append((['shift'] if c.isupper() else []) + [c.lower()])
        elif c in normal: events.append([normal[c]])
        elif c in shifted: events.append(['shift', shifted[c]])
        else: raise SystemExit('Unsupported password keyboard encoding; nothing sent')
    for event in events: key(event)
    if not a.no_enter:
        key(['ret'])
    password = None
    print('Disposable secret entered over local QMP; value omitted.')
