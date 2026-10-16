#!/usr/bin/env python3
"""Register a temporary desktop handler, observe xdg-open, then restore defaults.
Run --cleanup explicitly after screenshots. Snapshots are private and never printed.
No HTTP listener, account, API request, password or provider execution occurs.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

PREFIX = 'campus-982-links-'
GOOD = 'campus://task/982?island=https%3A%2F%2Ffixture.example.invalid'
NEGATIVE = (
    ('empty-id', 'campus://task/?island=https%3A%2F%2Ffixture.example.invalid'),
    ('unicode-id', 'campus://task/９８２?island=https%3A%2F%2Ffixture.example.invalid'),
    ('overflow-id', 'campus://task/9223372036854775808?island=https%3A%2F%2Ffixture.example.invalid'),
    ('encoded-separator', 'campus://task/982%2F983?island=https%3A%2F%2Ffixture.example.invalid'),
    ('foreign-principal', 'campus://task/982?island=https%3A%2F%2Fforeign.example.invalid'),
    ('userinfo-principal', 'campus://task/982?island=https%3A%2F%2Fuser%40fixture.example.invalid'),
    ('fragment', GOOD + '#other'),
    ('duplicate-query', GOOD + '&island=https%3A%2F%2Ffixture.example.invalid'),
    ('unknown-query', GOOD + '&token=synthetic-rejected'),
    ('missing-principal', 'campus://task/982'),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(argv):
    return subprocess.check_output(argv, text=True, stderr=subprocess.STDOUT, timeout=15).strip()


def quote(value):
    # Desktop Entry Exec quoting, parsed as argv by GIO; never /bin/sh -c.
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$') + '"'


def snapshot(path):
    try:
        stream = regular_file(path, os.O_RDONLY)
    except FileNotFoundError:
        return {'path': str(path), 'existed': False}
    with stream:
        return {'path': str(path), 'existed': True, 'mode': os.fstat(stream.fileno()).st_mode & 0o777, 'data': base64.b64encode(stream.read()).decode()}


def regular_file(path, flags):
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('refuse nonregular default file')
        return os.fdopen(fd, 'r+b' if flags & os.O_RDWR else 'rb')
    except BaseException:
        os.close(fd)
        raise


def current_hash(path):
    try:
        with regular_file(path, os.O_RDONLY) as stream:
            return sha(stream.read())
    except FileNotFoundError:
        return None


def restore_default(saved):
    path = Path(saved['path'])
    try:
        stream = regular_file(path, os.O_RDWR if saved['existed'] else os.O_RDONLY)
    except FileNotFoundError:
        if saved['after_sha256'] is not None or saved['existed']:
            raise ValueError('default disappeared; preserve and reconcile manually')
        return
    with stream:
        if sha(stream.read()) != saved['after_sha256']:
            raise ValueError('default changed; preserve and reconcile manually')
        if saved['existed']:
            stream.seek(0)
            stream.write(base64.b64decode(saved['data']))
            stream.truncate()
            stream.flush()
            os.fchmod(stream.fileno(), saved['mode'])
        else:
            # Cooperative cleanup only: this check/unlink is not atomic against
            # an adversarial same-UID rename. Never use on owner defaults.
            actual = os.stat(path, follow_symlinks=False)
            opened = os.fstat(stream.fileno())
            if (actual.st_dev, actual.st_ino) != (opened.st_dev, opened.st_ino):
                raise ValueError('default replaced; preserve and reconcile manually')
            path.unlink()


def events(root):
    file = root / 'events.jsonl'
    return [json.loads(line) for line in file.read_text().splitlines()] if file.exists() else []


def cleanup(root):
    state = json.loads((root / 'state.json').read_text())
    try:
        stopped = subprocess.run([state['executable'], '--root', str(root), '--format', state['format'], '--quit'], timeout=15)
        stop_result = stopped.returncode
    except (OSError, subprocess.TimeoutExpired):
        stop_result = 'unavailable-or-timeout'
    # Cooperative snapshot verification in the owned disposable guest only.
    # No-follow FDs prevent final-component symlink writes; no same-UID race claim.
    for saved in state['defaults']:
        path = Path(saved['path'])
        current = current_hash(path)
        assert current == saved['after_sha256'], 'default changed concurrently; preserve and reconcile manually'
    for saved in state['defaults']:
        restore_default(saved)
    desktop = Path(state['desktop'])
    assert desktop.name == PREFIX + state['format'] + '.desktop'
    restore_default({'path': str(desktop), 'existed': False, 'after_sha256': state['desktop_sha256']})
    restored = command(['xdg-mime', 'query', 'default', 'x-scheme-handler/campus'])
    assert restored == state['prior_default']
    report = {'script_sha256': sha(Path(__file__).read_bytes()), 'restored_default': restored, 'prior_default': state['prior_default'], 'desktop_removed': not desktop.exists(), 'ui_stop_exit': stop_result, 'result': 'PASS' if stop_result == 0 else 'FAIL: defaults restored but UI stop requires reconciliation'}
    (root / 'cleanup.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if stop_result == 0 else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--format', choices=('deb', 'appimage'))
    p.add_argument('--executable', type=Path)
    p.add_argument('--cleanup', action='store_true')
    args = p.parse_args()
    assert os.getuid() != 0 and args.root.is_absolute()
    if args.cleanup:
        return cleanup(args.root)
    assert args.executable and args.executable.is_absolute() and args.executable.is_file() and args.format
    os.umask(0o077)
    args.root.mkdir(mode=0o700)
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    applications = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'applications'
    applications.mkdir(parents=True, exist_ok=True)
    desktop = applications / (PREFIX + args.format + '.desktop')
    assert not desktop.exists()
    names = {'mimeapps.list'}
    for name in os.environ.get('XDG_CURRENT_DESKTOP', '').lower().split(':'):
        if name and all(c.isascii() and (c.isalnum() or c in '-_') for c in name):
            names.add(name + '-mimeapps.list')
    defaults = [snapshot(parent / name) for parent in (config, applications) for name in sorted(names)]
    prior = command(['xdg-mime', 'query', 'default', 'x-scheme-handler/campus'])
    content = '[Desktop Entry]\nType=Application\nName=Disposable Campus #982 link probe\nNoDisplay=true\nTerminal=false\nMimeType=x-scheme-handler/campus;\nExec=' + quote(args.executable) + ' --root ' + quote(args.root) + ' --format ' + args.format + ' %u\n'
    state = {'defaults': defaults, 'prior_default': prior, 'desktop': str(desktop), 'desktop_sha256': sha(content.encode()), 'executable': str(args.executable), 'format': args.format}
    for saved in defaults:
        path = Path(saved['path'])
        saved['after_sha256'] = current_hash(path)
    (args.root / 'state.json').write_text(json.dumps(state, indent=2) + '\n')
    try:
        with desktop.open('x') as stream:
            stream.write(content)
        desktop.chmod(0o644)
        command(['xdg-mime', 'default', desktop.name, 'x-scheme-handler/campus'])
    finally:
        for saved in defaults:
            path = Path(saved['path'])
            saved['after_sha256'] = current_hash(path)
        (args.root / 'state.json').write_text(json.dumps(state, indent=2) + '\n')
    observed_default = command(['xdg-mime', 'query', 'default', 'x-scheme-handler/campus'])
    assert observed_default == desktop.name
    rows = []
    for label, uri, kind in [('cold-start', GOOD, 'accepted'), ('existing-window', GOOD.replace('/982?', '/983?'), 'accepted')] + [(name, uri, 'rejected') for name, uri in NEGATIVE]:
        before = len([e for e in events(args.root) if e['kind'] in ('accepted', 'rejected')])
        # GIO may launch asynchronously; HTTP-style success is not activation proof.
        with (args.root / ('launch-' + label + '.log')).open('wb') as log:
            proc = subprocess.Popen(['xdg-open', uri], stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            navigation = [e for e in events(args.root) if e['kind'] in ('accepted', 'rejected')]
            if len(navigation) > before:
                assert navigation[-1]['kind'] == kind, label
                rows.append({'case': label, 'result': 'PASS', 'event': navigation[-1]})
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(label + ': no handler receipt; xdg-open exit is insufficient')
        if kind == 'accepted':
            time.sleep(0.5)
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            # Do not kill its descendant application; record the launcher state.
            rows[-1]['launcher_pending'] = True
    time.sleep(0.5)
    recorded = events(args.root)
    windows = [e for e in recorded if e['kind'] == 'window_created']
    accepted = [e for e in recorded if e['kind'] == 'accepted']
    assert len(windows) == 1 and len({e['pid'] for e in accepted}) == 1
    if args.format == 'appimage':
        assert windows[0]['appimage'] and windows[0]['mountinfo'], 'actual AppImage mount unproven; extraction is not this case'
    observations = [e for e in recorded if e['kind'] == 'window_observation']
    focus_result = 'PASS' if len(observations) >= 2 and all(e['active'] and e['visible'] for e in observations) else 'FAIL_OR_UNOBSERVED'
    report = {'script_sha256': sha(Path(__file__).read_bytes()), 'focus_result': focus_result, 'scope': 'actual disposable desktop package activation; synthetic principal/navigation only; no localhost HTTP bridge or API fetch', 'format': args.format, 'session': os.environ.get('XDG_SESSION_TYPE'), 'display': os.environ.get('DISPLAY'), 'wayland_display': os.environ.get('WAYLAND_DISPLAY'), 'architecture': os.uname().machine, 'handler_default': observed_default, 'executable_sha256': sha(args.executable.read_bytes()), 'singleton_window': windows[0], 'window_observations': [e for e in recorded if e['kind'] == 'window_observation'], 'cases': rows, 'cleanup': 'REQUIRED after screenshot: rerun --root SAME --cleanup'}
    (args.root / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if focus_result == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
