#!/usr/bin/env python3
"""Root supervisor uses a locale receipt actually produced through GNOME, not SSH locale."""
import hashlib,json,os,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent
assert os.getuid()==0 and os.uname().nodename=='lima-campus-linux-d5-noble-arm64'
s=json.loads((root/'session.json').read_text())
assert 'Active=yes' in s['session'] and 'Service=gdm-password' in s['session'] and 'Remote=no' in s['session']
unit='campus982-speech-1203-run4'
argv=['systemd-run','--unit='+unit,'--wait','--pipe','-p','User=campusqa','-p','MemoryMax=536870912','-p','MemorySwapMax=0','-p','TasksMax=32','-p','PrivateNetwork=yes','-p','NoNewPrivileges=yes','-p','RuntimeMaxSec=120','-p','LimitCORE=0','-p','KillMode=control-group']
for k,v in s['environment'].items():
    assert k in ('LANG','LC_ALL','LC_MESSAGES','LC_CTYPE') and '\n' not in v
    argv+=['--setenv='+k+'='+v]
argv+=['/usr/bin/python3','-B',str(root/'runner.py')]
r={'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')},'session_receipt_sha256':hashlib.sha256((root/'session.json').read_bytes()).hexdigest(),'argv':argv,'start_monotonic':time.monotonic(),'launch_boundary':'Locale observed inside real graphical launcher; privileged supervisor copies only allowlisted locale values into isolated system service. Inference process is not itself a graphical session child.'}
p=subprocess.run(argv,capture_output=True,text=True,timeout=135)
r.update(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,end_monotonic=time.monotonic())
r['cgroup_absent']=not Path('/sys/fs/cgroup/system.slice/'+unit+'.service').exists()
(root/'launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
