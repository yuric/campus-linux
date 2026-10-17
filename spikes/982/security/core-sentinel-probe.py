#!/usr/bin/env python3
"""Disposable arm64-only launcher proof for direction 10470. No real secrets.

Run each launcher in its own bounded transient unit. This is not a product adapter.
No crash-collector configuration is changed. All outputs contain synthetic state only.
"""
import ctypes as C
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import signal
import sys
import time

LIBC = C.CDLL(None, use_errno=True)
LIBC.syscall.restype = C.c_long
ARCH = 0xC00000B7
SETLIMIT, PRLIMIT = 164, 261
ALLOW, DENY, KILL = 0x7FFF0000, 0x50000 | errno.EPERM, 0x80000000


class Insn(C.Structure):
    _fields_ = [('code', C.c_ushort), ('jt', C.c_ubyte),
                ('jf', C.c_ubyte), ('k', C.c_uint32)]


class Program(C.Structure):
    _fields_ = [('length', C.c_ushort), ('instructions', C.POINTER(Insn))]


class Limits(C.Structure):
    _fields_ = [('soft', C.c_uint64), ('hard', C.c_uint64)]


def policy(expected_arch=ARCH):
    # seccomp_data: nr=0, arch=4, args=16. Resource arguments are unsigned int.
    # prlimit64's new_limit pointer is args[2]: both halves must be zero for a query.
    return [
        (0x20, 0, 0, 4),                  # 0 load architecture
        (0x15, 1, 0, expected_arch),      # 1 supported -> 3
        (0x06, 0, 0, KILL),              # 2 reject foreign ABI
        (0x20, 0, 0, 0),                 # 3 syscall number
        (0x15, 0, 3, SETLIMIT),          # 4 setrlimit -> 5, otherwise 8
        (0x20, 0, 0, 16),                # 5 resource low32
        (0x15, 8, 9, resource.RLIMIT_CORE), # 6 core ->15, noncore ->16
        (0x06, 0, 0, KILL),              # 7 unreachable
        (0x15, 0, 7, PRLIMIT),           # 8 prlimit ->9, other ->16
        (0x20, 0, 0, 24),                # 9 resource low32
        (0x15, 0, 5, resource.RLIMIT_CORE), # 10 noncore ->16
        (0x20, 0, 0, 32),                # 11 new_limit low32
        (0x15, 0, 2, 0),                 # 12 nonzero ->15
        (0x20, 0, 0, 36),                # 13 new_limit high32
        (0x15, 1, 0, 0),                 # 14 zero ->16, nonzero ->15
        (0x06, 0, 0, DENY),              # 15 reject mutation
        (0x06, 0, 0, ALLOW),             # 16 allow
    ]


def emit(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def snapshot(label):
    tail = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines())
    return {'label': label, 'pid': os.getpid(), 'ppid': os.getppid(),
            'start_ticks': int(tail[19]), 'sid': os.getsid(0),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'cgroup': Path('/proc/self/cgroup').read_text().strip(),
            'core_limit': resource.getrlimit(resource.RLIMIT_CORE),
            'dumpable': LIBC.prctl(3, 0, 0, 0, 0),
            'no_new_privs': status['NoNewPrivs'].strip(),
            'seccomp': status['Seccomp'].strip(),
            'seccomp_filters': status.get('Seccomp_filters', '').strip(),
            'marker_admitted': 'CAMPUS982_SYNTHETIC' in os.environ,
            'monotonic': time.monotonic()}


def install(mode):
    if platform.machine() != 'aarch64' or sys.byteorder != 'little':
        raise RuntimeError('unsupported ABI; no secret or exec')
    if mode == 'fail-limit':
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (1, 1))
    if resource.getrlimit(resource.RLIMIT_CORE) != (1, 1):
        raise RuntimeError('limit readback failed')
    if mode in {'bare', 'sentinel-abort'}:
        return
    if LIBC.prctl(38, 1, 0, 0, 0):
        raise OSError(C.get_errno(), 'no_new_privs failed')
    instructions = policy(0 if mode == 'foreign-abi' else ARCH)
    arr = (Insn * len(instructions))(*(Insn(*v) for v in instructions))
    prog = Program(0 if mode == 'fail-filter' else len(instructions), arr)
    if LIBC.prctl(22, 2, C.byref(prog), 0, 0):
        raise OSError(C.get_errno(), 'filter installation failed')
    if LIBC.prctl(21, 0, 0, 0, 0) != 2 or resource.getrlimit(resource.RLIMIT_CORE) != (1, 1):
        raise RuntimeError('filter/limit readback failed')


def raw(nr, *args):
    C.set_errno(0)
    result = LIBC.syscall(C.c_long(nr), *args)
    return {'return': result, 'errno': C.get_errno()}


