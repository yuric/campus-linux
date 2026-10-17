import subprocess,json,hashlib,shutil,datetime
from pathlib import Path
base=Path('spikes/982/security'); out=Path('docs/acceptance/mechanisms/receipts/apport-full-1213')
prefix=['/opt/homebrew/bin/limactl','shell','campus-linux-d5-noble-arm64','sudo']
guest='/home/campusqa/spike982/apport-full-1213'
def run(args,data=None):
 assert shutil.disk_usage('.').free>=20*1024**3
 p=subprocess.run(prefix+args,input=data,capture_output=True,timeout=35)
 if p.returncode:raise RuntimeError(p.stderr.decode()[:1000])
 return p.stdout
run(['mkdir','-m','755',guest])
for name in ['watchdog.py','drill.py','metadata.py']:
 data=(base/'full-report'/name).read_bytes();run(['tee',guest+'/'+name],data)
for name in ['apport-positive-preflight.py','apport-activation-launch.py','core-sentinel-probe.py']:
 run(['tee',guest+'/'+name],(base/name).read_bytes())
for name in ['drill','metadata','apport-positive-preflight']:
 p=subprocess.run(prefix+['/usr/bin/python3','-B',guest+'/'+name+'.py'],capture_output=True,timeout=35)
 (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
 x=json.loads(p.stdout);print(name,json.dumps(x))
 if p.returncode or (name=='metadata' and not x.get('preflight_pass')) or (name=='drill' and not x.get('pass')):break
