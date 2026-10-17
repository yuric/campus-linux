"""Host accounting and heartbeat; guest monitor, not SSH, owns cleanup."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'docs/acceptance/mechanisms/receipts/apport-full-1213'
GUEST='/home/campusqa/spike982/apport-full-1213'
PREFIX=['/opt/homebrew/bin/limactl','shell','campus-linux-d5-noble-arm64','sudo']
MIB=1024**2

def call(args,data=None,timeout=10):
    p=subprocess.run(PREFIX+args,input=data,capture_output=True,timeout=timeout)
    if len(p.stdout)+len(p.stderr)>MIB:raise RuntimeError('host command output cap')
    if p.returncode:raise RuntimeError('guest command failed: '+p.stderr.decode()[:1000])
    return p.stdout


def main():
    record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'samples':[],
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}}
    disk=Path.home()/'.lima/campus-linux-d5-noble-arm64/disk'
    image_start=disk.stat().st_blocks*512
    source_files=list(HERE.glob('*.py'))+[HERE.parent/name for name in
        ('apport-activation-pair.py','apport-activation-launch.py','core-sentinel-probe.py','apport-positive-preflight.py')]
    # Prior drill/metadata receipts are collected. Do not overwrite executed sources.
    for p in source_files:
        if p.name in ('watchdog.py','metadata.py','drill.py','apport-activation-launch.py','core-sentinel-probe.py','apport-positive-preflight.py'):
            actual=call(['sha256sum',GUEST+'/'+p.name]).decode().split()[0]
            if actual!=hashlib.sha256(p.read_bytes()).hexdigest():raise RuntimeError('deployed preflight source changed')
        else:
            call(['/usr/bin/python3','-B','-c','import sys; f=open(sys.argv[1],"xb"); f.write(sys.stdin.buffer.read(1048576)); f.close()',GUEST+'/'+p.name],p.read_bytes())
    accounting=call(['/usr/bin/python3','-B','-c',r'''
import json,os,stat
from pathlib import Path
def alloc(root):
 total=0
 for parent,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if not Path(parent,d).is_symlink()]
  for name in files:
   p=Path(parent,name);s=p.lstat()
   if stat.S_ISREG(s.st_mode):total+=s.st_blocks*512
 return total
roots=[p for p in Path('/home/campusqa/spike982').iterdir() if any(s in p.name for s in ['sentinel','apport','speech-next']) and p.name!='apport-full-1213']
owned={str(p):alloc(p) for p in roots};logs=alloc('/var/log')
r={'owned':owned,'var_log_allocated':logs,'historical_log_baseline':114270208,'prior_overhead_reserve':16*1024**2}
r['consumed_bytes']=sum(owned.values())+max(0,logs-114270208)+16*1024**2
r['remaining_bytes']=256*1024**2-r['consumed_bytes'];r['new_explicit_reservation']=64*1024**2
assert r['remaining_bytes']>=r['new_explicit_reservation']
print(json.dumps(r,indent=2))
'''])
    (OUT/'allocation-baseline.json').write_bytes(accounting)
    call(['tee',GUEST+'/allocation-baseline.json'],accounting)
    base=json.loads(accounting)['consumed_bytes'];record['baseline_consumed_bytes']=base
    try:
        for arm in ('positive','negative'):
            if shutil.disk_usage('.').free<20*1024**3:raise RuntimeError('host floor before arm')
            call(['touch',GUEST+'/heartbeat'])
            unit='campus982-full-monitor-1213-'+arm
            call(['systemd-run','--unit='+unit,'--collect','-p','MemoryMax=128M','-p','MemorySwapMax=0',
                  '-p','TasksMax=16','-p','UMask=0077','-p','WorkingDirectory='+GUEST,
                  '/usr/bin/python3','-B',GUEST+'/pair.py',arm])
            deadline=time.monotonic()+85
            while True:
                free=shutil.disk_usage('.').free;image=disk.stat().st_blocks*512
                local=sum(p.stat().st_blocks*512 for p in OUT.rglob('*') if p.is_file())
                sample=dict(arm=arm,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            host_free=free,image_positive_delta=max(0,image-image_start),local_allocated=local)
                record['samples'].append(sample)
                if free<20*1024**3 or base+max(0,image-image_start)+local>=192*MIB or local>=4*MIB or time.monotonic()>deadline:
                    call(['touch',GUEST+'/STOP']);raise RuntimeError('host early-stop threshold/deadline; guest requested cleanup')
                call(['touch',GUEST+'/heartbeat'])
                state=call(['systemctl','show',unit,'-p','ActiveState','--value']).decode().strip()
                if state in ('inactive','failed'):
                    break
                time.sleep(.5)
            raw=call(['cat',GUEST+'/'+arm+'.json']);(OUT/(arm+'.json')).write_bytes(raw)
            value=json.loads(raw)
            if not value.get('runtime_pass') or not value.get('cleanup_confirmed'):
                raise RuntimeError(arm+' failed; no next arm')
        record['matched_pair_pass']=True
    except Exception as exc:
        record.update(matched_pair_pass=False,error=str(exc))
    finally:
        record['host_free_final']=shutil.disk_usage('.').free
        record['image_allocated_before']=image_start;record['image_allocated_after']=disk.stat().st_blocks*512
        (OUT/'host-pair.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='samples'},indent=2))
    return 0 if record.get('matched_pair_pass') else 1

if __name__=='__main__':sys.exit(main())
