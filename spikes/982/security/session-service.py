#!/usr/bin/env python3
"""Dedicated #982 real-GDM service lifecycle probe. Parent controls logout/login."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile
import time

UNIT = 'campus-982-session-spike.service'
MARKER = 'Campus #982 disposable session mechanism only'
HELPER = r'''#!/usr/bin/python3
import fcntl, json, os, pathlib, signal, sys, time
root = pathlib.Path(sys.argv[1])
state_file = root / 'state.json'
log_file = root / 'events.jsonl'
stop = False

def event(kind, **fields):
    record = dict(event=kind, time_ns=time.time_ns(), monotonic_ns=time.monotonic_ns(), pid=os.getpid(), **fields)
    fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, (json.dumps(record, sort_keys=True) + '\n').encode())
        os.fsync(fd)
    finally:
        os.close(fd)

def state_mutation(change=None):
    with open(root / 'state.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        value = json.loads(state_file.read_text())
        if change:
            change(value)
            temp = root / ('state.%d.tmp' % os.getpid())
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as out:
                out.write(json.dumps(value) + '\n'); out.flush(); os.fsync(out.fileno())
            os.replace(temp, state_file)
            directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(directory)
            finally: os.close(directory)
        return value

def terminate(signum, frame):
    global stop
    stop = True

os.umask(0o077)
signal.signal(signal.SIGTERM, terminate)
signal.signal(signal.SIGUSR1, terminate)
initial = state_mutation()
if initial['revoked']:
    event('withheld_revoked', epoch=initial['epoch'])
    sys.exit(0)
epoch = initial['epoch']

def admit(value):
    if value['epoch'] != epoch or value['revoked']:
        return
    value['starts'] += 1
    if value['failures_remaining']:
        value['failures_remaining'] -= 1

remaining = initial['failures_remaining']
admitted = state_mutation(admit)
if admitted['epoch'] != epoch or admitted['revoked']:
    event('withheld_epoch', epoch=epoch)
    sys.exit(0)
stat = pathlib.Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
event('start', epoch=epoch, uid=os.getuid(), start_ticks=int(stat[19]),
      boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
      cgroup=pathlib.Path('/proc/self/cgroup').read_text().strip(),
      helper=str(pathlib.Path(__file__).resolve()), executable=os.readlink('/proc/self/exe'),
      inherited_environment_names=sorted(os.environ), remaining_failures_before_start=remaining)
if remaining:
    event('intentional_failure_75', epoch=epoch)
    sys.exit(75)
event('admitted', epoch=epoch)
while not stop:
    current = state_mutation()
    if current['revoked'] or current['epoch'] != epoch:
        event('revoked_or_epoch_changed', admitted_epoch=epoch, current_epoch=current['epoch'])
        sys.exit(0)
    time.sleep(0.1)
event('intentional_zero', epoch=epoch)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['setup', 'observe', 'start', 'retries', 'crash',
                                            'intentional-stop', 'revoke', 'reset', 'cleanup'])
    args = parser.parse_args()
    if os.uname().sysname != 'Linux':
        raise SystemExit('disposable Linux guest required')
    account = pwd.getpwnam('campusqa')
    if os.getuid() == 0:
        os.setgroups([]); os.setgid(account.pw_gid); os.setuid(account.pw_uid)
    if os.getuid() != account.pw_uid:
        raise SystemExit('run as campusqa, or guest root to drop to campusqa')
    os.umask(0o077)
    home = Path(account.pw_dir)
    os.chdir(home)
    base = home / '.local/share/campus-982-spike/session'
    state_root = base / 'state'
    unit_file = home / '.config/systemd/user' / UNIT
    env = {'HOME': str(home), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
           'XDG_RUNTIME_DIR': '/run/user/%d' % account.pw_uid,
           'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/%d/bus' % account.pw_uid}
    commands = []

    def command(argv, required=False):
        result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=12)
        commands.append({'argv': argv, 'returncode': result.returncode,
                         'stdout': result.stdout[:32768], 'stderr': result.stderr[:32768]})
        if required and result.returncode:
            raise RuntimeError('command failed: ' + ' '.join(argv))
        return result

    def systemctl(*argv, required=False):
        return command(['systemctl', '--user', *argv], required)

    def check_owned():
        if base.is_symlink() or not (base / 'OWNED-BY-982').is_file():
            raise RuntimeError('dedicated owned spike directory missing or replaced')
        if (base / 'OWNED-BY-982').read_text().strip() != MARKER:
            raise RuntimeError('ownership marker mismatch')
        for path in [base, state_root, state_root / 'state.json', state_root / 'state.lock']:
            if path.is_symlink() or path.stat().st_uid != account.pw_uid:
                raise RuntimeError('state path is not an owned nonsymlink')

    def mutate(change):
        check_owned()
        with open(state_root / 'state.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            path = state_root / 'state.json'
            state = json.loads(path.read_text())
            change(state)
            fd, name = tempfile.mkstemp(prefix='state-', suffix='.tmp', dir=state_root)
            with os.fdopen(fd, 'w') as out:
                out.write(json.dumps(state) + '\n'); out.flush(); os.fsync(out.fileno())
            os.replace(name, path)
            directory = os.open(state_root, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(directory)
            finally: os.close(directory)

    try:
        if args.operation == 'setup':
            if base.exists() and (base.is_symlink() or (base / 'OWNED-BY-982').is_symlink() or not (base / 'OWNED-BY-982').is_file() or (base / 'OWNED-BY-982').read_text().strip() != MARKER):
                raise RuntimeError('refusing to adopt existing unmarked spike path')
            base.mkdir(parents=True, mode=0o700, exist_ok=True)
            base.chmod(0o700)
            (base / 'OWNED-BY-982').write_text(MARKER + '\n')
            if state_root.is_symlink():
                raise RuntimeError('refusing symlink state directory')
            state_root.mkdir(mode=0o700, exist_ok=True)
            (state_root / 'state.lock').touch(mode=0o600, exist_ok=True)
            state_file = state_root / 'state.json'
            if not state_file.exists():
                state_file.write_text(json.dumps({'epoch': 1, 'revoked': False, 'starts': 0,
                                                  'failures_remaining': 0}) + '\n')
            check_owned()
            version = hashlib.sha256(HELPER.encode()).hexdigest()
            versions = base / 'versions'
            if versions.is_symlink():
                raise RuntimeError('refusing symlink version directory')
            versions.mkdir(mode=0o700, exist_ok=True)
            target = versions / version
            if target.is_symlink():
                raise RuntimeError('refusing symlink version identity')
            target.mkdir(mode=0o700, exist_ok=True)
            helper = target / 'helper.py'
            if helper.exists() and helper.read_text() != HELPER:
                raise RuntimeError('versioned helper bytes changed')
            helper.write_text(HELPER); helper.chmod(0o700)
            promotion = base / ('current-' + str(os.getpid()))
            promotion.symlink_to('versions/' + version)
            os.replace(promotion, base / 'current')
            unit_file.parent.mkdir(parents=True, exist_ok=True)
            if unit_file.is_symlink() or (unit_file.exists() and MARKER not in unit_file.read_text()):
                raise RuntimeError('refusing to overwrite an unrelated unit')
            # Stable launcher lives outside all AppImage mounts. Env is cleared before helper.
            content = f'''# {MARKER}
[Unit]
Description={MARKER}
Requisite=graphical-session.target
After=graphical-session.target
PartOf=graphical-session.target
StartLimitIntervalSec=0

[Service]
Type=exec
ExecStart=/usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/python3 {base}/current/helper.py {state_root}
Restart=on-failure
RestartSec=250ms
RestartSteps=3
RestartMaxDelaySec=2s
KillMode=control-group
TimeoutStopSec=2s
UMask=0077
LimitCORE=0
NoNewPrivileges=yes

[Install]
WantedBy=graphical-session.target
'''
            unit_file.write_text(content); unit_file.chmod(0o600)
            command(['systemd-analyze', '--user', 'verify', str(unit_file)], required=True)
            systemctl('daemon-reload', required=True)
            systemctl('enable', UNIT, required=True)
            # Requisite makes this fail at the greeter; never start the graphical target here.
            systemctl('start', UNIT)
            time.sleep(0.4)
        elif args.operation == 'cleanup':
            check_owned()
            systemctl('disable', '--now', UNIT, required=True)
            if unit_file.exists():
                if MARKER not in unit_file.read_text():
                    raise RuntimeError('unit ownership marker changed')
                unit_file.unlink()
            systemctl('daemon-reload', required=True)
            systemctl('reset-failed', UNIT)
            shutil.rmtree(base)
        else:
            check_owned()
            if args.operation == 'start':
                systemctl('start', UNIT)
                time.sleep(0.4)
            elif args.operation == 'retries':
                systemctl('stop', UNIT, required=True)
                def retry(state):
                    if state['revoked']:
                        raise RuntimeError('retries never clears durable revocation; use explicit reset')
                    state['failures_remaining'] = 3
                mutate(retry)
                systemctl('reset-failed', UNIT)
                systemctl('start', UNIT)
                time.sleep(7)
            elif args.operation == 'crash':
                systemctl('kill', '--kill-whom=main', '--signal=SIGKILL', UNIT, required=True)
                time.sleep(3)
            elif args.operation == 'intentional-stop':
                systemctl('kill', '--kill-whom=main', '--signal=SIGUSR1', UNIT, required=True)
                time.sleep(3)
            elif args.operation == 'revoke':
                def revoke(state):
                    state['epoch'] += 1; state['revoked'] = True
                mutate(revoke)
                time.sleep(0.5)
            elif args.operation == 'reset':
                def reset(state):
                    state['epoch'] += 1; state['revoked'] = False; state['failures_remaining'] = 0
                mutate(reset)
                systemctl('reset-failed', UNIT)
                systemctl('start', UNIT)
                time.sleep(0.4)
    finally:
        systemctl('show', 'graphical-session.target', '--property=ActiveState', '--property=SubState')
        systemctl('show', UNIT, '--property=ActiveState', '--property=SubState', '--property=MainPID',
                  '--property=ControlGroup', '--property=NRestarts', '--property=Result',
                  '--property=RestartUSec', '--property=RestartSteps', '--property=RestartMaxDelayUSec',
                  '--property=ExecMainStatus', '--property=ExecMainCode', '--property=FragmentPath')
        command(['loginctl', 'list-sessions', '--no-legend'])
        state = json.loads((state_root / 'state.json').read_text()) if (state_root / 'state.json').exists() else None
        events = (state_root / 'events.jsonl').read_text().splitlines() if (state_root / 'events.jsonl').exists() else []
        print(json.dumps({'scope': MARKER, 'operation': args.operation, 'time_ns': time.time_ns(),
                          'uid': account.pw_uid, 'unit': UNIT, 'base': str(base),
                          'state': state, 'events': [json.loads(line) for line in events[-100:]],
                          'commands': commands,
                          'limitations': 'Synthetic epoch only. Parent must record real GDM logout/login, SSH survival, absent target refusal and no-window restart. Not a product package receipt.'}, indent=2))


if __name__ == '__main__':
    main()
