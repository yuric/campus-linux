#!/usr/bin/env python3
"""Source-only controller for a separately leased normal-GUI denial attempt.

Run only from the existing independent root session. This is not a privilege
acquisition interface. A new reviewed source manifest and GUI driver are required.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import signal
import stat
import sys
import time
from types import SimpleNamespace


def load(path, expected):
    # Verify before executing any adjacent module, including under python -I.
    path = Path(path)
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise RuntimeError('noncanonical staged module')
    for parent in (path.parent, *path.parent.parents):
        info = parent.stat()
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise RuntimeError('untrusted staged module parent')
    info = path.lstat()
    if info.st_size > 128 * 1024:
        raise RuntimeError("oversized staged module")
    raw = path.read_bytes()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o222
            or path.parent.stat().st_mode & 0o222 or len(raw) > 128 * 1024
            or hashlib.sha256(raw).hexdigest() != expected):
        raise RuntimeError('staged module differs from independently reviewed bytes')
    spec = importlib.util.spec_from_file_location(path.stem.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    # Execute exactly the verified buffer; no second path read/import substitution.
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('lease', 'session-id', 'app-sha256', 'source-sha256', 'gate-source-sha256', 'authority-source-sha256'):
        parser.add_argument('--' + name, required=True)
    for name in ('uid', 'driver-pid', 'terminal-pid'):
        parser.add_argument('--' + name, type=int, required=True)
    for name in ('gate-directory', 'hints', 'source-manifest', 'gate-source', 'authority-source', 'receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if (sys.platform != 'linux' or os.getuid() != 0 or os.geteuid() != 0 or not sys.flags.isolated
            or not sys.dont_write_bytecode or 'PKEXEC_UID' in os.environ):
        raise RuntimeError('existing Linux root control session with /usr/bin/python3 -I -B required')
    authority = load(args.authority_source, args.authority_source_sha256)
    authority.staged_source(Path(__file__), args.source_sha256)
    helper = authority.staged_source(args.authority_source, args.authority_source_sha256)
    gate = load(args.gate_source, args.gate_source_sha256)
    sources = gate.root_read(args.source_manifest)
    required = {'desktop.py', 'serve.py', 'gated.py', 'gated-driver.py'}
    gate.require(set(sources) == required, 'exact reviewed GUI source manifest required')
    for name, entry in sources.items():
        gate.require(Path(entry['path']).name == name and gate.sha(gate.root_read_source(Path(entry['path']))) == entry['sha256'],
                     'GUI source manifest mismatch')
    gate.require(len({str(Path(entry['path']).parent) for entry in sources.values()}) == 1, 'GUI sources must share reviewed immutable directory')
    gate.require(sources['gated.py']['sha256'] == args.gate_source_sha256, 'root and GUI gate source differ')
    gate.require(args.uid > 0 and args.hints.is_absolute() and args.hints.resolve(strict=True) == args.hints
                 and args.hints.stat().st_uid == args.uid, 'existing GUI hint directory required')
    gate.require(not any((args.hints / name).exists() for name in ('app.json', 'request.json', 'abort.json')),
                 'stale hints refuse before preparation')
    authority.safe_root_parent(args.gate_directory.parent)
    authority.safe_root_parent(args.receipt.parent, private=True)
    args.gate_directory.mkdir(mode=0o555)  # Exclusive mkdir; no existing directory reused.
    os.chmod(args.gate_directory, 0o555)
    config = {'schema': 1, 'mode': gate.MODE, 'lease': args.lease, 'nonce': secrets.token_hex(16),
              'uid': args.uid, 'session_id': args.session_id, 'driver_pid': args.driver_pid,
              'terminal_pid': args.terminal_pid, 'app_sha256': args.app_sha256,
              'sources': sources, 'hints': str(args.hints), 'boot_id': gate.boot_id(),
              'prepared_ns': time.monotonic_ns()}
    config['prepare_deadline_ns'] = config['prepared_ns'] + 60_000_000_000
    config['terminal'] = gate.kernel_process(args.terminal_pid)
    config['custody'] = gate.custody(config, time.monotonic_ns() + 3_000_000_000)
    gate.source_process(args.driver_pid, sources['gated-driver.py'], args.uid)
    gate.publish(args.gate_directory, 'config.json', config)
    print(json.dumps({'event': 'gate_prepared', 'directory': str(args.gate_directory)}), flush=True)
    fd = os.open(args.receipt, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    window_args = SimpleNamespace(mode='deny', lease=args.lease, uid=args.uid, duration_seconds=45,
                                 source_receipt=helper, allow_shared_authority_window=False,
                                 subject_pid=None, session_id=args.session_id, receipt=args.receipt,
                                 gate_directory=args.gate_directory)
    window = authority.Window(window_args, fd)
    window.record['gated_control_sources'] = {'controller_sha256': args.source_sha256,
                                             'gate_sha256': args.gate_source_sha256,
                                             'gui_sources': sources}
    window.save()
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, authority.interrupted)
    try:
        while time.monotonic_ns() < config['prepare_deadline_ns']:
            gate.require(not (args.hints / 'abort.json').exists(), 'GUI aborted preparation')
            try:
                hint = gate.hint_read(args.hints / 'app.json')
                request = gate.hint_read(args.hints / 'request.json')
                break
            except FileNotFoundError:
                time.sleep(0.02)
        else:
            raise RuntimeError('GUI app/request preparation deadline')
        window.gated_context = (gate, config, hint, request)
        window.begin()  # Independently samples actual app before creating any rule.
        binding = window.record['user_manager_binding']
        window.record['lifetime_observations'] = []
        while time.monotonic() < window.deadline:
            gate.require(not (args.hints / 'abort.json').exists(), 'GUI recorder/server aborted')
            row = gate.recheck(binding, config, min(int(window.deadline * 1e9), binding['app_deadline_ns']), allow_zombie=True)
            window.record['lifetime_observations'].append({'monotonic_ns': time.monotonic_ns(), 'app': row})
            gate.require(len(window.record['lifetime_observations']) <= 128, 'lifetime observation bound')
            window.save()
            if row['state'] == 'Z':
                window.record['gate_transport'] = gate.transport_log(args.hints / 'server.jsonl')
                window.record['status'] = 'app_completed_pending_coordinator_review'
                break
            time.sleep(0.1)
        else:
            raise RuntimeError('authority observation deadline')
    except Exception as error:
        window.record.update(status='failed', error=str(error)[:2048])
    finally:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, signal.SIG_IGN)
        try:
            window.restore()
            # Remove only the exact release emitted by this helper. A changed
            # artifact requires independent recovery and cannot permit reaping.
            release = args.gate_directory / 'release.json'
            if release.exists():
                gate.require(gate.root_read(release) == window.record.get('gate_release'), 'release changed')
                release.unlink()
                (args.gate_directory / '.release.json.pending').unlink()
            gate.require(not os.path.lexists(authority.RULE), 'rule remains; no restoration acknowledgment')
            restoration = {
                'schema': 1, 'lease': config['lease'], 'nonce': config['nonce'], 'boot_id': config['boot_id'],
                'rule_absent': True, 'restored_ns': time.monotonic_ns(), 'status': window.record['status']}
            gate.publish(args.gate_directory, 'restored.json', restoration)
            window.record['gate_restoration'] = restoration
        except Exception as error:
            window.record.update(cleanup='manual_recovery_required', cleanup_error=str(error)[:2048])
        window.record['window_finished_unix_ns'] = time.time_ns()
        if window.started_at is not None:
            window.record['elapsed_seconds_including_cleanup'] = time.monotonic() - window.started_at
            window.record['deadline_exceeded'] = time.monotonic() > window.total_deadline
        window.save()
        os.close(fd)
    print(json.dumps({'event': 'gated_window_finished', 'status': window.record['status'],
                      'cleanup': window.record['cleanup'], 'acceptance': 'pending_coordinator_review'}), flush=True)
    return 0 if window.record['status'] == 'app_completed_pending_coordinator_review' and window.record['cleanup'] == 'restored' and not window.record.get('deadline_exceeded', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
