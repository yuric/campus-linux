#!/usr/bin/env python3
"""Bounded independent desktop fixture packages. No release signature/product code."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

RUNTIME_SHA256 = 'b4ff0030242d0c3bb12ce40541828303cf167493f4793456f0436edd6255c39d'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    args = p.parse_args()
    assert sys.platform == 'linux' and os.getuid() != 0
    assert digest(args.runtime) == RUNTIME_SHA256
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    arch = subprocess.check_output(['/usr/bin/dpkg', '--print-architecture'], text=True).strip()
    assert arch == 'arm64'
    root = args.output / 'deb-root'
    (root / 'DEBIAN').mkdir(parents=True)
    (root / 'DEBIAN/control').write_text(f'Package: campus-982-links-disposable\nVersion: 0.982.1\nArchitecture: {arch}\nDepends: python3, python3-gi, gir1.2-gtk-3.0\nMaintainer: Disposable Campus Test <fixture@example.invalid>\nDescription: Temporary URI activation probe without API or listener\n')
    handler = root / 'usr/lib/campus-982-links-disposable/handler.py'
    handler.parent.mkdir(parents=True)
    shutil.copyfile(Path(__file__).with_name('handler.py'), handler)
    handler.chmod(0o755)
    for directory, _, files in os.walk(root):
        Path(directory).chmod(0o755)
    (root / 'DEBIAN/control').chmod(0o644)
    deb = args.output / 'campus-982-links-disposable.deb'
    subprocess.run(['/usr/bin/dpkg-deb', '--root-owner-group', '--build', str(root), str(deb)], check=True)
    appdir = args.output / 'AppDir'
    appdir.mkdir(mode=0o755)
    shutil.copyfile(handler, appdir / 'handler.py')
    (appdir / 'handler.py').chmod(0o755)
    (appdir / 'AppRun').write_text('#!/bin/sh\nexec /usr/bin/python3 -I "$(dirname "$0")/handler.py" "$@"\n')
    (appdir / 'AppRun').chmod(0o755)
    squash = args.output / 'links.squashfs'
    subprocess.run(['/usr/bin/mksquashfs', str(appdir), str(squash), '-noappend', '-all-root', '-no-xattrs', '-comp', 'gzip'], check=True)
    appimage = args.output / 'campus-982-links-disposable.AppImage'
    appimage.write_bytes(args.runtime.read_bytes() + squash.read_bytes())
    appimage.chmod(0o755)
    report = {'scope': 'UNSIGNED disposable URI activation fixtures; GTK/Python host runtime, not Tauri product', 'arch': arch, 'deb_sha256': digest(deb), 'appimage_sha256': digest(appimage), 'runtime_sha256': RUNTIME_SHA256, 'handler_sha256': digest(handler)}
    (args.output / 'artifacts.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
