"""Hosted package identity, bounded-output inventory and dependency provenance."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

output = Path('/output')
packages = output / 'packages'
architecture = os.environ['FIXTURE_ARCH']
target_arch = {'arm64': 'aarch64', 'amd64': 'x86_64'}[architecture]

def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()

def run(args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs)

artifacts = []
for path in sorted(packages.iterdir()):
    if path.suffix not in ('.deb', '.AppImage'):
        continue
    version = re.search(r'([123]\.0\.0)', path.name).group(1)
    fmt = 'deb' if path.suffix == '.deb' else 'appimage'
    artifacts.append({'filename': path.name, 'version': version, 'format': fmt,
                      'architecture': architecture, 'target': f'linux-{target_arch}-{fmt}',
                      'bytes': path.stat().st_size, 'sha256': digest(path),
                      'signature': Path(str(path) + '.sig').read_text().strip()})
assert len(artifacts) == 6
assert sum(p['bytes'] for p in artifacts) <= 2 * 1024**3, 'Unexpected >2GiB output per architecture'
(output / 'receipts/package-index.json').write_text(json.dumps({
    'source_head': os.environ['EXACT_HEAD'], 'architecture': architecture,
    'total_package_bytes': sum(p['bytes'] for p in artifacts), 'artifacts': artifacts,
}, indent=2) + '\n')
inventory = []
for artifact in artifacts:
    package = packages / artifact['filename']
    with tempfile.TemporaryDirectory(prefix='fixture-inventory-') as directory:
        root = Path(directory)
        if artifact['format'] == 'deb':
            run(['dpkg-deb', '--extract', str(package), directory])
        else:
            # Inventory extraction is never used to execute or claim installed smoke.
            run([str(package), '--appimage-extract'], cwd=root, stderr=subprocess.DEVNULL)
            root = root / 'squashfs-root'
        files = []
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            row = {'path': str(path.relative_to(root)), 'bytes': path.stat().st_size, 'sha256': digest(path)}
            with path.open('rb') as stream:
                elf = stream.read(4) == b'\x7fELF'
            if elf:
                dynamic = run(['readelf', '-d', str(path)], stderr=subprocess.DEVNULL)
                symbols = run(['readelf', '--version-info', str(path)], stderr=subprocess.DEVNULL)
                glibc = sorted(set(re.findall(r'GLIBC_(\d+\.\d+(?:\.\d+)?)', symbols)),
                               key=lambda s: tuple(map(int, s.split('.'))))
                row['needed'] = re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)
                row['glibc_versions'] = glibc
                row['glibcxx_versions'] = sorted(set(re.findall(r'GLIBCXX_[\d.]+', symbols)))
                if glibc:
                    assert tuple(map(int, glibc[-1].split('.'))) <= (2, 35), (path, glibc[-1])
            files.append(row)
        inventory.append({'artifact': artifact['filename'], 'files': files})
(output / 'receipts/payload-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
metadata = json.loads(run(['cargo', 'metadata', '--locked', '--format-version', '1'], cwd='src-tauri'))
dependencies = [{'name': p['name'], 'version': p['version'], 'source': p['source'],
                 'license': p['license'], 'license_file': p['license_file']} for p in metadata['packages']]
(output / 'receipts/rust-dependencies.json').write_text(json.dumps(dependencies, indent=2) + '\n')
# Bundle helper/runtime inputs are measured here; #996 owns production pin custody.
helpers = []
cache = Path.home() / '.cache/tauri'
if cache.exists():
    for path in sorted(cache.rglob('*')):
        if path.is_file() and not path.is_symlink():
            helpers.append({'path': str(path.relative_to(cache)), 'bytes': path.stat().st_size, 'sha256': digest(path)})
(output / 'receipts/bundler-helper-inputs.json').write_text(json.dumps(helpers, indent=2) + '\n')
print(json.dumps({'architecture': architecture, 'package_bytes': sum(p['bytes'] for p in artifacts),
                  'receipt_bytes': sum(p.stat().st_size for p in (output / 'receipts').iterdir() if p.is_file())}))
