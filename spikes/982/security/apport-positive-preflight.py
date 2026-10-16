#!/usr/bin/env python3
"""Read-only identity/storage preflight for task direction 10500; never crashes.

Run via the owned Lima control connection as root, with Python -B. Outputs only
public package identities, hashes and allocation metadata; no crash contents.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


EXPECTED = {
    '/usr/share/apport/apport': ('apport', '1b8b5e2c53e8970dd2f47c9a0892030d1ebad57cae1f7242c43a6252f1f6dff2'),
    '/usr/lib/python3/dist-packages/apport/report.py': ('python3-apport', '8b8aefab8abf44254542e63381de7fc517ab91ad3caa9e1febe89d172c6b56c4'),
    '/usr/lib/python3/dist-packages/problem_report.py': ('python3-problem-report', '560649a7bf377fa671199aa86e7164b2710f6f80224cf4b63ff44e3a4911b3ad'),
    '/usr/bin/sleep': ('coreutils', None),
}


def main():
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64' or os.getuid() != 0:
        raise SystemExit('owned Lima guest root control connection required')
    files = {}
    for name, (package, expected_sha) in EXPECTED.items():
        path = Path(name)
        data = path.read_bytes()
        manifest = Path('/var/lib/dpkg/info') / (package + '.md5sums')
        expected_md5 = [line.split()[0] for line in manifest.read_text().splitlines()
                        if line.split(maxsplit=1)[-1] == name.lstrip('/')]
        md5 = hashlib.md5(data).hexdigest()
        sha = hashlib.sha256(data).hexdigest()
        files[name] = {'sha256': sha, 'bytes': len(data), 'canonical_path': str(path.resolve()),
                       'package': package, 'package_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
                       'package_md5_matches': expected_md5 == [md5],
                       'source_sha256_matches': sha == expected_sha if expected_sha else None}
    prospective = {}
    for suffix in ('.crash', '.upload', '.uploaded'):
        path = Path('/var/crash/_usr_bin_sleep.1000' + suffix)
        prospective[str(path)] = {'exists_or_symlink': os.path.lexists(path)}
    log_bytes = log_blocks = 0
    # Conservative whole-log-tree accounting; names and contents are not exported.
    # This is an upper bound including preexisting data, not attributed growth.
    for root, dirs, names in os.walk('/var/log', followlinks=False):
        for name in names:
            path = Path(root) / name
            if not path.is_symlink():
                st = path.stat()
                log_bytes += st.st_size
                log_blocks += st.st_blocks * 512
    free = shutil.disk_usage('/var/crash').free
    result = {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'kind': 'read-only-preflight-not-crash-test', 'direction': 10500,
        'uname': list(os.uname()), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'guest_free_bytes': free, 'plan_guest_20gib_predicate': free >= 20 * 1024**3,
        'files': files, 'prospective_paths': prospective,
        'core_pattern': Path('/proc/sys/kernel/core_pattern').read_text().strip(),
        'core_pipe_limit': Path('/proc/sys/kernel/core_pipe_limit').read_text().strip(),
        'packages': subprocess.check_output(['dpkg-query', '-W', '-f=${binary:Package} ${Version} ${Architecture}\n',
                    'apport', 'python3-apport', 'python3-problem-report', 'coreutils',
                    'linux-image-' + os.uname().release], text=True, timeout=5),
        'all_var_log_logical_bytes_upper_bound': log_bytes,
        'all_var_log_allocated_bytes_upper_bound': log_blocks,
        'kernel_source_directories': sorted(p.name for p in Path('/usr/src').iterdir()),
        'limits': ['No ELF runtime, metadata-size, kernel-note bound or collector positive is proved by this preflight.',
                   'Package MD5 checks compare the installed package database; they are not independent publisher authentication.',
                   'The extra guest 20 GiB predicate in the supplied plan requires coordinator clarification if false.'],
        'crash_launched': False,
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
