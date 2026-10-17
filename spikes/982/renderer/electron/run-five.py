#!/usr/bin/env python3
"""Five independently launched, foreground, pinned Electron candidates."""
import argparse,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('electron',type=Path)
p.add_argument('export',type=Path)
p.add_argument('frozen',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
freeze=json.loads(a.frozen.read_text())
if freeze.get('purpose')!='timing-candidate-with-motion-evidence' or not freeze.get('motion_proof_sha256'): raise SystemExit('Corrected untimed motion proof must precede timing')
a.output.mkdir(parents=True,exist_ok=False)
base=Path(__file__).resolve().parent
runs=[]
for n in range(1,6):
 out=a.output/f'run-{n}.json';runs.append(str(out))
 with (a.output/f'run-{n}.log').open('w') as log:
  subprocess.run([str(a.electron),str(base/'main.cjs'),str(a.export),str(a.frozen),str(out)],
   env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=130)
 if json.loads(out.read_text()).get('kind')!='measurement': raise SystemExit(f'Blocked run {n}; preserve all captures')
with (a.output/'summary.json').open('w') as out:
 subprocess.run([sys.executable,str(base.parent/'summarize.py'),*runs],stdout=out,check=True)
print((a.output/'summary.json').read_text())
