#!/usr/bin/env python3
"""#982 offline speech candidate; public synthetic audio, never a product choice."""
import argparse
import array
import ctypes
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import tarfile
import time
import urllib.request
import wave


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['download', 'offline'])
    parser.add_argument('directory', type=Path)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    pins = json.loads(Path(__file__).with_name('pins.json').read_text())
    root = args.directory.absolute()
    if root.is_symlink():
        raise SystemExit('refuse symlink output root')
    os.umask(0o077)
    if args.operation == 'download':
        root.mkdir(mode=0o700, exist_ok=False)
        for name, pin in [('source.tar.gz', pins['whisper_cpp']), ('tiny.en.bin', pins['model'])]:
            path = root / name; count = 0
            with urllib.request.urlopen(pin['url'], timeout=30) as response, path.open('wb') as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk: break
                    count += len(chunk)
                    if count > pin['download_bytes']: raise RuntimeError('download exceeds pinned size')
                    output.write(chunk)
            if count != pin['download_bytes'] or sha(path) != pin['sha256']:
                raise RuntimeError('pinned speech artifact mismatch')
        (root / 'pins.json').write_text(json.dumps(pins, indent=2) + '\n')
        print(json.dumps({'root': str(root), 'public_download_bytes': sum(pins[k]['download_bytes'] for k in ['whisper_cpp', 'model'])}))
        return
    if platform.system() != 'Linux' or platform.machine() != 'aarch64' or os.getuid() == 0:
        raise SystemExit('unprivileged Linux arm64 guest required')
    interfaces = [s.split(':')[0].strip() for s in Path('/proc/net/dev').read_text().splitlines() if ':' in s]
    if interfaces != ['lo']:
        raise SystemExit('fresh unshare --net namespace required')
    for name, pin in [('source.tar.gz', pins['whisper_cpp']), ('tiny.en.bin', pins['model'])]:
        if sha(root / name) != pin['sha256']: raise RuntimeError('speech artifact changed')
    captures = root / 'captures'
    previous_capture = None
    if args.resume:
        previous = json.loads((captures / 'receipt.json').read_text())
        if previous.get('completed') is not False or previous.get('pins') != pins:
            raise RuntimeError('resume requires matching failed probe receipt')
        previous_capture = 'captures-failed-' + str(time.time_ns())
        captures.rename(root / previous_capture)
    captures.mkdir(mode=0o700, exist_ok=False)
    home = root / 'home'
    if home.is_symlink(): raise RuntimeError('refuse symlink home')
    home.mkdir(mode=0o700, exist_ok=args.resume)
    env = {'HOME': str(home), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'TMPDIR': str(home)}
    report = {'scope': 'Human direction10361: bounded offline candidate only; no product adoption',
        'probe_sha256': sha(Path(__file__)),
        'uname': list(os.uname()), 'uid': os.getuid(), 'interfaces': interfaces,
        'pins': pins, 'prior_failed_captures': previous_capture, 'commands': [], 'measurements': [], 'microphone_used': False,
        'runtime_data_destination': 'local disposable guest files only; no network interface except loopback',
        'cost': 'No API/cloud fees; local CPU/RAM/storage and initial public download bandwidth',
        'limits': {'probe_max_seconds': 60, 'probe_max_bytes': 10 * 1024 * 1024,
                   'languages_tested': ['English synthetic sentence only'], 'product_limits': 'not selected'}}

    def command(argv, label, timeout=300):
        result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=timeout)
        (captures / (label + '.stdout')).write_text(result.stdout)
        (captures / (label + '.stderr')).write_text(result.stderr)
        report['commands'].append({'argv': argv, 'returncode': result.returncode, 'capture': label})
        if result.returncode: raise RuntimeError(label + ' failed; inspect capture')
        return result

    def valid_audio(path):
        if path.stat().st_size > 10 * 1024 * 1024: raise ValueError('probe_size_bound')
        with wave.open(str(path), 'rb') as wav:
            duration = wav.getnframes() / wav.getframerate()
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != 16000:
                raise ValueError('probe_format_bound')
            if duration <= 0 or duration > 60: raise ValueError('probe_duration_bound')
            return duration

    try:
        command(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\t${Architecture}\n',
                 'libespeak-ng1', 'cmake', 'g++', 'make'], 'toolchain-packages')
        command(['cmake', '--version'], 'cmake-version')
        command(['g++', '--version'], 'compiler-version')
        command(['make', '--version'], 'make-version')
        source = root / 'source'
        if source.is_symlink(): raise RuntimeError('refuse symlink source')
        source.mkdir(mode=0o700, exist_ok=args.resume)
        with tarfile.open(root / 'source.tar.gz') as archive:
            total = 0
            for item in archive.getmembers():
                parts = Path(item.name).parts[1:]
                if not parts: continue
                if any(p in ('.', '..') for p in parts) or Path(item.name).is_absolute():
                    raise ValueError('source archive traversal')
                target = source.joinpath(*parts)
                if target.is_symlink(): raise ValueError('source member replaced by symlink')
                if item.isdir(): target.mkdir(parents=True, exist_ok=True)
                elif item.isfile():
                    total += item.size
                    if total > 60 * 1024 * 1024: raise ValueError('expanded source exceeds bound')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(item) as infile, target.open('wb') as outfile: shutil.copyfileobj(infile, outfile)
                    target.chmod(0o700 if item.mode & 0o111 else 0o600)
                else: raise ValueError('nonregular source archive member')
        build = root / 'build'
        command(['cmake', '-S', str(source), '-B', str(build), '-DCMAKE_BUILD_TYPE=Release',
                 '-DBUILD_SHARED_LIBS=OFF', '-DGGML_NATIVE=OFF', '-DGGML_OPENMP=OFF',
                 '-DGGML_CPU_KLEIDIAI=OFF', '-DGGML_CCACHE=OFF', '-DWHISPER_BUILD_TESTS=OFF',
                 '-DWHISPER_BUILD_SERVER=OFF', '-DWHISPER_CURL=OFF', '-DWHISPER_SDL2=OFF',
                 '-DFETCHCONTENT_FULLY_DISCONNECTED=ON'], 'configure')
        command(['cmake', '--build', str(build), '--target', 'whisper-cli', '-j2'], 'build')
        binary = build / 'bin/whisper-cli'
        report['binary_sha256'] = sha(binary)
        report['source_license_sha256'] = sha(source / 'LICENSE')
        command([str(binary), '--help'], 'cli-help')
        # Retrieve synthesized PCM directly. No audio playback/device/microphone API is called.
        library = ctypes.util.find_library('espeak-ng')
        if not library: raise RuntimeError('libespeak-ng unavailable; no substitute downloaded')
        speech = ctypes.CDLL(library)
        speech.espeak_Initialize.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        speech.espeak_Initialize.restype = ctypes.c_int
        rate = speech.espeak_Initialize(1, 0, None, 0)
        if rate <= 0: raise RuntimeError('synthetic audio initializer failed')
        chunks = []
        callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
        @callback_type
        def callback(samples, count, events):
            if samples and count: chunks.append(ctypes.string_at(samples, count * 2))
            return 0
        speech.espeak_SetSynthCallback.argtypes = [callback_type]
        speech.espeak_SetSynthCallback(callback)
        speech.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
        if speech.espeak_SetVoiceByName(b'en-us') != 0: raise RuntimeError('English synthetic voice missing')
        speech.espeak_Synth.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_int,
                                       ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
        text = pins['fixture']['text'].encode()
        text_buffer = ctypes.create_string_buffer(text)
        if speech.espeak_Synth(text_buffer, len(text) + 1, 0, 1, 0, 1, None, None) != 0:
            raise RuntimeError('synthetic utterance failed')
        speech.espeak_Synchronize()
        speech.espeak_Terminate()
        pcm = array.array('h'); pcm.frombytes(b''.join(chunks))
        result = array.array('h')
        for sample in range(int(len(pcm) * 16000 / rate)):
            position = sample * rate / 16000; left = int(position); fraction = position - left
            result.append(round(pcm[left] * (1 - fraction) + pcm[min(left + 1, len(pcm) - 1)] * fraction))
        fixture = root / 'synthetic.wav'
        def write_audio(path, data):
            with wave.open(str(path), 'wb') as out:
                out.setnchannels(1); out.setsampwidth(2); out.setframerate(16000); out.writeframes(data)
        write_audio(fixture, result.tobytes())
        duration = valid_audio(fixture)
        report['audio'] = {'sha256': sha(fixture), 'bytes': fixture.stat().st_size, 'seconds': duration,
                           'synthesis_rate': rate, 'format': 'mono PCM16 16000Hz', 'text': pins['fixture']['text']}
        def measure(audio, label, cancel=False):
            valid_audio(audio)
            prefix = captures / label
            argv = [str(binary), '-m', str(root / 'tiny.en.bin'), '-f', str(audio), '-t', '2',
                    '-ng', '-l', 'en', '-otxt', '-oj', '-of', str(prefix)]
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            start = time.monotonic(); max_rss = 0; cancelled = False; cancel_start = None
            with (captures / (label + '.log')).open('wb') as output:
                child = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT, close_fds=True, start_new_session=True)
                while child.poll() is None:
                    try:
                        for line in Path('/proc/%d/status' % child.pid).read_text().splitlines():
                            if line.startswith(('VmHWM:', 'VmRSS:')): max_rss = max(max_rss, int(line.split()[1]))
                    except FileNotFoundError: pass
                    elapsed = time.monotonic() - start
                    if (cancel and elapsed > 0.5) or elapsed > 90:
                        cancel_start = time.monotonic(); cancelled = True
                        os.killpg(child.pid, signal.SIGTERM)
                        try: child.wait(timeout=2)
                        except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
                        break
                    time.sleep(0.02)
                child.wait()
            elapsed = time.monotonic() - start; after = resource.getrusage(resource.RUSAGE_CHILDREN)
            entry = {'label': label, 'argv': argv, 'returncode': child.returncode, 'wall_seconds': elapsed,
                'cpu_seconds': after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                'max_rss_sampled_kib': max_rss, 'cancel_requested_while_running': cancelled,
                'cancel_stop_seconds': time.monotonic() - cancel_start if cancel_start else None}
            report['measurements'].append(entry)
            return prefix.with_suffix('.txt')
        first = measure(fixture, 'cold')
        measure(fixture, 'warm1'); measure(fixture, 'warm2')
        if first.exists():
            draft = first.read_text()
            (captures / 'editable-draft.txt').write_text(draft)
            (captures / 'edited-draft.txt').write_text(draft + '\nUser-edit mechanism demonstration.\n')
            report['editable_plaintext_result'] = {'available': True, 'content': draft,
                'original_sha256': sha(captures / 'editable-draft.txt'), 'edited_sha256': sha(captures / 'edited-draft.txt'),
                'limit': 'Editable backend file only; no product text editor/consent flow tested'}
        long_audio = root / 'synthetic-50s.wav'
        repeated = (result.tobytes() * (int(50 / duration) + 1))[:50 * 16000 * 2]
        write_audio(long_audio, repeated); measure(long_audio, 'cancel', cancel=True)
        invalids = []
        for name, payload in [('empty.wav', b''), ('too-long.wav', b'\0' * 61 * 16000 * 2)]:
            path = root / name; write_audio(path, payload)
            try: valid_audio(path); invalids.append({'file': name, 'withheld': False})
            except ValueError as exc: invalids.append({'file': name, 'withheld': True, 'probe_reason': str(exc)})
        report['inference_available_in_this_probe'] = all(x['returncode'] == 0 for x in report['measurements'][:3]) and first.exists() and bool(first.read_text().strip())
        report['probe_bounds'] = invalids
        report['completed'] = True
    except Exception as exc:
        report['completed'] = False; report['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        report['disk_bytes'] = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
        (captures / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    return 0 if report.get('completed') and report.get('inference_available_in_this_probe') else 1


if __name__ == '__main__':
    raise SystemExit(main())
