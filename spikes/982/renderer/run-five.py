#!/usr/bin/env python3
"""Five fresh foreground host processes; preserve every run, never retry/drop slow runs."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--native-gpu-receipt',type=Path,required=True)
p.add_argument('export',type=Path)
p.add_argument('frozen',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
a.output.mkdir(exist_ok=False,parents=True)
base=Path(__file__).resolve().parent
freeze=json.loads(a.frozen.read_text())
for filename,key in [('run-five.py','run_five_sha256'),('summarize.py','summarizer_sha256')]:
    if hashlib.sha256((base/filename).read_bytes()).hexdigest()!=freeze[key]: raise SystemExit('Automation differs from frozen bytes')
env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1')
runs=[]
for n in range(1,6):
    out=a.output/f'run-{n}.json'
    runs.append(str(out))
    with (a.output/f'run-{n}.log').open('w') as log:
        subprocess.run([sys.executable,str(base/'run-webkit.py'),'--native-gpu-receipt',str(a.native_gpu_receipt),'--compositing-policy',freeze['compositing_policy'],str(a.export),str(a.frozen),str(out)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=125,check=True)
    raw=json.loads(out.read_text())
    if raw.get('kind')!='measurement':
        raise SystemExit(f'Run {n} blocked: retain receipt and correct preflight before another five-run series')
with (a.output/'summary.json').open('w') as summary:
    subprocess.run([sys.executable,str(base/'summarize.py'),*runs],stdout=summary,check=True)
print((a.output/'summary.json').read_text())
