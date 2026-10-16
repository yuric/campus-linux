#!/usr/bin/env python3
"""Create separate test-only minisign key and Tauri base64-wrapped signatures.
The original OpenSSL fixtures/key are not modified. Never use any release key.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def call(argv):
    return subprocess.check_output(argv, stderr=subprocess.STDOUT).decode().strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture', type=Path, required=True)
    args = p.parse_args()
    assert sys.platform == 'linux' and os.getuid() != 0
    os.umask(0o077)
    root = args.fixture / 'tauri-minisign'
    root.mkdir(mode=0o700, exist_ok=False)
    for prefix in ('synthetic', 'wrong-key'):
        call(['/usr/bin/minisign', '-G', '-W', '-s', str(root / (prefix + '.key')), '-p', str(root / (prefix + '.pub'))])
    public = (root / 'synthetic.pub').read_bytes()
    (root / 'public-key.b64').write_text(base64.b64encode(public).decode())
    receipt = {'scope': 'DISPOSABLE synthetic minisign; no release key; Tauri full-text base64 wrapper', 'minisign_version': call(['/usr/bin/minisign', '-v']), 'public_key_sha256': hashlib.sha256(public).hexdigest(), 'signatures': {}}
    for package in sorted(args.fixture.glob('*.deb')):
        label = package.stem
        version = '0.982.1' if label == 'v1' else '0.982.2'
        sig = root / (label + '.minisig')
        call(['/usr/bin/minisign', '-S', '-s', str(root / 'synthetic.key'), '-m', str(package), '-x', str(sig), '-t', 'timestamp:0\tfile:' + package.name + '\tversion:' + version])
        (root / (label + '.signature.b64')).write_text(base64.b64encode(sig.read_bytes()).decode())
        receipt['signatures'][label] = {'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(), 'minisig_sha256': hashlib.sha256(sig.read_bytes()).hexdigest(), 'version': version}
    for label, key, comment in (
        ('unversioned', 'synthetic', 'timestamp:0\tfile:v2.deb'),
        ('wrong-key', 'wrong-key', 'timestamp:0\tfile:v2.deb\tversion:0.982.2'),
    ):
        sig = root / (label + '.minisig')
        call(['/usr/bin/minisign', '-S', '-s', str(root / (key + '.key')), '-m', str(args.fixture / 'v2.deb'), '-x', str(sig), '-t', comment])
        (root / (label + '.signature.b64')).write_text(base64.b64encode(sig.read_bytes()).decode())
    tampered = (root / 'v2.minisig').read_text().replace('version:0.982.2', 'version:0.982.1')
    (root / 'tampered-comment.signature.b64').write_text(base64.b64encode(tampered.encode()).decode())
    (root / 'signature-artifacts.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
