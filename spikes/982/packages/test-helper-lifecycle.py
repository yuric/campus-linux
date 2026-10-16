#!/usr/bin/env python3
"""Disposable local lifecycle model, NOT production leases/outbox/session behavior.
Extract actual fixture packages, retain helper outside outer package, and exercise
cross-process lock, claim fence, atomic promotion and interrupted pointer recovery.
Every fixture/state directory is beneath one newly created caller-owned directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, obj):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as stream:
        json.dump(obj, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    fsync_dir(path.parent)


def select(root, version):
    temp = root / 'next'
    temp.unlink(missing_ok=True)
    temp.symlink_to('versions/' + version)
    os.replace(temp, root / 'current')
    fsync_dir(root)


def promote(root, boundary):
    # Synthetic fence and compatibility state only. No server-authoritative decision.
    assert not (root / 'active-attempt').exists()
    manifest = json.loads((root / 'versions/0.982.2/manifest.json').read_text())
    assert manifest['synthetic_state_schema'] == 1
    assert sha(root / 'versions/0.982.2/helper') == manifest['helper_sha256']
    if boundary == 'after-stage':
        os._exit(91)
    atomic_json(root / 'fenced.json', {'claims': 'withheld', 'synthetic': True})
    if boundary == 'after-fence':
        os._exit(91)
    atomic_json(root / 'promotion.json', {'previous': '0.982.1', 'candidate': '0.982.2', 'accepted': False})
    if boundary == 'before-promote':
        os._exit(91)
    select(root, '0.982.2')
    if boundary == 'after-promote':
        os._exit(91)
    # No real lease reconciliation here. Caller must supply that in product tests.
    atomic_json(root / 'promotion.json', {'previous': '0.982.1', 'candidate': '0.982.2', 'accepted': True})
    if boundary == 'after-accept':
        os._exit(91)
    (root / 'fenced.json').unlink()
    fsync_dir(root)


def recover(root):
    journal = root / 'promotion.json'
    if journal.exists():
        record = json.loads(journal.read_text())
        select(root, record['candidate'] if record['accepted'] else record['previous'])
    # Keep fence until caller has reconciled ownership; recovery never grants claims.


def spawn(root):
    (root / 'running.json').unlink(missing_ok=True)
    proc = subprocess.Popen([str(root / 'current/helper'), str(root)], close_fds=True)
    for _ in range(100):
        if (root / 'running.json').exists():
            return proc, json.loads((root / 'running.json').read_text())
        if proc.poll() is not None:
            raise RuntimeError('helper terminated before identity')
        time.sleep(0.02)
    proc.kill()
    proc.wait()
    raise TimeoutError('helper identity absent')


def stop(proc):
    started = time.monotonic()
    proc.terminate()
    proc.wait(timeout=5)
    return time.monotonic() - started


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--child-root', type=Path)
    p.add_argument('--crash-at')
    args = p.parse_args()
    if args.child_root:
        promote(args.child_root, args.crash_at)
        return
    assert sys.platform == 'linux' and os.getuid() != 0
    os.umask(0o077)
    rows = []
    artifacts = json.loads((args.fixture / 'artifacts.json').read_text())
    with tempfile.TemporaryDirectory(prefix='campus-982-lifecycle-') as temp:
        base = Path(temp)
        sentinel = base / 'user-repository'
        sentinel.write_text('must-survive-uninstall')
        for format in ('deb', 'appimage'):
            if format == 'appimage' and 'sha256' not in artifacts['appimage']:
                rows.append({'format': format, 'result': 'BLOCKED', 'reason': 'fixture not built'})
                continue
            root = base / format
            root.mkdir(mode=0o700)
            extracted = base / ('extracted-' + format)
            extracted.mkdir()
            outer = base / ('outer.' + format)
            if format == 'deb':
                shutil.copyfile(args.fixture / 'v1.deb', outer)
                subprocess.run(['/usr/bin/dpkg-deb', '--extract', str(outer), str(extracted)], check=True, capture_output=True)
                source = extracted / 'usr/lib/campus-982-disposable-spike/helper'
            else:
                shutil.copyfile(args.fixture / 'campus-982-disposable.AppImage', outer)
                outer.chmod(0o755)
                result = subprocess.run([str(outer), '--appimage-extract'], cwd=extracted, check=True, capture_output=True)
                source = extracted / 'squashfs-root/helper'
            for version in ('0.982.1', '0.982.2'):
                install = root / 'versions' / version
                install.mkdir(parents=True, mode=0o700)
                src = source if version == '0.982.1' else args.fixture / 'v2/usr/lib/campus-982-disposable-spike/helper'
                shutil.copyfile(src, install / 'helper')
                (install / 'helper').chmod(0o700)
                atomic_json(install / 'manifest.json', {'helper_sha256': sha(install / 'helper'), 'architecture': artifacts['arch'], 'synthetic_state_schema': 1, 'package_sha256': artifacts['appimage']['sha256'] if format == 'appimage' and version == '0.982.1' else artifacts['packages']['v1' if version.endswith('1') else 'v2']['sha256'], 'signature_scope': 'disposable fixture only; AppImage unsigned'})
            select(root, '0.982.1')
            atomic_json(root / 'synthetic-outbox.json', {'pending': [1, 2], 'ack_cursor': 0, 'owner': 'synthetic'})
            outbox_digest = sha(root / 'synthetic-outbox.json')
            proc, identity = spawn(root)
            try:
                duplicate = subprocess.run([str(root / 'current/helper'), str(root)], timeout=5)
                assert duplicate.returncode == 73
                outer.rename(base / ('moved.' + format))
                (base / ('moved.' + format)).unlink()
                shutil.rmtree(extracted)
                assert proc.poll() is None and Path(identity['image']).is_file()
                (root / 'active-attempt').touch()
                busy = subprocess.run([sys.executable, __file__, '--child-root', str(root)], capture_output=True)
                assert busy.returncode != 0 and os.readlink(root / 'current') == 'versions/0.982.1'
                (root / 'active-attempt').unlink()
            finally:
                duration = stop(proc)
            promote(root, None)
            new, new_identity = spawn(root)
            stop(new)
            assert new_identity['version'] == '0.982.2'
            assert sha(root / 'synthetic-outbox.json') == outbox_digest
            rows.append({'format': format, 'case': 'stable-copy-singleton-move-delete-busy-fence-promote', 'result': 'PASS', 'old_identity': identity, 'new_identity': new_identity, 'termination_seconds': duration, 'synthetic_outbox_sha256': outbox_digest, 'appimage_execution': 'extract-only; FUSE mount and graphical UI not exercised' if format == 'appimage' else 'dpkg-deb extracted helper'})
            for boundary in ('after-stage', 'after-fence', 'before-promote', 'after-promote', 'after-accept'):
                select(root, '0.982.1')
                (root / 'promotion.json').unlink(missing_ok=True)
                (root / 'fenced.json').unlink(missing_ok=True)
                interrupted = subprocess.run([sys.executable, __file__, '--child-root', str(root), '--crash-at', boundary])
                assert interrupted.returncode == 91
                recover(root)
                expected = '0.982.2' if boundary == 'after-accept' else '0.982.1'
                assert os.readlink(root / 'current') == 'versions/' + expected
                assert sha(root / 'synthetic-outbox.json') == outbox_digest
                recovered, recovered_identity = spawn(root)
                stop(recovered)
                rows.append({'format': format, 'case': 'crash-' + boundary, 'result': 'PASS', 'recovered_identity': recovered_identity, 'claims': 'not implemented; any recovery fence remains until reconciliation'})
            manifest = root / 'versions/0.982.2/manifest.json'
            contents = json.loads(manifest.read_text())
            contents['synthetic_state_schema'] = 2
            atomic_json(manifest, contents)
            before = os.readlink(root / 'current')
            incompatible = subprocess.run([sys.executable, __file__, '--child-root', str(root)], capture_output=True)
            assert incompatible.returncode != 0 and os.readlink(root / 'current') == before
            rows.append({'format': format, 'case': 'incompatible-synthetic-state-rejected', 'result': 'PASS'})
            shutil.rmtree(root)
            assert sentinel.read_text() == 'must-survive-uninstall'
            rows.append({'format': format, 'case': 'fixture-uninstall-preserves-sibling-user-data', 'result': 'PASS', 'limits': 'no registration credentials or systemd unit created by this model'})
    passed = len(rows) == 16 and all(row['result'] == 'PASS' for row in rows)
    args.output.write_text(json.dumps({'pass': passed, 'script_sha256': sha(Path(__file__)), 'scope': 'disposable package/helper filesystem and process mechanism model; no production protocol, systemd or graphical acceptance', 'cases': rows}, indent=2) + '\n')
    print(args.output.read_text())
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
