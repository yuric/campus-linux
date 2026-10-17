#!/usr/bin/env python3
"""Synthetic sleep launcher shared by the matched SIGQUIT arms; guest only."""
import ctypes
import importlib.util
import os
from pathlib import Path
import resource
import sys

if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64' or os.getuid() != 1000:
    raise SystemExit('owned guest and fixture UID required')
arm = sys.argv[1]
if arm not in ('positive', 'negative'):
    raise SystemExit('unknown arm')
spec = importlib.util.spec_from_file_location('sentinel', Path(__file__).with_name('core-sentinel-probe.py'))
sentinel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentinel)
libc = ctypes.CDLL(None, use_errno=True)
libc.execve.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p)]
argv = (ctypes.c_char_p * 3)(b'/usr/bin/sleep', b'90', None)
env = (ctypes.c_char_p * 4)(b'LANG=C', b'PATH=/usr/bin:/bin',
                           b'CAMPUS982_SYNTHETIC=public-apport-activation-1196', None)
with open('/proc/self/coredump_filter', 'w') as stream:
    stream.write('1')
# All potentially allocating setup precedes the small ELF address-space limit.
if arm == 'negative':
    sentinel.install('filtered')
else:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.closerange(3, 1024)
resource.setrlimit(resource.RLIMIT_AS, (8388608, 8388608))
libc.execve(b'/usr/bin/sleep', argv, env)
os._exit(24)
