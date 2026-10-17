#!/usr/bin/env python3
"""Verify public Claude release metadata in a disposable keyring; creates no key."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import urllib.request

FINGERPRINT = '31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE'
SOURCES = [
    ('claude-key.asc', 'https://downloads.claude.ai/keys/claude-code.asc',
     'bd70a5e4a268002704024ceba7f8446024114e94f3f0bdd11c23a9e592be81c6'),
    ('manifest.json', 'https://downloads.claude.ai/claude-code-releases/2.1.301/manifest.json',
     '8517444f8515ccb572272d6dd666999aa7115fd14ae4207631edaa25d4dfce40'),
    ('manifest.json.sig', 'https://downloads.claude.ai/claude-code-releases/2.1.301/manifest.json.sig',
     'd98450e26c5b134e869d6b0aefc1db3418085bffbb85f3736ef4b30c88dc6d5f'),
]

with tempfile.TemporaryDirectory(prefix='c982-gpg-', dir='/tmp') as temp:
    root = Path(temp)
    sources = []
    for name, url, digest in SOURCES:
        data = urllib.request.urlopen(url, timeout=30).read(1024 * 1024)
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit('pinned public verification metadata changed')
        (root / name).write_bytes(data)
        sources.append({'file': name, 'url': url, 'sha256': digest, 'bytes': len(data)})
    gpg = ['gpg', '--homedir', temp, '--batch', '--no-options', '--no-auto-key-retrieve']
    shown = subprocess.run(gpg + ['--with-colons', '--import-options', 'show-only', '--import',
                           str(root / 'claude-key.asc')], capture_output=True, text=True, check=True)
    fingerprints = [line.split(':')[9] for line in shown.stdout.splitlines() if line.startswith('fpr:')]
    if fingerprints != [FINGERPRINT]:
        raise SystemExit('unexpected vendor public key identity')
    subprocess.run(gpg + ['--import', str(root / 'claude-key.asc')], capture_output=True, check=True)
    verified = subprocess.run(gpg + ['--status-fd', '1', '--verify', str(root / 'manifest.json.sig'),
                                    str(root / 'manifest.json')], capture_output=True, text=True, check=True)
    if '[GNUPG:] VALIDSIG ' + FINGERPRINT + ' ' not in verified.stdout:
        raise SystemExit('signature did not validate expected public key')
    manifest = json.loads((root / 'manifest.json').read_text())
    print(json.dumps({'command': 'python3 spikes/982/providers/verify_claude_signature.py',
        'public_key_fingerprints': fingerprints, 'returncode': verified.returncode,
        'stdout': verified.stdout, 'stderr': verified.stderr, 'sources': sources,
        'manifest_version': manifest['version'], 'expected_arm64_binary_sha256':
        manifest['platforms']['linux-arm64']['checksum'],
        'scope': 'Public vendor-key verification only; no private/release key generated; not a Linux runtime receipt'}, indent=2))
