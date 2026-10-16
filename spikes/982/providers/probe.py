#!/usr/bin/env python3
"""Disposable provider binary observation. Never a production provider registry."""
import argparse
import base64
import ctypes
import ctypes.util
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import tarfile
import tempfile
import time
import urllib.request

PINS = Path(__file__).with_name('pins.json')
LIMIT = 512 * 1024 * 1024
SYNTHETIC = 'campus982-synthetic-not-a-valid-provider-key'


def download(root):
    root.mkdir(mode=0o700, parents=False, exist_ok=True)
    if root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise ValueError('download root must be owned by current user and mode 0700')
    for item in json.loads(PINS.read_text())['artifacts']:
        directory = root / item['engine']
        if directory.is_symlink():
            raise ValueError('refuse symlink download directory')
        directory.mkdir(mode=0o700, exist_ok=True)
        previous = directory / 'artifact.json'
        executable = directory / item['engine']
        if previous.exists():
            old = json.loads(previous.read_text())
            if executable.is_symlink() or old.get('url') != item['url'] or old.get('integrity') != item.get('integrity'):
                raise ValueError('existing artifact does not match pin')
            actual = hashlib.sha256(executable.read_bytes()).hexdigest()
            if actual != old['binary_sha256'] or (item.get('signed_manifest_binary_sha256', actual) != actual):
                raise ValueError('existing verified binary changed')
            print(json.dumps({'resumed_verified': item['engine']}), flush=True)
            continue
        if list(directory.iterdir()):
            raise ValueError('partial directory contains unreceipted data; preserve and inspect')
        with urllib.request.urlopen(item['url'], timeout=60) as response:
            data = response.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('artifact exceeds bounded download size')
        digest = hashlib.sha512(data).digest()
        expected = (base64.b64decode(item['integrity'].removeprefix('sha512-'), validate=True)
                    if 'integrity' in item else bytes.fromhex(item['sha512']))
        if digest != expected:
            raise ValueError('pinned artifact digest mismatch')
        # Extract exactly one regular executable; never unpack vendor paths/symlinks.
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            members = [m for m in archive.getmembers()
                       if Path(m.name).name == item['member_basename'] and m.isfile()]
            if len(members) != 1 or members[0].size > LIMIT:
                raise ValueError('ambiguous or oversized binary member')
            binary = archive.extractfile(members[0]).read(LIMIT + 1)
        if item['kind'] == 'tar-brotli':
            library = ctypes.util.find_library('brotlidec')
            if not library:
                raise ValueError('system libbrotlidec unavailable; preserve pin and mark blocked')
            decoder = ctypes.CDLL(library)
            decoder.BrotliDecoderDecompress.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p]
            decoder.BrotliDecoderDecompress.restype = ctypes.c_int
            capacity = ctypes.c_size_t(LIMIT)
            buffer = ctypes.create_string_buffer(LIMIT)
            compressed = ctypes.create_string_buffer(binary)
            if decoder.BrotliDecoderDecompress(len(binary), compressed, ctypes.byref(capacity), buffer) != 1:
                raise ValueError('bounded Brotli decompression failed')
            binary = ctypes.string_at(buffer, capacity.value)
            del buffer, compressed
        if 'signed_manifest_binary_sha256' in item and hashlib.sha256(binary).hexdigest() != item['signed_manifest_binary_sha256']:
            raise ValueError('binary differs from signed vendor manifest')
        target = directory / item['engine']
        target.write_bytes(binary)
        target.chmod(0o700)
        receipt = dict(item, artifact_sha256=hashlib.sha256(data).hexdigest(),
                       binary_sha256=hashlib.sha256(binary).hexdigest(),
                       member=members[0].name, binary_size=len(binary))
        (directory / 'artifact.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'downloaded': item['engine'], 'bytes': len(data)}), flush=True)


def bound_output():
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run(root):
    if platform.system() != 'Linux' or platform.machine() not in ('aarch64', 'arm64'):
        raise SystemExit('execution requires the disposable Linux arm64 guest')
    if os.getuid() == 0:
        raise SystemExit('execute as an unprivileged disposable guest user')
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64':
        raise SystemExit('execute only in the named owned disposable guest')
    interfaces = [line.split(':')[0].strip() for line in Path('/proc/net/dev').read_text().splitlines() if ':' in line]
    if interfaces != ['lo']:
        raise SystemExit('execution requires a fresh unshare --net namespace (loopback only)')
    captures = root / 'captures'
    captures.mkdir(mode=0o700, exist_ok=False)
    records = []
    for item in json.loads(PINS.read_text())['artifacts']:
        engine = item['engine']
        binary = root / engine / engine
        receipt = json.loads((root / engine / 'artifact.json').read_text())
        if hashlib.sha256(binary.read_bytes()).hexdigest() != receipt['binary_sha256']:
            raise ValueError('downloaded binary changed before execution')
        home = captures / engine
        home.mkdir(mode=0o700)
        scope = home / 'scope'
        scope.mkdir(mode=0o700)
        environment = {'HOME': str(home), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
                       'TMPDIR': str(home), 'XDG_CONFIG_HOME': str(home / 'config'),
                       'XDG_CACHE_HOME': str(home / 'cache'), 'XDG_DATA_HOME': str(home / 'data'),
                       'DISABLE_AUTOUPDATER': '1', 'DISABLE_UPDATES': '1', 'CI': '1',
                       'TERM': 'dumb'}
        # These are pinned reference adapter inputs, not availability decisions.
        variable = {'claude': 'CLAUDE_CONFIG_DIR', 'codex': 'CODEX_HOME',
                    'grok': 'GROK_HOME'}.get(engine)
        if variable:
            environment[variable] = str(scope)
        commands = [(['--version'], None), (['--help'], None)]
        if engine == 'claude':
            commands += [(['auth', 'status'], None), (['update', '--help'], None)]
        elif engine == 'codex':
            (scope / 'config.toml').write_text('cli_auth_credentials_store = "file"\n')
            commands += [(['login', '--help'], None), (['login', '--with-api-key'], SYNTHETIC + '\n'),
                         (['login', 'status'], None), (['logout'], None), (['update', '--help'], None)]
        elif engine == 'grok':
            commands += [(['login', '--help'], None), (['update', '--help'], None)]
        elif engine == 'agy':
            commands += [(['update', '--help'], None)]
        for number, (args, stdin) in enumerate(commands):
            start = time.monotonic()
            log = home / ('command-%02d.txt' % number)
            # Bounded timeout and capture. No inherited environment, FDs, bus or auth.
            with tempfile.TemporaryFile() as output:
                child = subprocess.Popen([str(binary)] + args, cwd=home, env=environment,
                                         stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT,
                                         close_fds=True, start_new_session=True, preexec_fn=bound_output)
                timed_out = False
                try:
                    child.communicate(input=stdin.encode() if stdin else b'', timeout=15)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                output.seek(0)
                raw = output.read(65537)
            text = raw[:65536].decode('utf-8', errors='replace').replace(SYNTHETIC, '[SYNTHETIC REDACTED]')
            log.write_text(text)
            log.chmod(0o600)
            records.append({'engine': engine, 'argv': args, 'returncode': child.returncode,
                            'timeout': timed_out, 'seconds': round(time.monotonic() - start, 3),
                            'capture': str(log.relative_to(root)), 'truncated': len(raw) > 65536,
                            'interpretation': 'raw observation only; no domain-success inference'})
        (home / 'filesystem.json').write_text(json.dumps([
            {'path': str(p.relative_to(home)), 'mode': oct(p.lstat().st_mode & 0o777),
             'bytes': p.lstat().st_size, 'symlink': p.is_symlink()}
            for p in sorted(home.rglob('*'))], indent=2) + '\n')
    result = {'uname': platform.uname()._asdict(), 'uid': os.getuid(), 'network_interfaces': interfaces,
              'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'observation_complete': True,
              'bounded_capture_checks_passed': all(not row['timeout'] and not row['truncated'] for row in records),
              'provider_authentication_or_update_success': 'not inferred from these command return codes',
              'records': records, 'unproven': ['real OAuth login/refresh/cancel/account isolation',
              'vendor update and previous-version recovery', 'active-run concurrency',
              'Gemini runtime', 'provider identity authenticity beyond recorded integrity']}
    (captures / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'receipt': str(captures / 'receipt.json')}))
    return 0 if result['bounded_capture_checks_passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['download', 'offline'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if not args.directory.is_absolute() or args.directory.is_symlink():
        parser.error('use an absolute non-symlink disposable directory')
    os.umask(0o077)
    raise SystemExit((download if args.operation == 'download' else run)(args.directory))
