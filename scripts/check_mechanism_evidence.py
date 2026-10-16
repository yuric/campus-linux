#!/usr/bin/env python3
"""Check published mechanism inventories, without granting runtime acceptance."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (
    'docs/acceptance/mechanisms/receipts/artifact-index.json',
    'docs/acceptance/mechanisms/receipts/core-sentinel-followup-index.json',
    'docs/acceptance/mechanisms/receipts/apport-positive-preflight-index.json',
    'docs/acceptance/mechanisms/receipts/apport-activation-index.json',
    'docs/acceptance/mechanisms/receipts/repair-1200-index.json',
)


def verify(root=ROOT, manifests=MANIFESTS):
    root = Path(root)
    # In git archive verification containers there is deliberately no .git: the
    # independently admitted source archive already contains only committed files.
    tracked = None
    if (root / '.git').exists():
        tracked = set(subprocess.check_output(
            ['git', 'ls-files', '-z'], cwd=root).decode().split('\0'))
    count = 0
    for manifest in manifests:
        if tracked is not None and manifest not in tracked:
            raise ValueError(f'untracked evidence manifest: {manifest}')
        rows = json.loads((root / manifest).read_text())['files']
        if not isinstance(rows, list) or not rows:
            raise ValueError(f'empty evidence manifest: {manifest}')
        seen = set()
        for row in rows:
            relative = row['path']
            path = PurePosixPath(relative)
            if path.is_absolute() or '..' in path.parts or str(path) != relative or relative in seen:
                raise ValueError(f'invalid or duplicate evidence path: {relative}')
            seen.add(relative)
            if tracked is not None and relative not in tracked:
                raise ValueError(f'untracked indexed evidence: {relative}')
            target = root / relative
            component = root
            for part in path.parts:
                component = component / part
                if component.is_symlink():
                    raise ValueError(f'symlink evidence: {relative}')
            data = target.read_bytes()
            if type(row['bytes']) is not int or len(data) != row['bytes']:
                raise ValueError(f'evidence size mismatch: {relative}')
            if hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError(f'evidence digest mismatch: {relative}')
            count += 1
    print(f'PASS {count} indexed evidence entries; tracked membership checked: {tracked is not None}; no runtime acceptance')
    return count


if __name__ == '__main__':
    verify()
