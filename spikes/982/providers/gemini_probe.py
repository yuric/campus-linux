#!/usr/bin/env python3
"""Bounded guest-only Gemini API-key CLI availability; no login/model execution."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import struct
import subprocess
import tarfile
import time
import urllib.request

NODE = '24.22.0'
NODE_FILE = 'node-v24.22.0-linux-arm64.tar.xz'
NODE_SHA = 'fef00bb4d36e1c50104a9775a10359beee98f162b4104dd12472c75065c6a143'
NODE_SIGNER = 'C82FA3AE1CBEDC6BE46B9360C43CEC45C17AB93C'
REGISTRY_KEY = 'SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U'
REGISTRY_DER_SHA256 = 'fb190a462123443500cbcdb6519623e7179e9f38d84ad4e9362b72d2b68b62c1'
GEMINI_SRI = 'sha512-FHrZ1NPf9QszyVMaa/BP3SsPy40ogBLnbZNWkv/PMi1Uz2zoDNMLGiBzBGmx4Bl7iLRq01K9PY/5kmloXFTpsA=='
BUDGET = 600_000_000


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=['download', 'offline'])
    p.add_argument('directory', type=Path)
    p.add_argument('--resume', action='store_true', help='preserve and resume the selected failed stage')
    args = p.parse_args()
    if platform.system() != 'Linux' or platform.machine() != 'aarch64' or os.geteuid() == 0 or os.uname().nodename != 'lima-campus-linux-d5-noble-arm64':
        raise SystemExit('unprivileged named owned arm64 guest only')
    os.umask(0o077)
    root = args.directory.absolute()
    if root.is_symlink(): raise SystemExit('refuse symlink root')
    report = {'probe_sha256': sha(Path(__file__)), 'uname': list(os.uname()), 'uid': os.getuid(),
              'operation': args.operation, 'commands': [], 'budget_bytes': BUDGET,
              'scope': 'Disposable Gemini0.64.0 availability only, no login/API call, optional native addons omitted'}
    resumed_downloads = {}
    if args.resume:
        prior_path = root/('captures-' + args.operation)
        prior = json.loads((prior_path/'receipt.json').read_text())
        if prior.get('completed') is not False or prior.get('operation') != args.operation: raise SystemExit('only matching failed stage receipts can resume')
        for item in prior.get('downloads', []):
            if Path(item['file']).name != item['file'] or sha(root/item['file']) != item['sha256']: raise SystemExit('failed download receipt inputs changed')
            resumed_downloads[item['file']] = item
        history = 'captures-' + args.operation + '-failed-' + str(time.time_ns())
        prior_path.rename(root/history)
        report['prior_failed_captures'] = history
        report['prior_probe_sha256'] = prior['probe_sha256']
    if args.operation == 'download': root.mkdir(mode=0o700, exist_ok=args.resume)
    captures = root / ('captures-' + args.operation); captures.mkdir(mode=0o700, exist_ok=False)
    def allocated():
        return sum(x.lstat().st_size for x in root.rglob('*') if x.is_file() and not x.is_symlink())
    def bound():
        size = allocated(); report['peak_file_size_sum'] = max(report.get('peak_file_size_sum', 0), size)
        if size > BUDGET - 10_000_000: raise RuntimeError('600MB combined download/expanded bound exceeded')
    def download(url, filename, limit):
        target = root / filename; size = 0
        if filename in resumed_downloads:
            item = resumed_downloads[filename]
            if item['url'] != url or item['bytes'] > limit or target.stat().st_size != item['bytes']: raise RuntimeError('resume download mismatch')
            report.setdefault('downloads', []).append(dict(item, reused_verified_download=True))
            return target
        if target.exists(): raise RuntimeError('unreceipted download already exists: ' + filename)
        with urllib.request.urlopen(url, timeout=30) as incoming, target.open('wb') as out:
            while True:
                chunk = incoming.read(1024 * 1024)
                if not chunk: break
                size += len(chunk)
                if size > limit: raise RuntimeError('download size bound: ' + filename)
                out.write(chunk); bound()
        report.setdefault('downloads', []).append({'url': url, 'file': filename, 'bytes': size, 'sha256': sha(target)})
        return target
    attempt = root/('attempt-' + args.operation + '-' + str(time.time_ns()))
    attempt.mkdir(mode=0o700)
    home = attempt/'home'; home.mkdir(mode=0o700)
    scope = attempt/'scope'; scope.mkdir(mode=0o700)
    work = attempt/'installation'; work.mkdir(mode=0o700)
    for config in ('npm-user-empty.conf', 'npm-global-empty.conf'):
        fd = os.open(home/config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600); os.close(fd)
    report['private_attempt_directory'] = str(attempt.relative_to(root))
    env = {'HOME': str(home), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
           'TMPDIR': str(home), 'npm_config_cache': str(attempt / 'cache'),
           'npm_config_userconfig': str(home/'npm-user-empty.conf'), 'npm_config_globalconfig': str(home/'npm-global-empty.conf'),
           'npm_config_update_notifier': 'false', 'npm_config_ignore_scripts': 'true',
           'npm_config_audit': 'false', 'npm_config_fund': 'false',
           'GEMINI_CLI_HOME': str(scope)}
    def command(argv, name, timeout=120):
        with (captures / (name + '.stdout')).open('wb') as out, (captures / (name + '.stderr')).open('wb') as err:
            child = subprocess.Popen(argv, env=env, cwd=work, stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
            start = time.monotonic()
            try:
                while child.poll() is None:
                    bound()
                    if time.monotonic() - start > timeout: raise RuntimeError(name + ' timeout')
                    time.sleep(.1)
            except BaseException:
                os.killpg(child.pid, signal.SIGKILL); child.wait(); raise
        report['commands'].append({'argv': argv, 'returncode': child.returncode, 'seconds': time.monotonic()-start, 'capture': name})
        bound()
        if child.returncode: raise RuntimeError(name + ' failed; inspect captures')
    try:
        if args.operation == 'download':
            base = 'https://nodejs.org/dist/v' + NODE + '/'
            checks = download(base + 'SHASUMS256.txt', 'SHASUMS256.txt', 100_000)
            sig = download(base + 'SHASUMS256.txt.sig', 'SHASUMS256.txt.sig', 10_000)
            key = download('https://raw.githubusercontent.com/nodejs/release-keys/main/keys/' + NODE_SIGNER + '.asc', 'node-key.asc', 100_000)
            gpg = root / 'gpg'; gpg.mkdir(mode=0o700, exist_ok=args.resume)
            command(['gpg', '--homedir', str(gpg), '--batch', '--import', str(key)], 'node-key-import')
            command(['gpg', '--homedir', str(gpg), '--batch', '--with-colons', '--fingerprint'], 'node-fingerprint')
            fingerprints = (captures / 'node-fingerprint.stdout').read_text()
            if ('fpr:::::::::' + NODE_SIGNER + ':') not in fingerprints: raise RuntimeError('Node signer fingerprint mismatch')
            command(['gpg', '--homedir', str(gpg), '--batch', '--status-fd', '1', '--verify', str(sig), str(checks)], 'node-signature')
            if '[GNUPG:] VALIDSIG ' + NODE_SIGNER + ' ' not in (captures / 'node-signature.stdout').read_text(): raise RuntimeError('Node signature from unexpected signer')
            if NODE_SHA + '  ' + NODE_FILE not in checks.read_text().splitlines(): raise RuntimeError('Node signed checksum differs')
            archive = download(base + NODE_FILE, NODE_FILE, 80_000_000)
            if sha(archive) != NODE_SHA: raise RuntimeError('Node archive checksum mismatch')
            meta = download('https://registry.npmjs.org/@google/gemini-cli/0.64.0', 'gemini-metadata.json', 1_000_000)
            metadata = json.loads(meta.read_text()); dist = metadata['dist']
            if metadata['version'] != '0.64.0' or metadata['name'] != '@google/gemini-cli' or dist['integrity'] != GEMINI_SRI: raise RuntimeError('Gemini pinned metadata differs')
            keys = json.loads(download('https://registry.npmjs.org/-/npm/v1/keys', 'npm-keys.json', 100_000).read_text())
            key = next(k for k in keys['keys'] if k['keyid'] == REGISTRY_KEY)
            if key.get('expires') is not None: raise RuntimeError('registry key expiry requires explicit re-evaluation')
            encoded = key['key']; der = base64.b64decode(encoded)
            # npm keyid fingerprints use the SSH public-key wire encoding, not SPKI DER.
            # Also pin the complete DER digest fetched from the official registry endpoint.
            prefix = bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d030107034200')
            if hashlib.sha256(der).hexdigest() != REGISTRY_DER_SHA256 or len(der) != 91 or not der.startswith(prefix) or der[-65] != 4:
                raise RuntimeError('registry pinned P-256 public key differs')
            ssh = b''.join(struct.pack('>I', len(part)) + part for part in (b'ecdsa-sha2-nistp256', b'nistp256', der[-65:]))
            if 'SHA256:' + base64.b64encode(hashlib.sha256(ssh).digest()).decode().rstrip('=') != REGISTRY_KEY: raise RuntimeError('registry SSH public key fingerprint mismatch')
            report['registry_key_verification'] = {'keyid': REGISTRY_KEY, 'keyid_encoding': 'SSH public-key wire format', 'spki_der_sha256': REGISTRY_DER_SHA256}
            (root / 'registry.pem').write_text('-----BEGIN PUBLIC KEY-----\n' + '\n'.join(encoded[i:i+64] for i in range(0,len(encoded),64)) + '\n-----END PUBLIC KEY-----\n')
            signature = next(s for s in dist['signatures'] if s['keyid'] == REGISTRY_KEY)
            (root / 'registry.sig').write_bytes(base64.b64decode(signature['sig']))
            (root / 'registry.message').write_text('@google/gemini-cli@0.64.0:' + GEMINI_SRI)
            command(['openssl', 'dgst', '-sha256', '-verify', str(root/'registry.pem'), '-signature', str(root/'registry.sig'), str(root/'registry.message')], 'registry-signature')
            archive = download('https://registry.npmjs.org/@google/gemini-cli/-/gemini-cli-0.64.0.tgz', 'gemini.tgz', 100_000_000)
            h = hashlib.sha512()
            with archive.open('rb') as f:
                for chunk in iter(lambda:f.read(1024*1024), b''):h.update(chunk)
            if 'sha512-' + base64.b64encode(h.digest()).decode() != GEMINI_SRI: raise RuntimeError('Gemini SRI mismatch')
            report['registry_signature_verified'] = True
            report['publisher_provenance_verified'] = False
            for name in ('gemini-package.json', 'gemini-package-lock.json'):
                shutil.copyfile(Path(__file__).with_name(name), root/name.removeprefix('gemini-'))
            report['lock_sha256'] = sha(root/'package-lock.json')
        else:
            interfaces = [s.split(':')[0].strip() for s in Path('/proc/net/dev').read_text().splitlines() if ':' in s]
            if interfaces != ['lo']: raise RuntimeError('fresh unshare --net namespace required')
            report['interfaces'] = interfaces
            prior = json.loads((root/'captures-download/receipt.json').read_text())
            if prior.get('completed') is not True or sha(root/NODE_FILE) != NODE_SHA or sha(root/'package-lock.json') != prior['lock_sha256']: raise RuntimeError('verified download receipt or inputs changed')
            for item in prior['downloads']:
                if sha(root/item['file']) != item['sha256']: raise RuntimeError('download changed: '+item['file'])
            for filename in ('package.json', 'package-lock.json'):
                if sha(root/filename) != sha(Path(__file__).with_name('gemini-' + filename)):
                    raise RuntimeError('pinned npm input changed: ' + filename)
                shutil.copyfile(root/filename, work/filename)
            node_root = root / ('node-v' + NODE + '-linux-arm64')
            reused_node = node_root.exists()
            if node_root.is_symlink(): raise RuntimeError('refuse symlink Node extraction')
            with tarfile.open(root/NODE_FILE) as archive:
                members = archive.getmembers(); total = sum(x.size for x in members)
                if total > 300_000_000 or allocated() + (0 if reused_node else total) > 400_000_000: raise RuntimeError('Node expanded bound exceeded')
                if not reused_node:
                    # Python3.12 Ubuntu24.04 data filter rejects escaping links/devices.
                    archive.extractall(root, filter='data')
                expected = set(); regular = 0; links = 0
                for item in members:
                    path = root/item.name
                    if not path.is_relative_to(node_root) or not path.resolve().is_relative_to(node_root.resolve()):
                        raise RuntimeError('Node member escapes verified extraction')
                    expected.add(path)
                    if item.isdir():
                        if path.is_symlink() or not path.is_dir(): raise RuntimeError('Node directory changed')
                    elif item.issym():
                        if not path.is_symlink() or os.readlink(path) != item.linkname: raise RuntimeError('Node symlink changed')
                        links += 1
                    elif item.isfile():
                        if path.is_symlink() or not path.is_file() or path.stat().st_size != item.size: raise RuntimeError('Node member shape changed')
                        original = hashlib.sha256()
                        with archive.extractfile(item) as stream:
                            for chunk in iter(lambda:stream.read(1024*1024), b''):original.update(chunk)
                        if sha(path) != original.hexdigest(): raise RuntimeError('Node member bytes changed')
                        regular += 1
                    else: raise RuntimeError('unsupported Node archive member')
                if set(node_root.rglob('*')) | {node_root} != expected: raise RuntimeError('unexpected files in Node extraction')
                report['node_extraction_verification'] = {'reused': reused_node, 'regular_files_verified': regular, 'symlinks_verified': links, 'archive_sha256': NODE_SHA}
            node = node_root/'bin/node'; npm = node_root/'lib/node_modules/npm/bin/npm-cli.js'
            report['node_binary_sha256'] = sha(node); report['npm_entry_sha256'] = sha(npm)
            env['PATH'] = str(node_root/'bin') + ':/usr/bin:/bin'
            command([str(node),'--version'], 'node-version')
            if (captures/'node-version.stdout').read_text().strip() != 'v' + NODE:
                raise RuntimeError('Node reported version differs from exact pin')
            command([str(node),str(npm),'--version'], 'npm-version')
            command([str(node),str(npm),'cache','add',str(root/'gemini.tgz'),'--offline','--ignore-scripts'], 'npm-cache')
            command([str(node),str(npm),'ci','--offline','--ignore-scripts','--omit=optional','--no-audit','--no-fund'], 'npm-ci')
            entry = work/'node_modules/@google/gemini-cli/bundle/gemini.js'
            report['entry_sha256'] = sha(entry)
            command([str(node),str(entry),'--version'], 'gemini-version', 30)
            if (captures/'gemini-version.stdout').read_text().strip() != '0.64.0':
                raise RuntimeError('Gemini reported version differs from exact pin')
            command([str(node),str(entry),'--help'], 'gemini-help', 30)
            if 'Usage: gemini [options] [command]' not in (captures/'gemini-help.stdout').read_text():
                raise RuntimeError('Gemini help output did not expose expected CLI entry point')
            report['installed_packages'] = sorted(str(x.relative_to(root)) for x in (work/'node_modules').glob('**/package.json'))
            report['credential_files'] = sorted(str(x.relative_to(root)) for x in scope.rglob('*') if x.is_file())
            report['not_proven'] = ['API-key authentication/model execution', 'OAuth/native keytar', 'refresh/cancel', 'two-account isolation', 'fixed update/rollback', 'publisher provenance']
        report['completed'] = True
    except Exception as exc:
        report['completed'] = False; report['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        report['final_file_size_sum'] = allocated()
        (captures/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    return 0 if report['completed'] else 1


if __name__ == '__main__': raise SystemExit(main())