def verify_mutations():
    checks = []
    for nr in (SETLIMIT, PRLIMIT):
        for value in (0, 1, (1 << 64) - 1):
            lim = Limits(value, value)
            # Include a high-word alias: the kernel resource argument is unsigned int.
            for res in (resource.RLIMIT_CORE, (1 << 32) | resource.RLIMIT_CORE):
                args = (C.c_ulonglong(res), C.byref(lim)) if nr == SETLIMIT else (
                    C.c_long(0), C.c_ulonglong(res), C.byref(lim), C.c_void_p())
                observed = raw(nr, *args)
                checks.append({'syscall': nr, 'resource': res, 'value': value, **observed})
                assert observed == {'return': -1, 'errno': errno.EPERM}, checks[-1]
    # A nonnull pointer whose low word is zero must still be rejected before dereference.
    ptr = raw(PRLIMIT, C.c_long(0), C.c_long(resource.RLIMIT_CORE), C.c_void_p(1 << 32), C.c_void_p())
    assert ptr == {'return': -1, 'errno': errno.EPERM}, ptr
    query = Limits()
    q = raw(PRLIMIT, C.c_long(0), C.c_long(resource.RLIMIT_CORE), C.c_void_p(), C.byref(query))
    assert q['return'] == 0 and (query.soft, query.hard) == (1, 1)
    other = resource.getrlimit(resource.RLIMIT_NOFILE)
    lim = Limits(*other)
    noncore = [raw(SETLIMIT, C.c_long(resource.RLIMIT_NOFILE), C.byref(lim)),
               raw(PRLIMIT, C.c_long(0), C.c_long(resource.RLIMIT_NOFILE), C.byref(lim), C.byref(query))]
    assert all(v['return'] == 0 for v in noncore), noncore
    assert resource.getrlimit(resource.RLIMIT_CORE) == (1, 1)
    emit({'mutations': checks, 'high_pointer': ptr, 'core_query': q, 'noncore_same_value': noncore})


def fixture(mode, depth):
    state = snapshot('after-exec-depth-' + str(depth)); emit(state)
    assert state['dumpable'] == 1 and tuple(state['core_limit']) == (1, 1)
    if mode == 'bare':
        resource.setrlimit(resource.RLIMIT_CORE, (0, 1))
        emit({'bare_lowered_soft_to_zero': resource.getrlimit(resource.RLIMIT_CORE) == (0, 1)})
        return
    if mode != 'sentinel-abort':
        verify_mutations()
    if mode in {'descendants', 'descendants-abort'} and depth < 2:
        pid = os.fork()
        if pid == 0:
            if depth == 1:
                os.setsid()
            os.execve('/usr/bin/python3', ['/usr/bin/python3', '-I', '-S', __file__, 'fixture', mode, str(depth + 1)], dict(os.environ))
        _, status = os.waitpid(pid, 0)
        emit({'waited_pid': pid, 'wait_status': status})
        expected = signal.SIGABRT if mode == 'descendants-abort' and depth == 1 else 0
        assert status == expected, (status, expected)
    if mode in {'sentinel-abort', 'filtered-abort'} or (mode == 'descendants-abort' and depth == 2):
        # Only after the actual kernel emitted its exact-PID sentinel refusal in the
        # foreign-ABI negative control. A positive unlimited/zero-core dump is not run.
        assert resource.getrlimit(resource.RLIMIT_CORE) == (1, 1)
        assert LIBC.prctl(3, 0, 0, 0, 0) == 1
        emit({'abort_pid': os.getpid(), 'state': snapshot('immediately-before-abort')})
        os.kill(os.getpid(), signal.SIGABRT)


def main():
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64' or os.getuid() != 1000:
        raise SystemExit('owned guest and campusqa UID required')
    if sys.argv[1] == 'fixture':
        return fixture(sys.argv[2], int(sys.argv[3]))
    mode = sys.argv[1]
    if mode not in {'bare', 'filtered', 'descendants', 'fail-limit', 'fail-filter', 'foreign-abi',
                    'sentinel-abort', 'filtered-abort', 'descendants-abort'}:
        raise SystemExit('unknown disposable case')
    assert 'CAMPUS982_SYNTHETIC' not in os.environ
    emit({'case': mode, 'launcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'initial': snapshot('before-secret')})
    try:
        install(mode)
    except (OSError, ValueError, RuntimeError) as exc:
        emit({'refused_before_secret': True, 'provider_execed': False,
              'marker_admitted': False, 'error_type': type(exc).__name__, 'error': str(exc)})
        return 23
    if mode in {'fail-limit', 'fail-filter', 'foreign-abi'}:
        raise RuntimeError('negative control unexpectedly admitted')
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'HOME': '/home/campusqa',
           'CAMPUS982_SYNTHETIC': 'public-fixture-marker-10470'}
    os.execve('/usr/bin/python3', ['/usr/bin/python3', '-I', '-S', __file__, 'fixture', mode, '0'], env)


if __name__ == '__main__':
    sys.exit(main())
