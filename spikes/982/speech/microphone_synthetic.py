#!/usr/bin/env python3
"""Real guest audio-server access using only a dedicated synthetic monitor source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import secrets
import shutil
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--label', choices=['wayland', 'x11'], required=True)
    args = parser.parse_args()
    if sys.platform != 'linux' or os.geteuid() != 0:
        raise SystemExit('guest root orchestration required; argument is completed speech probe directory')
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64':
        raise SystemExit('refuse root operations outside named owned disposable guest')
    os.umask(0o077)
    root = args.directory.resolve(strict=True)
    qa = pwd.getpwnam('campusqa'); nobody = pwd.getpwnam('nobody')
    base_receipt = json.loads((root / 'captures/receipt.json').read_text())
    fixture = root / 'synthetic.wav'
    if hashlib.sha256(fixture.read_bytes()).hexdigest() != base_receipt.get('audio', {}).get('sha256'):
        raise SystemExit('synthetic fixture differs from offline probe receipt')
    capture = root / ('microphone-synthetic-' + args.label); capture.mkdir(mode=0o700, exist_ok=False)
    os.chown(capture, qa.pw_uid, qa.pw_gid)
    server = '/run/user/%d/pulse/native' % qa.pw_uid
    name = 'campus982_synthetic_' + secrets.token_hex(4)
    report = {'scope': 'real guest PulseAudio/PipeWire access and cancel using dedicated synthetic source only',
        'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'recorder_sha256': hashlib.sha256(Path(__file__).with_name('synthetic_recorder.py').read_bytes()).hexdigest(),
        'source': name + '.monitor', 'sink': name, 'server': server, 'microphone_or_default_source_used': False,
        'fixture_sha256': base_receipt['audio']['sha256'], 'requested_session': args.label, 'commands': [],
        'limits': 'No product microphone consent UI, portal permission grant/deny, physical-device removal, or host microphone was tested.'}
    def drop(uid):
        def do():
            account = pwd.getpwuid(uid); os.setgroups([]); os.setgid(account.pw_gid); os.setuid(uid)
        return do
    def env(uid):
        return {'PATH': '/usr/bin:/bin', 'HOME': pwd.getpwuid(uid).pw_dir, 'LANG': 'C.UTF-8',
                'XDG_RUNTIME_DIR': '/run/user/%d' % uid, 'PULSE_SERVER': 'unix:' + server}
    def command(argv, uid=qa.pw_uid):
        result = subprocess.run(argv, env=env(uid), preexec_fn=drop(uid), capture_output=True, text=True, timeout=10)
        report['commands'].append({'argv': argv, 'uid': uid, 'returncode': result.returncode,
                                   'stdout': result.stdout[:4096], 'stderr': result.stderr[:4096]})
        return result
    module = None; recorder = None; playback = None
    try:
        if not Path(server).is_socket(): raise RuntimeError('real session audio server unavailable; no fallback server started')
        for tool in ['pactl', 'paplay']:
            if not shutil.which(tool): raise RuntimeError(tool + ' unavailable (pulseaudio-utils prerequisite)')
        session = command(['loginctl', 'show-user', qa.pw_name, '-p', 'Display', '--value'])
        session_id = session.stdout.strip()
        if session.returncode or not session_id: raise RuntimeError('active GDM display session unavailable')
        details = command(['loginctl', 'show-session', session_id, '-p', 'Type', '-p', 'Class', '-p', 'Active', '-p', 'Service', '-p', 'Remote'])
        observed = dict(line.split('=', 1) for line in details.stdout.splitlines() if '=' in line)
        report['session'] = observed
        if details.returncode or observed.get('Type') != args.label or observed.get('Class') != 'user' or observed.get('Active') != 'yes' or observed.get('Service') != 'gdm-password' or observed.get('Remote') != 'no':
            raise RuntimeError('requested real GDM tuple not active')
        denied = command(['pactl', 'info'], nobody.pw_uid)
        report['other_uid_server_access_denied'] = denied.returncode != 0
        allowed = command(['pactl', 'info'])
        report['same_uid_server_access_allowed'] = allowed.returncode == 0
        if allowed.returncode: raise RuntimeError('GDM user audio server access unavailable')
        loaded = command(['pactl', 'load-module', 'module-null-sink', 'sink_name=' + name,
                          'sink_properties=device.description=Campus982SyntheticOnly'])
        if loaded.returncode or not loaded.stdout.strip().isdigit(): raise RuntimeError('dedicated null sink unavailable')
        module = loaded.stdout.strip()
        raw = capture / 'synthetic-monitor.raw'
        with raw.open('wb') as output, (capture / 'recorder.stderr').open('wb') as err:
            recorder = subprocess.Popen(['/usr/bin/python3', str(Path(__file__).with_name('synthetic_recorder.py')),
                                         server, name + '.monitor'], env=env(qa.pw_uid),
                                         preexec_fn=drop(qa.pw_uid), stdin=subprocess.DEVNULL,
                                         stdout=output, stderr=err, start_new_session=True, close_fds=True)
            time.sleep(0.25)
            playback = subprocess.Popen(['paplay', '--device=' + name, str(fixture)], env=env(qa.pw_uid),
                                        preexec_fn=drop(qa.pw_uid), stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        start_new_session=True, close_fds=True)
            time.sleep(1.5)
            was_running = recorder.poll() is None
            started = time.monotonic()
            if was_running:
                os.killpg(recorder.pid, signal.SIGTERM)
                try: recorder.wait(timeout=2)
                except subprocess.TimeoutExpired: os.killpg(recorder.pid, signal.SIGKILL); recorder.wait()
            report['cancellation'] = {'recorder_was_running': was_running,
                'stop_seconds': time.monotonic() - started, 'returncode': recorder.returncode}
        data = raw.read_bytes()
        report['synthetic_capture'] = {'bytes': len(data), 'nonzero_samples_present': any(data),
                                        'sha256': hashlib.sha256(data).hexdigest()}
        report['completed'] = True
    except Exception as exc:
        report['completed'] = False; report['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        # Stop every recording/playback stream BEFORE unloading the synthetic source.
        # Unloading an active source can move a stream to a default source, so never do that here.
        for child in [recorder, playback]:
            if child and child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL); child.wait()
        if module is not None:
            try:
                unloaded = command(['pactl', 'unload-module', module])
                report['synthetic_source_cleanup_completed'] = unloaded.returncode == 0
            except Exception as exc:
                report['synthetic_source_cleanup_completed'] = False
                report['cleanup_failure'] = {'type': type(exc).__name__, 'message': str(exc)}
        report['checks_passed'] = (report.get('completed') is True and
            report.get('other_uid_server_access_denied') is True and report.get('same_uid_server_access_allowed') is True and
            report.get('cancellation', {}).get('recorder_was_running') is True and
            report.get('cancellation', {}).get('returncode') == -15 and
            report.get('cancellation', {}).get('stop_seconds', 999) < 2 and
            report.get('synthetic_capture', {}).get('nonzero_samples_present') is True and
            0 < report.get('synthetic_capture', {}).get('bytes', 0) < 1024 * 1024 and
            report.get('synthetic_source_cleanup_completed') is True)
        (capture / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    return 0 if report['checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
