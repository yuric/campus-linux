#!/usr/bin/env python3
"""Disposable Linux OS mechanism tests, not a product executor or authority policy.

Run as an unprivileged guest user. Only TemporaryDirectory roots are modified.
All credentials below are synthetic. No network or provider invocation occurs.
"""
import base64
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

results = []
def record(name, ok, **observed):
    results.append(dict(case=name, result='pass' if ok else 'fail', observed=observed))

def scope(value):
    raw = value.encode('utf-8')
    if not raw or len(raw) > 160 or b'\0' in raw:
        raise ValueError('invalid opaque scope')
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')

class How(ctypes.Structure):
    _fields_ = [('flags', ctypes.c_uint64), ('mode', ctypes.c_uint64), ('resolve', ctypes.c_uint64)]

libc = ctypes.CDLL(None, use_errno=True)
def beneath(fd, path, flags=os.O_RDONLY, mode=0):
    if platform.machine() not in ('aarch64', 'x86_64'):
        raise RuntimeError('unverified syscall architecture')
    how = How(flags | os.O_CLOEXEC, mode, 0x08 | 0x04)  # BENEATH | NO_SYMLINKS, deliberately not NO_XDEV
    result = libc.syscall(437, fd, os.fsencode(path), ctypes.byref(how), ctypes.sizeof(how))
    if result < 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))
    return result

def peer(sock):
    return struct.unpack('3i', sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))

