#!/usr/bin/env python3
"""Freeze a successful actual Electron preflight before fallback measurement."""
import argparse,datetime,hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--motion-proof',type=Path,help='Corrected untimed proof; omission makes diagnostic-only freeze')
p.add_argument('preflight',type=Path)
p.add_argument('environment',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists(): raise SystemExit('Preserve previous freeze')
raw=json.loads(a.preflight.read_text())
env=json.loads(a.environment.read_text())
if raw.get('kind')!='preflight' or raw.get('errors'): raise SystemExit('Successful actual preflight required')
if raw['runtime']['electron']!='44.8.0' or 'llvmpipe' not in raw['renderer'].lower(): raise SystemExit('Pinned actual software runtime required')
base=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(base))
from motion_evidence import verified_motion
protocol=base.parents[2]/'docs/acceptance/visual-protocol.json'
digest=lambda file:hashlib.sha256(file.read_bytes()).hexdigest()
for file,value in raw['input_hashes'].items():
 if file!='executable' and digest(base/file)!=value: raise SystemExit('Harness bytes differ from successful preflight')
required=('kernel','architecture','os','session','mesa','llvm','graphics')
if any(not env.get(k) for k in required): raise SystemExit('Observe complete actual guest environment')
frozen=dict(purpose='untimed-diagnostic-only',zoom_units='absolute producer camera zoom',driver_revision='absolute-zoom-v3',initial_zoom=1,initial_zoom_tolerance=1e-5,projection_observer_during_timing=False,environment=env,preflight_sha256=digest(a.preflight),runtime=raw['runtime'],input_hashes=raw['input_hashes'],
 rendering_env=raw['rendering_env'],webgl_api_renderer=raw['renderer'],native_gpu=raw['native_gpu'],
 protocol_sha256=digest(protocol),frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 repeats=5,duration_seconds=60,warmup_seconds=30,p95_ms_max=33.3,viewport=[1440,900],device_scale=1,
 render_scale=1,appearance='light',projects=12,agents=48,tasks=180,seed=98120261016)
if a.motion_proof:
 proof,proof_digest=verified_motion(a.motion_proof)
 if proof.get('input_hashes')!=raw['input_hashes'] or proof.get('runtime')!=raw['runtime'] or proof.get('rendering_env')!=raw['rendering_env']: raise SystemExit('Motion proof candidate differs from preflight')
 frozen.update(purpose='timing-candidate-with-motion-evidence',motion_proof_sha256=proof_digest)
a.output.write_text(json.dumps(frozen,indent=2)+'\n')
print(digest(a.output))
