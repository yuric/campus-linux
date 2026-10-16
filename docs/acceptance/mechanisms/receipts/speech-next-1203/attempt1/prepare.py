#!/usr/bin/env python3
"""Owned guest preflight and single pinned download; no build/install/cache."""
import hashlib,json,os,shutil,subprocess,urllib.request,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODEL_BYTES=77691713
MODEL_SHA='be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21'
assert os.uname().nodename=='lima-campus-linux-d5-noble-arm64'
def allocated(p):
    return sum(x.stat().st_blocks*512 for x in [p,*p.rglob('*')] if not x.is_symlink())
r={'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'monotonic':time.monotonic(),'guest_free_bytes':shutil.disk_usage('/').free}
try:
    base=ROOT.parent
    r['prior_g4_allocated_bytes']=sum(allocated(p) for p in base.iterdir() if p.name.startswith(('apport-','core-sentinel')))
    r['var_log_allocated_bytes']=int(subprocess.check_output(['du','-sk','/var/log']).split()[0])*1024
    r['g4_var_log_baseline_bytes']=114270208
    r['prior_consumed_upper_account']=r['prior_g4_allocated_bytes']+max(0,r['var_log_allocated_bytes']-r['g4_var_log_baseline_bytes'])+16*1024**2
    r['remaining_256mib']=256*1024**2-r['prior_consumed_upper_account']
    assert r['remaining_256mib']>=128*1024**2 and r['guest_free_bytes']>=2*1024**3
    binary=base/'speech-offline2/build/bin/whisper-cli'
    r['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
    assert r['binary_sha256']=='50712621452d3ab5f0d7b2a2c5dbaad5100c8d9b86538da1e1a192074b3ec2a2'
    r['cgroup_preflight']=subprocess.run(['systemd-run','--unit=campus982-speech-bound-check','--wait','--pipe','-p','User=campusqa','-p','MemoryMax=536870912','-p','MemorySwapMax=0','-p','PrivateNetwork=yes','/usr/bin/python3','-c', 'from pathlib import Path; p=Path("/sys/fs/cgroup"+Path("/proc/self/cgroup").read_text().strip().split(":")[-1]); assert (p/"memory.max").read_text().strip()=="536870912"; assert (p/"memory.swap.max").read_text().strip()=="0"; print(Path("/proc/net/dev").read_text())'],capture_output=True,text=True,timeout=20).__dict__
    assert r['cgroup_preflight']['returncode']==0
    r['url']='https://huggingface.co/ggerganov/whisper.cpp/resolve/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-tiny.bin'
    count=0; h=hashlib.sha256(); path=ROOT/'ggml-tiny.bin'
    with path.open('xb') as out, urllib.request.urlopen(r['url'],timeout=30) as stream:
        while True:
            chunk=stream.read(1024*1024)
            if not chunk:break
            count+=len(chunk)
            if count>MODEL_BYTES:raise RuntimeError('download exceeds exact pin')
            out.write(chunk);h.update(chunk)
    r['model_bytes']=count;r['model_sha256']=h.hexdigest()
    assert count==MODEL_BYTES and h.hexdigest()==MODEL_SHA
    path.chmod(0o444)
    r['completed']=True
except Exception as e:r['completed']=False;r['failure']=repr(e)
finally:
    r['allocated_bytes']=allocated(ROOT);r['guest_free_after']=shutil.disk_usage('/').free
    (ROOT/'prepare.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
raise SystemExit(0 if r['completed'] else 1)
