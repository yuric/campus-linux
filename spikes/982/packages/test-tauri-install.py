#!/usr/bin/env python3
"""Second independent root installer probe: exact Tauri minisign/version verifier.
No OpenSSL/legacy-signature fallback. Run only after explicit root fixture setup.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess

HELPER = '/usr/local/libexec/campus-982-tauri-spike-install'
INSTALLED = Path('/usr/lib/campus-982-disposable-spike/helper')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    modes = p.add_mutually_exclusive_group()
    modes.add_argument('--denied', action='store_true')
    modes.add_argument('--prompt', action='store_true')
    args = p.parse_args()
    assert os.getuid() != 0
    signatures = args.fixture / 'tauri-minisign'
    rows = []

    def payload(label='v2', siglabel=None, version=None, corrupt=False, openssl=False):
        data = (args.fixture / (label + '.deb')).read_bytes()
        if corrupt:
            data = data[:-1] + bytes([data[-1] ^ 1])
        sig = (signatures / ((siglabel or label) + '.signature.b64')).read_text()
        if openssl:
            sig = base64.b64encode((args.fixture / (label + '.deb.sig')).read_bytes()).decode()
        return json.dumps({'package': base64.b64encode(data).decode(), 'signature': sig, 'version': version or ('0.982.1' if label == 'v1' else '0.982.2')}).encode()

    def invoke(name, request, accepted):
        before = sha(INSTALLED)
        requested_version = json.loads(request)['version']
        expected = (sha(args.fixture / ('v1' if requested_version == '0.982.1' else 'v2') /
                        'usr/lib/campus-982-disposable-spike/helper') if accepted else before)
        if accepted and expected is None:
            raise RuntimeError('Missing expected fixture helper bytes')
        result = subprocess.run(['/usr/bin/pkexec', '--disable-internal-agent', HELPER], input=request, capture_output=True, timeout=45)
        after = sha(INSTALLED)
        passed = (result.returncode == 0) == accepted and expected == after
        rows.append({'case': name, 'result': 'PASS' if passed else 'FAIL', 'exit': result.returncode, 'before_helper_sha256': before, 'expected_helper_sha256': expected, 'after_helper_sha256': after, 'stdout': result.stdout.decode(errors='replace'), 'stderr': result.stderr.decode(errors='replace')})
        assert passed, name

    try:
        if args.denied:
            assert INSTALLED.is_file()
            invoke('tauri-polkit-denied-intact', payload(), False)
        elif args.prompt:
            invoke('tauri-real-polkit-prompt', payload(), True)
        else:
            invoke('tauri-native-v1-authenticated-version', payload('v1'), True)
            invoke('tauri-package-bytes-tamper-rejected', payload(corrupt=True), False)
            invoke('tauri-wrong-key-rejected', payload(siglabel='wrong-key'), False)
            invoke('tauri-unsigned-version-downgrade-rejected', payload(siglabel='unversioned'), False)
            invoke('tauri-announced-signed-version-mismatch-rejected', payload('v1', version='0.982.2'), False)
            invoke('tauri-authenticated-comment-tamper-rejected', payload(siglabel='tampered-comment', version='0.982.1'), False)
            invoke('openssl-signature-no-format-fallback', payload(openssl=True), False)
            for label in ('wrong-name', 'wrong-arch', 'maintainer-script', 'symlink-payload', 'arbitrary-path', 'setuid-helper', 'oversized-expanded-payload', 'wrong-owner', 'writable-helper'):
                if (args.fixture / (label + '.deb')).exists():
                    invoke('tauri-' + label + '-intact', payload(label), False)
                else:
                    rows.append({'case': 'tauri-' + label + '-intact', 'result': 'BLOCKED', 'reason': 'missing fixture'})
            original = args.fixture / 'v2.deb'
            data = original.read_bytes()
            proc = subprocess.Popen(['/usr/bin/pkexec', '--disable-internal-agent', HELPER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.stdin.write(payload())
            proc.stdin.close()
            first = proc.stdout.readline()
            try:
                assert json.loads(first)['phase'] == 'verified-root-owned-bytes'
                original.write_bytes(b'synthetic-substituted-download')
                rest = proc.stdout.read()
                error = proc.stderr.read()
                code = proc.wait(timeout=45)
                expected = sha(args.fixture / 'v2/usr/lib/campus-982-disposable-spike/helper')
                passed = code == 0 and sha(INSTALLED) == expected
                rows.append({'case': 'tauri-substituted-original-after-verification', 'result': 'PASS' if passed else 'FAIL', 'exit': code, 'expected_helper_sha256': expected, 'installed_helper_sha256': sha(INSTALLED), 'stdout': (first + rest).decode(), 'stderr': error.decode()})
                assert passed
            finally:
                original.write_bytes(data)
    finally:
        passed = len(rows) == (1 if args.denied or args.prompt else 17) and all(row['result'] == 'PASS' for row in rows)
        report = {'pass': passed, 'script_sha256': sha(Path(__file__)), 'scope': 'disposable polkit/root exact-byte installer using exact upstream Tauri2.14.0 verification functions and signed-version requirement; NOT full installed Tauri updater or release acceptance', 'signature_scheme': 'Tauri base64-wrapped minisign', 'require_signed_version': True, 'cases': rows}
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
