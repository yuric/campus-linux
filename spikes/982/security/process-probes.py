#!/usr/bin/env python3
"""Disposable #982 Linux process/cgroup/crash observations; run as guest root."""
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import resource
import secrets
import select
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import time

LIBC = ctypes.CDLL(None, use_errno=True)
PR_SET_DUMPABLE, PR_GET_DUMPABLE = 4, 3


def identity(pid):
    try:
        # comm may contain spaces and parentheses; fields after its final ')' are stable.
        tail = Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()
        return {'pid': pid, 'state': tail[0], 'start_ticks': int(tail[19]),
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'cgroup': Path('/proc/%d/cgroup' % pid).read_text().strip()}
    except FileNotFoundError:
        return None


def drop_user(uid):
    def drop():
        account = pwd.getpwuid(uid)
        os.setgroups([])
        os.setgid(account.pw_gid)
        os.setuid(uid)
    return drop


def clean_env(uid):
    return {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
            'HOME': pwd.getpwuid(uid).pw_dir, 'XDG_RUNTIME_DIR': '/run/user/%d' % uid,
            'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/%d/bus' % uid}


def child_modes():
    if len(sys.argv) < 2 or not sys.argv[1].startswith('--'):
        return False
    mode = sys.argv[1]
    if mode == '--service-child':
        out = Path(sys.argv[2])
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        subprocess.Popen(['/usr/bin/python3', __file__, '--grandchild', str(out)],
                         close_fds=True, start_new_session=True)
        (out / 'leader.json').write_text(json.dumps(identity(os.getpid())))
        while True:
            time.sleep(1)
    elif mode == '--grandchild':
        out = Path(sys.argv[2])
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        (out / 'grandchild.json').write_text(json.dumps(identity(os.getpid())))
        while True:
            time.sleep(1)
    elif mode == '--dumpability':
        before = LIBC.prctl(PR_GET_DUMPABLE, 0, 0, 0, 0)
        result = LIBC.prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
        after = LIBC.prctl(PR_GET_DUMPABLE, 0, 0, 0, 0)
        print(json.dumps({'after_exec': before, 'set_result': result, 'after_child_set': after}))
    elif mode == '--crash':
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        if LIBC.prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != 0:
            raise SystemExit(3)
        marker = sys.stdin.buffer.read()
        retained = ctypes.create_string_buffer(marker)
        if not retained.raw or LIBC.prctl(PR_GET_DUMPABLE, 0, 0, 0, 0) != 0:
            raise SystemExit(4)
        os.kill(os.getpid(), signal.SIGABRT)
    elif mode == '--ipc-client':
        token = sys.stdin.buffer.read()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(5)
            endpoint = Path(sys.argv[2]).lstat()
            expected_pid, expected_start = int(sys.argv[3]), int(sys.argv[4])
            if endpoint.st_uid != 0 or not stat.S_ISSOCK(endpoint.st_mode):
                raise SystemExit(2)
            client.connect(sys.argv[2])
            pid, uid, gid = struct.unpack('3i', client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            observed = identity(pid)
            authenticated = (pid == expected_pid and uid == 0 and observed is not None
                             and observed['start_ticks'] == expected_start)
            if not authenticated:
                print(json.dumps({'server_peer_authenticated': False, 'token_sent': False,
                                  'server_pid': pid, 'server_uid': uid}))
                raise SystemExit(2)
            sent = False
            try:
                client.sendall(token)
                sent = True
                client.shutdown(socket.SHUT_WR)
                client.recv(1)
            except (BrokenPipeError, ConnectionResetError):
                pass
            print(json.dumps({'server_peer_authenticated': True, 'token_sent': sent,
                              'server_pid': pid, 'server_uid': uid,
                              'server_start_ticks': observed['start_ticks']}))
    else:
        raise SystemExit('unknown child mode')
    return True


def main():
    if sys.platform != 'linux' or os.geteuid() != 0:
        raise SystemExit('run as root only inside the disposable Linux guest')
    uid = pwd.getpwnam('campusqa').pw_uid
    nobody = pwd.getpwnam('nobody').pw_uid
    if uid == nobody:
        raise SystemExit('distinct disposable peer UIDs required')
    root = Path(tempfile.mkdtemp(prefix='campus982-process-', dir='/var/tmp'))
    root.chmod(0o755)
    script = root / 'probe.py'
    shutil.copyfile(__file__, script)
    script.chmod(0o755)
    unit = 'campus982-attempt-' + secrets.token_hex(6)
    env = clean_env(uid)
    report = {'schema': 1, 'scope': 'disposable OS mechanism only; no product acceptance',
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'uname': list(os.uname()), 'uid': uid, 'unit': unit, 'scratch': str(root),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    command_records = []

    def user_command(argv, timeout=15):
        result = subprocess.run(argv, env=env, preexec_fn=drop_user(uid),
                                capture_output=True, text=True, timeout=timeout)
        command_records.append({'argv': argv, 'returncode': result.returncode,
                                'stdout': result.stdout[:16384], 'stderr': result.stderr[:16384]})
        return result

    unit_started = False
    try:
        out = root / 'children'
        out.mkdir(mode=0o700)
        os.chown(out, uid, pwd.getpwuid(uid).pw_gid)
        launch = user_command(['systemd-run', '--user', '--unit=' + unit,
                              '--property=KillMode=control-group', '--property=TimeoutStopSec=2s',
                              '--property=SendSIGKILL=yes', '--property=Restart=no', '--property=RuntimeMaxSec=30s',
                              '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8',
                              '/usr/bin/python3', str(script), '--service-child', str(out)])
        unit_started = launch.returncode == 0
        if unit_started:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and not all((out / (r + '.json')).exists() for r in ['leader', 'grandchild']):
                time.sleep(0.1)
            identities = [json.loads(p.read_text()) for p in sorted(out.glob('*.json'))]
            pidfds = [os.pidfd_open(i['pid']) for i in identities] if hasattr(os, 'pidfd_open') else []
            show = user_command(['systemctl', '--user', 'show', unit, '--property=ControlGroup',
                                 '--property=MainPID', '--property=KillMode', '--property=TimeoutStopUSec'])
            start = time.monotonic()
            stopped = user_command(['systemctl', '--user', 'stop', unit], timeout=10)
            elapsed = time.monotonic() - start
            after = [identity(i['pid']) for i in identities]
            pidfd_exit = [bool(select.select([fd], [], [], 1)[0]) for fd in pidfds]
            for fd in pidfds:
                os.close(fd)
            survivors = [now for old, now in zip(identities, after)
                         if now and now['start_ticks'] == old['start_ticks'] and now['state'] != 'Z']
            report['cgroup_stop'] = {'before': identities, 'after': after, 'seconds': elapsed,
                'detached_grandchild_observed': len(identities) == 2,
                'same_attempt_cgroup': len(identities) == 2 and identities[0]['cgroup'] == identities[1]['cgroup'],
                'stop_returncode': stopped.returncode, 'survivors': survivors, 'pidfd_exit_readable': pidfd_exit,
                'pass': len(identities) == 2 and identities[0]['cgroup'] == identities[1]['cgroup']
                    and stopped.returncode == 0 and not survivors and elapsed < 6 and len(pidfd_exit) == 2 and all(pidfd_exit)}
        else:
            report['cgroup_stop'] = {'pass': False, 'blocked': 'user systemd unit launch failed'}
        # Demonstrate pre-exec dumpability is reset, and child-side hardening is required.
        def preexec_dump():
            drop_user(uid)()
            if LIBC.prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != 0:
                os._exit(90)
        dumped = subprocess.run(['/usr/bin/python3', str(script), '--dumpability'],
                                preexec_fn=preexec_dump, env=env, capture_output=True, text=True, timeout=10)
        report['dumpability'] = {'returncode': dumped.returncode, 'observation': json.loads(dumped.stdout),
                                'stderr': dumped.stderr}
        # Reject another UID from SO_PEERCRED before reading its queued token bytes.
        endpoint = root / 'peer.sock'
        marker = secrets.token_bytes(32)
        peers = []
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(str(endpoint)); endpoint.chmod(0o666)
            listener.listen(2); listener.settimeout(5)
            server_identity = identity(os.getpid())
            for peer_uid, expected_server_pid, expected_auth in [(nobody, os.getpid(), True),
                    (uid, os.getpid(), True), (uid, os.getpid() + 1, False)]:
                child = subprocess.Popen(['/usr/bin/python3', str(script), '--ipc-client', str(endpoint),
                                         str(expected_server_pid), str(server_identity['start_ticks'])],
                                         preexec_fn=drop_user(peer_uid), env=clean_env(peer_uid),
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, close_fds=True)
                child.stdin.write(marker); child.stdin.close()
                try:
                    conn, _ = listener.accept()
                    with conn:
                        conn.settimeout(5)
                        pid, actual_uid, gid = struct.unpack('3i', conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                        accepted = actual_uid == uid
                        value = conn.recv(4096) if accepted else None
                        peer_result = {'requested_uid': peer_uid, 'peer_pid': pid, 'peer_uid': actual_uid,
                                      'peer_gid': gid, 'token_read': accepted,
                                      'token_match': value == marker if accepted else None,
                                      'expected_server_authentication': expected_auth}
                finally:
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill(); child.wait()
                    client_result = json.loads(child.stdout.read())
                    child.stdout.close()
                    child.stderr.close()
                peer_result['client_observation'] = client_result
                peer_result['client_exit'] = child.returncode
                peer_result['pass'] = (actual_uid == peer_uid
                    and client_result['server_peer_authenticated'] == expected_auth
                    and (expected_auth or client_result['token_sent'] is False)
                    and child.returncode == (0 if expected_auth else 2)
                    and (value == marker if accepted and expected_auth else
                         value is None if not accepted else value == b''))
                peers.append(peer_result)
            endpoint.unlink()
        report['ipc_peers'] = peers
        # Real abort with synthetic data only, dumpability disabled inside the executed child.
        crashdir = Path('/var/crash')
        before = set(crashdir.iterdir()) if crashdir.exists() else set()
        coredir = Path('/var/lib/systemd/coredump')
        cores_before = set(coredir.iterdir()) if coredir.exists() else set()
        pattern = Path('/proc/sys/kernel/core_pattern').read_text().strip()
        synthetic = ('campus982-crash-' + secrets.token_hex(24)).encode()
        crashed = subprocess.run(['/usr/bin/python3', str(script), '--crash'],
                                 preexec_fn=drop_user(uid), env=env, input=synthetic,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=out, timeout=10)
        time.sleep(3)
        after = set(crashdir.iterdir()) if crashdir.exists() else set()
        new_files = sorted(str(p) for p in after - before)
        cores_after = set(coredir.iterdir()) if coredir.exists() else set()
        new_systemd_cores = sorted(str(p) for p in cores_after - cores_before)
        local_cores = [str(p) for p in out.glob('core*')]
        report['crash_collector'] = {'core_pattern': pattern, 'returncode': crashed.returncode,
            'core_limit': 0, 'child_dumpable': 0, 'new_var_crash_paths': new_files,
            'new_local_core_paths': local_cores, 'new_systemd_coredump_paths': new_systemd_cores, 'marker_in_child_output': synthetic in crashed.stdout + crashed.stderr,
            'pass': crashed.returncode == -signal.SIGABRT and not new_files and not local_cores and not new_systemd_cores
                    and synthetic not in crashed.stdout + crashed.stderr,
            'limits': 'Observed 3-second window under recorded collector only. No claim for enabled dumpability or all collectors; no unrelated crash contents read.'}
        report['process_identity_limits'] = 'boot_id + pid + /proc start_ticks + attempt cgroup recorded; PID reuse was not forced. Production must use pidfd/cgroup handles, never PID alone.'
    except Exception as exc:
        report['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        if unit:
            try:
                user_command(['systemctl', '--user', 'stop', unit], timeout=10)
                user_command(['systemctl', '--user', 'reset-failed', unit], timeout=10)
            except Exception as exc:
                report['cleanup_failure'] = str(exc)
        report['commands'] = command_records
        dump = report.get('dumpability', {})
        report['pass'] = (not report.get('failure') and not report.get('cleanup_failure')
            and report.get('cgroup_stop', {}).get('pass') is True
            and dump.get('returncode') == 0
            and dump.get('observation') == {'after_exec': 1, 'set_result': 0, 'after_child_set': 0}
            and len(report.get('ipc_peers', [])) == 3
            and all(peer.get('pass') is True for peer in report.get('ipc_peers', []))
            and report.get('crash_collector', {}).get('pass') is True)
        (root / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        # Preserve receipts; only synthetic detached children created by this unit are stopped.
        print(json.dumps(report, indent=2))
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    if not child_modes():
        raise SystemExit(main())
