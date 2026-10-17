#!/usr/bin/env python3
"""Guest-only signed Claude fixed-version install/upgrade/recovery; no model calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import stat
import subprocess
import time
import urllib.request


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def child_limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (300_000_000, 300_000_000))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact_root', type=Path)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--incremental-budget-bytes', type=int, choices=[500_000_000, 1_073_741_824], default=500_000_000)
    args = parser.parse_args()
    pins = json.loads(Path(__file__).with_name('claude-transition-pins.json').read_text())
    source = args.artifact_root.resolve(strict=True)
    if platform.system() != 'Linux' or platform.machine() != 'aarch64' or os.getuid() == 0:
        raise SystemExit('unprivileged disposable Linux arm64 guest required')
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64':
        raise SystemExit('refuse online installer outside named owned guest')
    if shutil.disk_usage(source).free < 500_000_000:
        raise SystemExit('guest free-space reserve insufficient')
    if not shutil.which('gpg'):
        raise SystemExit('gpg missing: no install or trust fallback performed')
    os.umask(0o077)
    root = source / 'claude-transitions'
    if root.is_symlink():
        raise SystemExit('refuse symlink transition root')
    root.mkdir(mode=0o700, exist_ok=args.resume)
    if root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise SystemExit('transition root must be private and owned by current user')
    previous_receipt = None
    history_record = None
    if args.resume:
        previous_receipt = json.loads((root / 'receipt.json').read_text())
        if previous_receipt.get('source_root') != str(source) or previous_receipt.get('uid') != os.getuid() or previous_receipt.get('completed') is not False:
            raise SystemExit('resume requires matching incomplete prior receipt')
        history = root / 'history'
        history.mkdir(mode=0o700, exist_ok=True)
        attempt = str(time.time_ns())
        archived = history / ('receipt-' + attempt + '.json')
        shutil.copyfile(root / 'receipt.json', archived)
        logs = []
        for old_log in sorted(root.glob('*.txt')):
            if old_log.is_symlink():
                raise SystemExit('refuse symlink prior log')
            saved = history / (attempt + '-' + old_log.name)
            shutil.copyfile(old_log, saved)
            logs.append({'path': str(saved.relative_to(root)), 'sha256': digest(saved)})
        history_record = {'receipt': str(archived.relative_to(root)), 'sha256': digest(archived), 'logs': logs}
    home = root / 'home'
    if home.is_symlink():
        raise SystemExit('refuse symlink probe home')
    home.mkdir(mode=0o700, exist_ok=args.resume)
    auth = home / 'isolated-auth'
    if auth.is_symlink():
        raise SystemExit('refuse symlink auth directory')
    auth.mkdir(mode=0o700, exist_ok=args.resume)
    sentinel = auth / 'synthetic-user-data.keep'
    if args.resume:
        if sentinel.is_symlink() or sentinel.read_bytes() != b'campus982 synthetic preservation sentinel\n':
            raise SystemExit('prior synthetic user-data sentinel changed')
    else:
        sentinel.write_bytes(b'campus982 synthetic preservation sentinel\n')
    sentinel_digest = digest(sentinel)
    environment = {'HOME': str(home), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
        'TMPDIR': str(home / 'tmp'), 'XDG_CONFIG_HOME': str(home / '.config'),
        'XDG_CACHE_HOME': str(home / '.cache'), 'XDG_DATA_HOME': str(home / '.local/share'),
        'CLAUDE_CONFIG_DIR': str(auth), 'DISABLE_AUTOUPDATER': '1',
        'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1', 'CI': '1', 'TERM': 'dumb'}
    (home / 'tmp').mkdir(mode=0o700, exist_ok=args.resume)
    os.environ.clear(); os.environ.update(environment)
    report = {'scope': 'actual vendor install command with synthetic guest-only home; no account or model request',
        'probe_sha256': digest(Path(__file__)),
        'uname': list(os.uname()), 'uid': os.getuid(), 'source_root': str(source),
        'shared_verified_bytes': '2.1.301 reused by hardlink to stay within incremental budget; not downloaded again',
        'disk_policy': 'Maximum of deduplicated tree allocated blocks (excluding original301 inode) and conservative filesystem free-space delta; prior partial attempt remains charged. 300 MB per-file kernel limit.',
        'authorized_incremental_budget_bytes': args.incremental_budget_bytes,
        'allocation_abort_threshold_bytes': args.incremental_budget_bytes - (50_000_000 if args.incremental_budget_bytes == 500_000_000 else 67_108_864),
        'prior_attempt_preserved': history_record,
        'host_disk_floor': 'Parent must separately confirm host free space >=35 GiB; guest cannot measure host APFS',
        'signatures': [], 'transitions': [], 'peak_incremental_allocated_bytes': 0}
    original = source / 'claude/claude'
    expected = {v['version']: v for v in pins['versions']}
    if digest(original) != expected['2.1.301']['binary_sha256']:
        raise SystemExit('original 2.1.301 does not match signed manifest pin')
    original_stat = original.stat()
    shared_inode = (original_stat.st_dev, original_stat.st_ino)
    allocation_baseline = {}

    def allocated(snapshot=None):
        seen = {shared_inode}; total = 0; rows = []
        for path in root.rglob('*'):
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue  # Vendor promotion can rename during this observation.
            identity = (info.st_dev, info.st_ino)
            counted = identity not in seen and not stat.S_ISLNK(info.st_mode)
            if counted:
                seen.add(identity); total += info.st_blocks * 512
            if snapshot is not None:
                rows.append({'path': str(path.relative_to(root)), 'device': info.st_dev, 'inode': info.st_ino,
                    'nlink': info.st_nlink, 'size': info.st_size, 'allocated_bytes': info.st_blocks * 512,
                    'counted': counted, 'original_shared_inode': identity == shared_inode})
        free = shutil.disk_usage(source).free
        if not allocation_baseline:
            allocation_baseline.update(tree=total, free=free)
            report['allocation_baseline'] = dict(allocation_baseline)
        free_space_charge = max(0, allocation_baseline['tree'] + allocation_baseline['free'] - free)
        charged = max(total, free_space_charge)  # Also catches unlinked-but-open staging files conservatively.
        if snapshot is not None:
            (root / snapshot).write_text(json.dumps({'total_counted_bytes': total, 'filesystem_free_space_charge': free_space_charge, 'charged_bytes': charged, 'original_device_inode': list(shared_inode), 'paths': rows}, indent=2) + '\n')
        report['peak_incremental_allocated_bytes'] = max(report['peak_incremental_allocated_bytes'], charged)
        return charged

    def fetch(url, checksum, path):
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read(128 * 1024 + 1)
        if len(data) > 128 * 1024 or hashlib.sha256(data).hexdigest() != checksum:
            raise RuntimeError('public verification metadata differs from pin')
        path.write_bytes(data)

    def gpg_run(argv):
        result = subprocess.run(['gpg', '--homedir', str(root / 'keyring'), '--batch', '--no-options',
                                 '--no-auto-key-retrieve', *argv], env=environment,
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise RuntimeError('GPG verification failed: ' + result.stderr[:2000])
        return result

    def run_commands(label, commands, timeout):
        children = []
        try:
            for index, command in enumerate(commands):
                output = root / (label + '-' + str(index) + '.txt')
                stream = output.open('wb')
                child = subprocess.Popen(command, cwd=home, env=environment, stdin=subprocess.DEVNULL,
                    stdout=stream, stderr=subprocess.STDOUT, close_fds=True, start_new_session=True,
                    preexec_fn=child_limits)
                children.append((child, stream, output, command))
            start = time.monotonic(); aborted = None
            while any(child.poll() is None for child, _, _, _ in children):
                if allocated() > report['allocation_abort_threshold_bytes']:
                    aborted = 'incremental allocation cutoff'; break
                if time.monotonic() - start > timeout:
                    aborted = 'bounded operation timeout'; break
                time.sleep(0.05)
            outcomes = []
            for child, stream, output, command in children:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait(); stream.close()
                outcomes.append({'argv': command, 'returncode': child.returncode,
                    'seconds': round(time.monotonic() - start, 3), 'capture': output.name,
                    'abort': aborted})
            report['transitions'].append({'stage': label, 'commands': outcomes})
            allocated()
            if aborted or any(outcome['returncode'] for outcome in outcomes):
                raise RuntimeError(label + ' did not complete; preserve raw failure capture')
        finally:
            for child, stream, _, _ in children:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
                stream.close()

    def inspect(version, stage):
        launcher = home / '.local/bin/claude'
        resolved = launcher.resolve(strict=True)
        if not resolved.is_relative_to(home):
            raise RuntimeError('vendor launcher escaped disposable home')
        actual = digest(resolved)
        if actual != expected[version]['binary_sha256']:
            raise RuntimeError('installed bytes differ from signed manifest; refuse execution')
        result = subprocess.run([str(launcher), '--version'], cwd=home, env=environment,
                                capture_output=True, text=True, timeout=10)
        record = {'version_requested': version, 'launcher': str(launcher), 'resolved': str(resolved),
            'binary_sha256': actual, 'matches_verified_manifest': actual == expected[version]['binary_sha256'],
            'version_returncode': result.returncode, 'version_stdout': result.stdout,
            'version_stderr': result.stderr, 'sentinel_unchanged': digest(sentinel) == sentinel_digest,
            'source_unchanged': digest(original) == expected['2.1.301']['binary_sha256']}
        report['transitions'][-1]['installed'] = record
        if not all([record['matches_verified_manifest'], record['sentinel_unchanged'],
                    record['source_unchanged'], result.returncode == 0, result.stdout.split()[:1] == [version]]):
            raise RuntimeError(stage + ' artifact/version/preservation verification failed')
        return launcher

    try:
        report['incremental_allocated_bytes_before_retry'] = allocated('allocation-before.json')
        if allocated() > report['allocation_abort_threshold_bytes']:
            raise RuntimeError('existing partial attempt exceeds newly authorized allocation threshold')
        verification = root / 'verification'; verification.mkdir(mode=0o700, exist_ok=args.resume)
        (root / 'keyring').mkdir(mode=0o700, exist_ok=args.resume)
        public_key = verification / 'key.asc'
        fetch(pins['key_url'], pins['key_sha256'], public_key)
        shown = gpg_run(['--with-colons', '--import-options', 'show-only', '--import', str(public_key)])
        fingerprints = [line.split(':')[9] for line in shown.stdout.splitlines() if line.startswith('fpr:')]
        if fingerprints != [pins['fingerprint']]:
            raise RuntimeError('vendor key fingerprint mismatch')
        gpg_run(['--import', str(public_key)])
        for version, row in expected.items():
            manifest = verification / (version + '.json')
            signature = verification / (version + '.sig')
            fetch(row['manifest_url'], row['manifest_sha256'], manifest)
            fetch(row['signature_url'], row['signature_sha256'], signature)
            checked = gpg_run(['--status-fd', '1', '--verify', str(signature), str(manifest)])
            if '[GNUPG:] VALIDSIG ' + pins['fingerprint'] + ' ' not in checked.stdout:
                raise RuntimeError('expected signing identity not verified')
            native = json.loads(manifest.read_text())['platforms']['linux-arm64']
            if native['checksum'] != row['binary_sha256'] or native['size'] != row['binary_size']:
                raise RuntimeError('verified manifest differs from pinned binary identity')
            report['signatures'].append({'version': version, 'fingerprint': pins['fingerprint'],
                'stdout': checked.stdout, 'stderr': checked.stderr, **row})
        cache = home / '.local/share/claude/versions'
        cache.mkdir(mode=0o700, parents=True, exist_ok=args.resume)
        cached = cache / '2.1.301'
        if cached.exists():
            if cached.is_symlink() or digest(cached) != expected['2.1.301']['binary_sha256']:
                raise RuntimeError('existing301 cache failed signed-manifest hash; refuse resume')
            report['existing_301_cache_inode'] = [cached.stat().st_dev, cached.stat().st_ino]
            report['existing_301_cache_is_shared_original'] = (cached.stat().st_dev, cached.stat().st_ino) == shared_inode
        else:
            os.link(original, cached)
        run_commands('install-2.1.300', [[str(original), 'install', '2.1.300']], 90)
        launcher = inspect('2.1.300', 'initial install')
        run_commands('upgrade-2.1.301', [[str(launcher), 'install', '2.1.301']], 45)
        inspect('2.1.301', 'upgrade')
        run_commands('recover-2.1.300', [[str(launcher), 'install', '2.1.300']], 45)
        inspect('2.1.300', 'recovery')
        run_commands('concurrent-install-2.1.301', [[str(launcher), 'install', '2.1.301'],
                                                  [str(launcher), 'install', '2.1.301']], 45)
        inspect('2.1.301', 'concurrent install')
        report['completed'] = True
    except Exception as exc:
        report['completed'] = False
        report['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        report['incremental_allocated_bytes_final'] = allocated('allocation-after.json')
        report['source_preserved_final'] = original.is_file() and digest(original) == expected['2.1.301']['binary_sha256']
        report['sentinel_preserved_final'] = sentinel.is_file() and digest(sentinel) == sentinel_digest
        report['final_safety_checks_passed'] = (report['source_preserved_final'] and report['sentinel_preserved_final'] and
            report['peak_incremental_allocated_bytes'] <= report['allocation_abort_threshold_bytes'])
        if not report['final_safety_checks_passed']:
            report['completed'] = False
            report.setdefault('failure', {'type': 'FinalSafetyCheckFailure', 'message': 'source/sentinel preservation or allocation bound failed'})
        report['limits'] = ['No model/account execution', 'No active provider run during install',
            'No credential refresh or account-isolation proof', 'No Campus product update action delivered',
            'Reuses verified 2.1.301 cache bytes', 'No claim for other providers or install layouts']
        (root / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    return 0 if report.get('completed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
