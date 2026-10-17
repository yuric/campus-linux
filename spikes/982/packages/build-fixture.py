#!/usr/bin/env python3
"""Create signed disposable deb fixtures and optionally a real arm64 AppImage.
Requires existing dpkg-deb/openssl/mksquashfs; never downloads/installs tooling.
No provider account, network execution, product key or product artifact is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

RUNTIME_SHA256 = 'b4ff0030242d0c3bb12ce40541828303cf167493f4793456f0436edd6255c39d'
HELPER = '''#!/usr/bin/python3 -I
import fcntl, json, os, pathlib, signal, sys, time
root = pathlib.Path(sys.argv[1])
lock = (root / "singleton.lock").open("a")
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(73)
(root / "running.json").write_text(json.dumps({"pid": os.getpid(), "version": "VERSION", "image": os.path.realpath(__file__)}))
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
while True:
    time.sleep(0.1)
'''


def command(*args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        print(result.stdout.decode(errors='replace'), file=sys.stderr)
        result.check_returncode()
    return result.stdout.decode().strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runtime', type=Path)
    args = p.parse_args()
    assert sys.platform == 'linux' and os.getuid() != 0
    os.umask(0o077)
    out = args.output.absolute()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    arch = command('/usr/bin/dpkg', '--print-architecture')
    command('/usr/bin/openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(out / 'private.pem'))
    command('/usr/bin/openssl', 'pkey', '-in', str(out / 'private.pem'), '-pubout', '-out', str(out / 'public.pem'))
    receipts = {'scope': 'DISPOSABLE #982 fixtures; not Tauri build/product/release acceptance', 'arch': arch, 'packages': {}}
    for label, version, name, package_arch in (
        ('v1', '0.982.1', 'campus-982-disposable-spike', arch),
        ('v2', '0.982.2', 'campus-982-disposable-spike', arch),
        ('wrong-name', '0.982.2', 'campus-982-wrong-name', arch),
        ('wrong-arch', '0.982.2', 'campus-982-disposable-spike', 'amd64' if arch == 'arm64' else 'arm64'),
    ):
        root = out / label
        (root / 'DEBIAN').mkdir(parents=True)
        (root / 'DEBIAN').chmod(0o755)
        (root / 'DEBIAN/control').write_text(f'Package: {name}\nVersion: {version}\nArchitecture: {package_arch}\nMaintainer: Disposable Campus Test <fixture@example.invalid>\nDescription: Disposable mechanism probe only; no product or provider code\n')
        helper = root / 'usr/lib/campus-982-disposable-spike/helper'
        helper.parent.mkdir(parents=True)
        helper.write_text(HELPER.replace('VERSION', version))
        helper.chmod(0o755)
        (root / 'DEBIAN/control').chmod(0o644)
        for directory, _, _ in os.walk(root):
            Path(directory).chmod(0o755)
        package = out / (label + '.deb')
        command('/usr/bin/dpkg-deb', '--root-owner-group', '--build', str(root), str(package))
        command('/usr/bin/openssl', 'pkeyutl', '-sign', '-inkey', str(out / 'private.pem'), '-rawin', '-in', str(package), '-out', str(package) + '.sig')
        receipts['packages'][label] = {'sha256': digest(package), 'version': version, 'name': name, 'arch': package_arch, 'helper_sha256': digest(helper)}
    if args.runtime:
        assert arch == 'arm64' and digest(args.runtime) == RUNTIME_SHA256
        appdir = out / 'AppDir'
        appdir.mkdir()
        for filename, content in (
            ('AppRun', '#!/bin/sh\nexec "$(dirname "$0")/helper" "$@"\n'),
            ('helper', HELPER.replace('VERSION', '0.982.1')),
        ):
            path = appdir / filename
            path.write_text(content)
            path.chmod(0o755)
        appdir.chmod(0o755)
        squash = out / 'fixture.squashfs'
        command('/usr/bin/mksquashfs', str(appdir), str(squash), '-noappend', '-all-root', '-no-xattrs', '-comp', 'gzip')
        appimage = out / 'campus-982-disposable.AppImage'
        appimage.write_bytes(args.runtime.read_bytes() + squash.read_bytes())
        appimage.chmod(0o755)
        receipts['appimage'] = {'sha256': digest(appimage), 'runtime_sha256': RUNTIME_SHA256, 'runtime_commit': '8f39b89e2ac31e1640b3d3f7e9a5108e6ce805fa', 'runtime_asset_id': 596077442, 'webview': 'NONE: lifecycle mechanism fixture only', 'signature': 'UNSIGNED disposable fixture; not updater trust evidence'}
    else:
        receipts['appimage'] = {'status': 'NOT BUILT: no pinned runtime supplied'}
    (out / 'artifacts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(json.dumps(receipts, indent=2))


if __name__ == '__main__':
    main()
