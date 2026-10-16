#!/usr/bin/env python3
"""Add signed malicious-shape fixtures using the existing DISPOSABLE key only.
No fixture is installed by this script; the root verifier must reject every one.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture', type=Path, required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--only-expansion', action='store_true', help='add only the bounded 256KiB expansion negative to an existing fixture')
    mode.add_argument('--only-metadata', action='store_true', help='add only wrong-owner and writable-helper negatives to an existing fixture')
    args = p.parse_args()
    assert sys.platform == 'linux' and os.getuid() != 0
    out = args.fixture.absolute()
    assert out.is_dir() and not out.is_symlink()
    receipt = json.loads((out / 'artifacts.json').read_text())
    labels = (('oversized-expanded-payload',) if args.only_expansion else
              ('wrong-owner', 'writable-helper') if args.only_metadata else
              ('maintainer-script', 'symlink-payload', 'arbitrary-path', 'setuid-helper',
               'oversized-expanded-payload', 'wrong-owner', 'writable-helper'))
    for label in labels:
        root = out / label
        shutil.copytree(out / 'v2', root)
        helper = root / 'usr/lib/campus-982-disposable-spike/helper'
        if label == 'maintainer-script':
            script = root / 'DEBIAN/postinst'
            script.write_text('#!/bin/sh\nexit 0\n')
            script.chmod(0o755)
        elif label == 'symlink-payload':
            helper.unlink()
            helper.symlink_to('/etc/hostname')
        elif label == 'arbitrary-path':
            (root / 'usr/lib/campus-982-unrelated-fixture').write_text('forbidden extra file')
        elif label == 'setuid-helper':
            helper.chmod(0o4755)
        elif label == 'writable-helper':
            helper.chmod(0o777)
        elif label == 'oversized-expanded-payload':
            # Compresses to a tiny deb; verifier must stop before buffering this tar.
            helper.write_bytes(b'X' * (256 * 1024))
        package = out / (label + '.deb')
        # Wrong-owner deliberately retains this unprivileged builder's UID/GID in
        # the archive; every normal fixture has root-owned archive metadata.
        owner_args = [] if label == 'wrong-owner' else ['--root-owner-group']
        subprocess.run(['/usr/bin/dpkg-deb', *owner_args, '--build', str(root), str(package)], check=True)
        subprocess.run(['/usr/bin/openssl', 'pkeyutl', '-sign', '-inkey', str(out / 'private.pem'), '-rawin', '-in', str(package), '-out', str(package) + '.sig'], check=True)
        receipt['packages'][label] = {'sha256': hashlib.sha256(package.read_bytes()).hexdigest(), 'purpose': 'signed archive-shape rejection; must never install'}
        signing = out / 'tauri-minisign'
        if signing.is_dir():
            # Resume an existing test-only minisign fixture without replacing its key.
            sig = signing / (label + '.minisig')
            subprocess.run(['/usr/bin/minisign', '-S', '-s', str(signing / 'synthetic.key'),
                            '-m', str(package), '-x', str(sig), '-t',
                            'timestamp:0\tfile:' + package.name + '\tversion:0.982.2'], check=True)
            (signing / (label + '.signature.b64')).write_text(base64.b64encode(sig.read_bytes()).decode())
            manifest = signing / 'signature-artifacts.json'
            signed = json.loads(manifest.read_text())
            signed['signatures'][label] = {'package_sha256': receipt['packages'][label]['sha256'],
                                          'minisig_sha256': hashlib.sha256(sig.read_bytes()).hexdigest(),
                                          'version':'0.982.2'}
            manifest.write_text(json.dumps(signed, indent=2) + '\n')
    (out / 'artifacts.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: receipt['packages'][key] for key in labels}, indent=2))


if __name__ == '__main__':
    main()
