#!/usr/bin/env python3
"""Collect only this public synthetic probe; never transfer model/audio bytes."""
import base64,datetime,hashlib,json,subprocess,sys,shutil
from pathlib import Path
OUT=Path('docs/acceptance/mechanisms/receipts/speech-next-1203')
script=r'''
import base64,hashlib,json,shutil,subprocess
from pathlib import Path
p=Path('/home/campusqa/spike982/speech-next-1203')
r={'files':{},'allocated_bytes':sum(x.stat().st_blocks*512 for x in [p,*p.rglob('*')]),'guest_free_bytes':shutil.disk_usage('/').free,'var_log_allocated_bytes':int(subprocess.check_output(['du','-sk','/var/log']).split()[0])*1024,'audio_hashes':{str(x.relative_to(p)):{'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in p.rglob('*.wav')}}
for x in p.rglob('*'):
 if x.is_file() and x.suffix in ('.json','.py','.stdout','.stderr'):
  data=x.read_bytes();assert len(data)<65536
  r['files'][str(x.relative_to(p))]=base64.b64encode(data).decode()
r['output_allocated_bytes']=r['allocated_bytes']-(p/'ggml-tiny.bin').stat().st_blocks*512
r['cgroups_absent']={n:not Path('/sys/fs/cgroup/system.slice/'+n+'.service').exists() for n in ['campus982-speech-preflight','campus982-speech-bound-check','campus982-speech-1203','campus982-speech-1203-run2','campus982-speech-1203-run3','campus982-speech-1203-run4']}
print(json.dumps(r))
'''
p=subprocess.run(['limactl','shell','campus-linux-d5-noble-arm64','sudo','python3','-'],input=script,text=True,capture_output=True,check=True)
r=json.loads(p.stdout);redactions=[]
for name,payload in r.pop('files').items():
    data=base64.b64decode(payload)
    # Preserve guest originals. Publish a declared derived copy excluding public
    # upstream maintainer emails/unrelated module descriptions, not probe failures.
    if name=='attempt3/receipt.json':
        original_hash=hashlib.sha256(data).hexdigest();obj=json.loads(data)
        for c in obj['commands']:
            if c['argv']==['pactl','--format=json','list','modules']:
                c['stdout']='[public upstream module author metadata omitted in this publication copy]'
        data=(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode()
        redactions.append({'path':name,'original_sha256':original_hash,'published_sha256':hashlib.sha256(data).hexdigest(),'reason':'Unrelated public upstream module-author metadata; original guest receipt preserved; failure unchanged.'})
    dest=OUT/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
r['publication_redactions']=redactions;r['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
r['host_free_bytes']=shutil.disk_usage('.').free
image=Path.home()/'.lima/campus-linux-d5-noble-arm64/disk';r['disk_apparent_bytes']=image.stat().st_size;r['disk_allocated_bytes']=image.stat().st_blocks*512
r['collector_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(OUT/'collection.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
