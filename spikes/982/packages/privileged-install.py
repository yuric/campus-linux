#!/usr/bin/python3 -I
"""TEST ONLY. Root helper for a disposable guest; never install as a product service.
Input is a bounded JSON message on stdin, not a user-controlled path or command.
The trust anchor belongs to this disposable spike, not the Campus release key.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import select
import signal
import subprocess
import sys
import tempfile
import tarfile
import time

ROOT = Path('/var/lib/campus-982-spike')
MAX_BYTES = 4 * 1024 * 1024
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C', 'HOME': '/root'}


def run(argv, max_output=128 * 1024):
    # Bound output while reading, before decompression can accumulate in memory.
    # The private process group includes dpkg-deb's decompressor children.
    proc = subprocess.Popen(argv, env=ENV, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True)
    output = bytearray()
    deadline = time.monotonic() + 30
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([proc.stdout], [], [], remaining)[0]:
                raise subprocess.TimeoutExpired(argv, 30)
            chunk = os.read(proc.stdout.fileno(), min(65536, max_output + 1 - len(output)))
            if not chunk:
                break
            output.extend(chunk)
            if len(output) > max_output:
                raise ValueError('subprocess output exceeds disposable bound')
        code = proc.wait(timeout=max(0.001, deadline - time.monotonic()))
        if code:
            raise subprocess.CalledProcessError(code, argv)
        return bytes(output)
    except BaseException:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)
        raise
    finally:
        proc.stdout.close()


def verify_archive(payload, expected):
    """Accept only the exact harmless fixture schema, never arbitrary signed metadata."""
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive:
        for member in archive.getmembers():
            name = member.name.rstrip('/')
            if name not in expected or name in seen:
                raise ValueError('unexpected or duplicate fixture archive member')
            kind, mode = expected[name]
            correct_type = (member.type == tarfile.DIRTYPE if kind == 'directory' else
                            member.type in (tarfile.REGTYPE, tarfile.AREGTYPE) and member.name == name)
            if (not correct_type or member.mode != mode or member.uid != 0 or member.gid != 0
                    or member.size > 64 * 1024 or member.pax_headers
                    or (kind == 'directory' and member.size != 0)):
                raise ValueError('fixture archive type/owner/mode/metadata mismatch')
            seen.add(name)
    if seen != set(expected):
        raise ValueError('required fixture archive members missing')


def protected(path, directory=False):
    st = path.lstat()
    assert not stat.S_ISLNK(st.st_mode)
    assert st.st_uid == 0 and st.st_mode & 0o022 == 0
    assert stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode)


def main():
    assert os.getuid() == 0 and sys.platform == 'linux'
    assert len(sys.argv) == 1, 'no arguments accepted'
    protected(Path('/etc/campus-982-disposable-guest'))
    for parent in (Path('/var'), Path('/var/lib'), ROOT):
        protected(parent, directory=True)
    protected(ROOT / 'public.pem')
    raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    assert len(raw) <= MAX_BYTES, 'request exceeds bound'
    request = json.loads(raw)
    assert set(request) == {'package', 'signature'}
    data = base64.b64decode(request['package'], validate=True)
    sig = base64.b64decode(request['signature'], validate=True)
    assert len(data) <= 2 * 1024 * 1024 and len(sig) == 64
    os.umask(0o077)
    # Root owns every pathname component from this point to dpkg. No reopening a
    # user-owned download after verification; the caller only supplied byte data.
    with tempfile.TemporaryDirectory(prefix='stage-', dir=ROOT) as tmp:
        stage = Path(tmp)
        pkg = stage / 'package.deb'
        signature = stage / 'signature'
        for path, value in ((pkg, data), (signature, sig)):
            with path.open('xb') as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
            path.chmod(0o400)
        run(['/usr/bin/openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(ROOT / 'public.pem'), '-rawin', '-in', str(pkg), '-sigfile', str(signature)])
        name = run(['/usr/bin/dpkg-deb', '-f', str(pkg), 'Package']).decode().strip()
        arch = run(['/usr/bin/dpkg-deb', '-f', str(pkg), 'Architecture']).decode().strip()
        version = run(['/usr/bin/dpkg-deb', '-f', str(pkg), 'Version']).decode().strip()
        assert name == 'campus-982-disposable-spike'
        assert arch == run(['/usr/bin/dpkg', '--print-architecture']).decode().strip()
        assert version in ('0.982.1', '0.982.2')
        # The fixture is intentionally incapable of installing maintainer scripts,
        # diversions, links, arbitrary paths or privileged executables.
        for option, expected in (
            ('--ctrl-tarfile', {'.': ('directory', 0o755), './control': ('file', 0o644)}),
            ('--fsys-tarfile', {
                '.': ('directory', 0o755), './usr': ('directory', 0o755),
                './usr/lib': ('directory', 0o755),
                './usr/lib/campus-982-disposable-spike': ('directory', 0o755),
                './usr/lib/campus-982-disposable-spike/helper': ('file', 0o755),
            }),
        ):
            payload = run(['/usr/bin/dpkg-deb', option, str(pkg)])
            verify_archive(payload, expected)
        digest = hashlib.sha256(data).hexdigest()
        print(json.dumps({'phase': 'verified-root-owned-bytes', 'sha256': digest}), flush=True)
        # Deliberate deterministic race window, ONLY for this bounded test helper.
        time.sleep(1)
        assert hashlib.sha256(pkg.read_bytes()).hexdigest() == digest
        run(['/usr/bin/dpkg', '--install', str(pkg)])
        print(json.dumps({'phase': 'installed', 'sha256': digest, 'version': version}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Never reflect caller bytes, signature data, or potentially secret payloads.
        print(json.dumps({'phase': 'rejected', 'error_type': type(error).__name__}), flush=True)
        sys.exit(1)
