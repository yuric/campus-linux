"""Resume only the originally assigned negative arm after same-report recovery."""
import hashlib
import json
from pathlib import Path
import shutil
import time
from host import call, HERE, OUT, GUEST, MIB

recovery=json.loads((OUT/'reinspection.json').read_text())
assert recovery['pass'] and recovery['owned_report_removed'] and recovery['report_binding_verified']
assert not recovery['crash_sent']
original=(OUT/'positive.json').read_bytes()
assert hashlib.sha256(original).hexdigest()==recovery['original_receipt_sha256']
assert call(['cat',GUEST+'/positive.json'])==original
# Retain original producing code before the corrected negative revision.
call(['mkdir',GUEST+'/source-pair1'])
call(['cp',GUEST+'/pair.py',GUEST+'/source-pair1/pair.py'])
call(['tee',GUEST+'/pair.py'],(HERE/'pair.py').read_bytes())
call(['tee',GUEST+'/reinspection.json'],(OUT/'reinspection.json').read_bytes())
call(['tee',GUEST+'/resume_negative.py'],Path(__file__).read_bytes())
assert not call(['find',GUEST,'-maxdepth','1','-name','negative.json']).strip()
disk=Path.home()/'.lima/campus-linux-d5-noble-arm64/disk'
image_start=disk.stat().st_blocks*512
base=json.loads((OUT/'allocation-baseline.json').read_text())['consumed_bytes']
r={'kind':'negative-only-after-confirmed-positive-cleanup','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
   'pair_sha256':hashlib.sha256((HERE/'pair.py').read_bytes()).hexdigest(),
   'reinspection_sha256':hashlib.sha256((OUT/'reinspection.json').read_bytes()).hexdigest(),'samples':[]}
try:
    assert shutil.disk_usage('.').free>=20*1024**3
    call(['touch',GUEST+'/heartbeat'])
    unit='campus982-full-monitor-1213-negative'
    call(['systemd-run','--unit='+unit,'--collect','-p','MemoryMax=128M','-p','MemorySwapMax=0','-p','TasksMax=16',
          '-p','UMask=0077','-p','WorkingDirectory='+GUEST,'/usr/bin/python3','-B',GUEST+'/pair.py','negative'])
    end=time.monotonic()+85
    while True:
        free=shutil.disk_usage('.').free;growth=max(0,disk.stat().st_blocks*512-image_start)
        local=sum(p.stat().st_blocks*512 for p in OUT.rglob('*') if p.is_file())
        r['samples'].append(dict(monotonic=time.monotonic(),host_free=free,image_growth=growth,local_allocated=local))
        if free<20*1024**3 or base+growth+local>=192*MIB or time.monotonic()>end:
            call(['touch',GUEST+'/STOP']);raise RuntimeError('host requested bounded stop')
        call(['touch',GUEST+'/heartbeat'])
        state=call(['systemctl','show',unit,'-p','ActiveState','--value']).decode().strip()
        if state in ('inactive','failed'):break
        time.sleep(.5)
    raw=call(['cat',GUEST+'/negative.json']);(OUT/'negative.json').write_bytes(raw)
    value=json.loads(raw);r['pass']=value['runtime_pass'] and value['cleanup_confirmed']
except Exception as exc:r.update(error=str(exc),pass_=False)
finally:
    (OUT/'host-negative.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
