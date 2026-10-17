"""Exercise the common guest deadline and retained-child cleanup without a crash."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from watchdog import Watchdog

if os.getuid() != 0 or os.uname().nodename != 'lima-campus-linux-d5-noble-arm64':
    raise SystemExit('disposable guest root required')
result = {'kind':'non-crashing-watchdog-drill', 'crash_sent':False,
          'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [Path(__file__),Path(__file__).with_name('watchdog.py')]}}
child = subprocess.Popen(['/usr/bin/python3','-B','-I','-S','-c',
    'import subprocess,time; p=subprocess.Popen(["/usr/bin/sleep","60"]); time.sleep(60)'],
    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    env={'PATH':'/usr/bin:/bin','LANG':'C'}, close_fds=True)
watch = Watchdog(.5, lambda: None)
try:
    watch.retain(child.pid)
    try:
        while True:
            watch.tick()
            time.sleep(.02)
    except TimeoutError:
        result['deadline_exercised'] = True
    result['cleanup_confirmed'] = watch.stop()
    result['identities'] = watch.receipt()
    child.wait(timeout=1)
    result['pass'] = result['cleanup_confirmed'] and len(result['identities']) == 2
finally:
    watch.stop()
    watch.close()
    if child.poll() is None:
        child.kill()
    child.wait(timeout=1)
print(json.dumps(result,indent=2))
sys.exit(0 if result['pass'] else 1)
