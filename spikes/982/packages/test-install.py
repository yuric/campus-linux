#!/usr/bin/env python3
"""Execute only the disposable polkit action. No sudo/password collection fallback.
Run allow cases with root fixture configured --mode allow; then --denied after
configuration --mode deny. A YES rule proves routing, not interactive auth.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess

HELPER = '/usr/local/libexec/campus-982-spike-install'
INSTALLED = Path('/usr/lib/campus-982-disposable-spike/helper')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def request(fixture, label, corrupt=False):
    data = (fixture / (label + '.deb')).read_bytes()
    signature = (fixture / (label + '.deb.sig')).read_bytes()
    if corrupt:
        signature = bytes([signature[0] ^ 1]) + signature[1:]
    return json.dumps({'package': base64.b64encode(data).decode(), 'signature': base64.b64encode(signature).decode()}).encode()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--denied', action='store_true')
    mode.add_argument('--prompt', action='store_true', help='one real active-session authorization, no rule; capture GUI externally')
    args = p.parse_args()
    assert os.getuid() != 0
    cases = []

    def invoke(label, payload, expect_success):
        before = sha(INSTALLED)
        result = subprocess.run(['/usr/bin/pkexec', '--disable-internal-agent', HELPER], input=payload, capture_output=True, timeout=30)
        after = sha(INSTALLED)
        passed = (result.returncode == 0) == expect_success and (expect_success or before == after)
        cases.append({'case': label, 'result': 'PASS' if passed else 'FAIL', 'exit': result.returncode, 'before_helper_sha256': before, 'after_helper_sha256': after, 'stdout': result.stdout.decode(errors='replace'), 'stderr': result.stderr.decode(errors='replace')})
        assert passed, label

    if args.prompt:
        invoke('real-polkit-prompt-valid-native-v2', request(args.fixture, 'v2'), True)
    elif args.denied:
        assert INSTALLED.is_file(), 'denied test requires existing installed fixture'
        invoke('polkit-denied-intact-install', request(args.fixture, 'v2'), False)
    else:
        invoke('valid-native-v1', request(args.fixture, 'v1'), True)
        invoke('bad-signature-intact-install', request(args.fixture, 'v2', corrupt=True), False)
        invoke('wrong-package-intact-install', request(args.fixture, 'wrong-name'), False)
        invoke('wrong-arch-intact-install', request(args.fixture, 'wrong-arch'), False)
        for label in ('maintainer-script', 'symlink-payload', 'arbitrary-path', 'setuid-helper', 'oversized-expanded-payload', 'wrong-owner', 'writable-helper'):
            if (args.fixture / (label + '.deb')).exists():
                invoke(label + '-intact-install', request(args.fixture, label), False)
            else:
                cases.append({'case': label + '-intact-install', 'result': 'BLOCKED', 'reason': 'run build-negative-fixtures.py first'})
        # Wait until privileged verifier has copied and verified the byte request,
        # then substitute the untrusted original path during the deliberate pause.
        original = args.fixture / 'v2.deb'
        contents = original.read_bytes()
        proc = subprocess.Popen(['/usr/bin/pkexec', '--disable-internal-agent', HELPER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.stdin.write(request(args.fixture, 'v2'))
        proc.stdin.close()
        first = proc.stdout.readline()
        try:
            assert json.loads(first)['phase'] == 'verified-root-owned-bytes'
            original.write_bytes(b'substituted-untrusted-download')
            rest = proc.stdout.read()
            error = proc.stderr.read()
            code = proc.wait(timeout=30)
            expected = sha(args.fixture / 'v2/usr/lib/campus-982-disposable-spike/helper')
            passed = code == 0 and sha(INSTALLED) == expected
            cases.append({'case': 'substitute-original-after-root-verification', 'result': 'PASS' if passed else 'FAIL', 'exit': code, 'installed_helper_sha256': sha(INSTALLED), 'expected_helper_sha256': expected, 'stdout': (first + rest).decode(), 'stderr': error.decode()})
            assert passed
        finally:
            original.write_bytes(contents)
    args.output.write_text(json.dumps({'scope': 'disposable root-owned staging and polkit routing; not Tauri signature or interactive prompt acceptance', 'cases': cases}, indent=2) + '\n')
    print(args.output.read_text())


if __name__ == '__main__':
    main()
