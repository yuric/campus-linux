#!/usr/bin/env python3
"""Offline disposable vendor updater failure observations; never rollback acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import time


def bounds():
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact_root', type=Path)
    args = parser.parse_args()
    source = args.artifact_root.resolve(strict=True)
    if platform.system() != 'Linux' or platform.machine() != 'aarch64' or os.getuid() == 0:
        raise SystemExit('unprivileged disposable Linux arm64 guest required')
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64':
        raise SystemExit('execute only in the named owned disposable guest')
    interfaces = [s.split(':')[0].strip() for s in Path('/proc/net/dev').read_text().splitlines() if ':' in s]
    if interfaces != ['lo']:
        raise SystemExit('fresh unshare --net namespace with loopback only required')
    os.umask(0o077)
    root = source / 'update-failures'
    root.mkdir(mode=0o700, exist_ok=False)
    records = []
    specifications = [
        ('claude', '.local/share/claude/versions/2.1.301', '.local/bin/claude',
         ['update'], 'native-shaped extracted binary, not vendor installer-created'),
        ('codex', '.local/bin/codex', '.local/bin/codex',
         ['update'], 'standalone extracted binary; reference npm tree not tested'),
        ('grok', '.grok/downloads/grok-linux-aarch64', '.grok/bin/grok',
         ['update', '--version', '1.0.59'], 'native-shaped extracted binary; requested older version unavailable offline'),
        ('agy', '.local/bin/agy', '.local/bin/agy',
         ['update'], 'native-shaped extracted binary, not vendor installer-created'),
    ]
    for engine, relative, link_relative, argv, layout_label in specifications:
        original = source / engine / engine
        artifact = json.loads((source / engine / 'artifact.json').read_text())
        original_hash = checksum(original)
        if original_hash != artifact['binary_sha256']:
            raise ValueError('source binary changed from artifact receipt')
        home = root / engine
        home.mkdir(mode=0o700)
        target, launcher = home / relative, home / link_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target); target.chmod(0o700)
        if launcher != target:
            launcher.parent.mkdir(parents=True, exist_ok=True)
            launcher.symlink_to(os.path.relpath(target, launcher.parent))
        state = home / 'isolated-auth'
        state.mkdir(mode=0o700)
        sentinel = state / 'synthetic-user-data.keep'
        sentinel.write_bytes(b'campus982 disposable preservation sentinel\n')
        sentinel_hash = checksum(sentinel)
        environment = {'HOME': str(home), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
                       'XDG_CONFIG_HOME': str(home / 'config'), 'XDG_CACHE_HOME': str(home / 'cache'),
                       'XDG_DATA_HOME': str(home / 'data'), 'TMPDIR': str(home), 'CI': '1',
                       'TERM': 'dumb', 'DISABLE_AUTOUPDATER': '1'}
        var = {'claude': 'CLAUDE_CONFIG_DIR', 'codex': 'CODEX_HOME', 'grok': 'GROK_HOME'}.get(engine)
        if var:
            environment[var] = str(state)
        # Two actual updater invocations contend on this same disposable layout.
        # Network is absent; this is failure/concurrent-attempt evidence, not an active-run update pass.
        children = []
        for index in range(2):
            log = home / ('update-%d.txt' % index)
            stream = log.open('wb')
            start = time.monotonic()
            child = subprocess.Popen([str(launcher)] + argv, cwd=home, env=environment,
                                     stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                                     close_fds=True, start_new_session=True, preexec_fn=bounds)
            children.append((child, stream, log, start))
        deadline = time.monotonic() + 20
        outcomes = []
        for child, stream, log, start in children:
            timed_out = False
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(child.pid, signal.SIGKILL); child.wait()
            finally:
                try: os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                stream.close()
            outcomes.append({'argv': [str(launcher)] + argv, 'pid': child.pid,
                'returncode': child.returncode, 'timeout': timed_out,
                'seconds': round(time.monotonic() - start, 3), 'capture': str(log.relative_to(source)),
                'output_bytes': log.stat().st_size})
        resolved = launcher.resolve(strict=False)
        in_layout = resolved.is_relative_to(home)
        after_hash = checksum(resolved) if in_layout and resolved.is_file() else None
        records.append({'engine': engine, 'version': artifact['version'], 'layout': layout_label,
            'launcher': str(launcher), 'resolved_after': str(resolved), 'resolved_inside_layout': in_layout,
            'binary_sha256_before': original_hash, 'binary_sha256_after': after_hash,
            'binary_unchanged': original_hash == after_hash,
            'sentinel_unchanged': sentinel.exists() and checksum(sentinel) == sentinel_hash,
            'source_unchanged': checksum(original) == original_hash, 'concurrent_attempts': outcomes,
            'interpretation': 'Only offline updater invocation and failure preservation measured; no successful update, rollback or active provider run proved.'})
    result = {'uname': list(os.uname()), 'uid': os.getuid(), 'network_interfaces': interfaces,
        'probe_sha256': checksum(Path(__file__)), 'observation_complete': True,
        'preservation_checks_passed': all(row['resolved_inside_layout'] and row['binary_unchanged'] and row['sentinel_unchanged'] and row['source_unchanged'] for row in records),
        'successful_update_or_rollback_proven': False,
        'records': records, 'not_proven': ['successful vendor update', 'previous-version recovery',
        'authenticity after update', 'active provider run/install concurrency', 'reference Codex npm layout',
        'vendor-created installation layouts', 'disk-full or interruption during successful promotion']}
    (root / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['preservation_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
