"""Hosted-only exact tool downloads. No release/private credentials are used."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import urllib.request

lock = json.loads(Path('/opt/fixture-toolchain/downloads.json').read_text())
arch = platform.machine()
selected = lock['architectures'][arch]
with tempfile.TemporaryDirectory(prefix='fixture-tools-') as directory:
    root = Path(directory)
    for name in ('rust', 'cli'):
        archive = root / (name + '.tar')
        urllib.request.urlretrieve(selected[name + '_url'], archive)
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == selected[name + '_sha256']
        subprocess.run(['tar', 'xf', str(archive), '-C', str(root)], check=True)
    subprocess.run([
        str(root / f'rust-1.99.1-{arch}-unknown-linux-gnu/install.sh'),
        '--prefix=/usr/local', '--disable-ldconfig',
        f'--components=rustc,cargo,rust-std-{arch}-unknown-linux-gnu,rustfmt-preview',
    ], check=True)
    cli = list(root.rglob('cargo-tauri'))
    assert len(cli) == 1
    subprocess.run(['install', '-m', '0755', str(cli[0]), '/usr/local/bin/cargo-tauri'], check=True)
subprocess.run(['rustc', '--version'], check=True)
subprocess.run(['cargo', 'tauri', '--version'], check=True)