def main():
    if sys.platform != 'linux' or os.getuid() == 0:
        raise SystemExit('Run on disposable Linux as an unprivileged user')
    vectors = [('a','YQ'), ('ab','YWI'), ('abc','YWJj'), ('é','w6k'), ('日本語','5pel5pys6Kqe'), ('../','Li4v')]
    for value, expected in vectors:
        actual = scope(value)
        record('scope-vector', actual == expected, input_utf8_hex=value.encode().hex(), expected=expected, actual=actual)
    for value in ['', '\0', 'a\0b', 'a'*161, 'é'*81]:
        try: scope(value); rejected = False
        except ValueError: rejected = True
        record('scope-reject', rejected, bytes=len(value.encode()), nul='\0' in value)
    record('scope-160-byte-boundary', len(scope('é'*80)) == 214)
    with tempfile.TemporaryDirectory(prefix='campus-982-security-') as tmp:
        root = Path(tmp)
        private = root/'trusted'
        private.mkdir(mode=0o700)
        outside = root/'user-repository'
        outside.mkdir()
        marker = outside/'KEEP'
        marker.write_bytes(b'user-data-never-delete')
        before = hashlib.sha256(marker.read_bytes()).hexdigest()
        rootfd = os.open(private, os.O_RDONLY | os.O_DIRECTORY)
        (private/'scope').mkdir(mode=0o700)
        for path, target in [('escape', outside), ('scope/link', outside)]: (private/path).symlink_to(target)
        for path in ['escape/KEEP', 'scope/link/KEEP', '../user-repository/KEEP', str(marker)]:
            try:
                fd = beneath(rootfd, path); os.close(fd); rejected = False
            except OSError as e: rejected = e.errno in (errno.EXDEV, errno.ELOOP)
            record('openat2-escape-rejected', rejected, path_kind=path if not path.startswith('/') else 'absolute')
        held = beneath(rootfd, 'scope', os.O_RDONLY | os.O_DIRECTORY)
        os.rename(private/'scope', private/'renamed')
        (private/'scope').symlink_to(outside)
        fd = beneath(held, 'probe', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, b'synthetic')
        os.close(fd)
        record('held-descriptor-rename', (private/'renamed/probe').exists() and not (outside/'probe').exists(), caveat='FD pins inode, not continued lexical ancestry; no claim of same-UID containment')
        os.close(held)
        (private/'race').mkdir()
        (private/'race/KEEP').write_bytes(b'inside')
        stop = threading.Event()
        errors = []
        def swap():
            try:
                while not stop.is_set():
                    os.rename(private/'race', private/'parking')
                    (private/'race').symlink_to(outside)
                    (private/'race').unlink()
                    os.rename(private/'parking', private/'race')
            except Exception as e: errors.append(type(e).__name__)
        worker = threading.Thread(target=swap)
        worker.start()
        opened = rejected = escaped = 0
        for _ in range(3000):
            try:
                fd = beneath(rootfd, 'race/KEEP')
                data = os.read(fd, 100); os.close(fd)
                opened += 1
                escaped += data != b'inside'
            except OSError as e:
                if e.errno not in (errno.ELOOP, errno.ENOENT, errno.EAGAIN, errno.EXDEV): raise
                rejected += 1
        stop.set(); worker.join()
        record('symlink-rename-race', not escaped and not errors and opened > 0, iterations=3000, opened=opened, rejected=rejected, escaped=escaped, thread_errors=errors)
        os.close(rootfd)
        with tempfile.TemporaryDirectory(prefix='campus-982-repository-', dir='/dev/shm') as cross:
            crossfd = os.open(cross, os.O_RDONLY | os.O_DIRECTORY)
            fd = beneath(crossfd, 'KEEP', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, b'user-controlled-repository'); os.close(fd)
            record('separate-filesystem-repository', os.stat(cross).st_dev != os.stat(private).st_dev, root_device=os.stat(private).st_dev, repository_device=os.stat(cross).st_dev, method='Independent authorized repository descriptor; no global NO_XDEV restriction')
            os.close(crossfd)
        # Authenticate kernel peer before the synthetic token is sent on either end.
        endpoint = str(private/'ipc.sock')
        listener = socket.socket(socket.AF_UNIX)
        listener.bind(endpoint); os.chmod(endpoint, 0o600); listener.listen(1)
        client = socket.socket(socket.AF_UNIX); client.connect(endpoint)
        server, _ = listener.accept()
        cp, sp = peer(client), peer(server)
        record('ipc-mutual-peer', cp[1] == sp[1] == os.getuid() and cp[0] == sp[0] == os.getpid(), client_peer=cp, server_peer=sp)
        # This predicate establishes principal separation only after peer and token checks.
        allowed = {'ui': {'navigate'}, 'executor': {'claim'}, 'attempt-1': {'event-1'}}
        def authorize(uid, token, principal, action):
            return uid == os.getuid() and token == b'synthetic-ipc-only' and action in allowed.get(principal, set())
        record('ipc-wrong-principal', not authorize(os.getuid(), b'synthetic-ipc-only', 'ui', 'claim'))
        record('ipc-wrong-token', not authorize(os.getuid(), b'wrong', 'executor', 'claim'))
        record('ipc-other-uid-predicate', not authorize(os.getuid()+1, b'synthetic-ipc-only', 'executor', 'claim'), limitation='Actual different-UID connect requires separate privileged test')
        record('ipc-cross-attempt', not authorize(os.getuid(), b'synthetic-ipc-only', 'attempt-1', 'event-2'))
        server.close(); client.close(); listener.close()
        stale = socket.socket(socket.AF_UNIX)
        try: stale.connect(endpoint); failed = False
        except ConnectionRefusedError: failed = True
        finally: stale.close()
        record('ipc-stale-endpoint', failed)
        # Peer UID cannot distinguish malicious software under the same UID.
        record('ipc-same-uid-limit-observed', cp[1] == os.getuid(), limitation='Token readable to same UID; no application identity or sandbox claim')
        fd = os.open(private/'ambient-fd', os.O_CREAT | os.O_RDWR, 0o600)
        os.set_inheritable(fd, True)
        env = {'PATH':'/usr/bin:/bin', 'HOME':str(private), 'LANG':'C.UTF-8', 'CAMPUS_API_TOKEN':'synthetic-attempt-runtime', 'CAMPUS_MCP_TOKEN':'synthetic-attempt-mcp'}
        code = 'import os,json; print(json.dumps({"keys":sorted(os.environ),"fds":[int(x) for x in os.listdir("/proc/self/fd") if int(x)>2 and os.path.exists("/proc/self/fd/"+x)]}))'
        child = json.loads(subprocess.check_output(['/usr/bin/python3','-c',code], env=env, close_fds=True))
        record('child-environment-and-fds', set(child['keys']) <= set(env) | {'LC_CTYPE'} and not child['fds'], inherited_keys=child['keys'], inherited_fds=child['fds'], no_values_logged=True)
        os.close(fd)
        record('user-data-preserved', marker.read_bytes() == b'user-data-never-delete', before_sha256=before, after_sha256=hashlib.sha256(marker.read_bytes()).hexdigest())
    return {'schema':1,'scope':'OS spike only; no product/contract acceptance','platform':platform.platform(),'architecture':platform.machine(),'uid':os.getuid(),'cases':results,'remaining':['real separate-UID IPC and socket owner/starttime authentication','real token authority/expiry/revoke requires merged Rails contracts','same-UID malicious processes are outside containment guarantee','credential-root rename outside ancestry must fence future CLI launches']}

if __name__ == '__main__':
    data = main()
    print(json.dumps(data, indent=2))
    raise SystemExit(any(r['result'] != 'pass' for r in results))
