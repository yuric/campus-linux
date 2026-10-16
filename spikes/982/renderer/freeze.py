#!/usr/bin/env python3
"""Create immutable-input receipt before first run; never fills unobserved environment facts."""
import argparse,datetime,hashlib,json
from pathlib import Path
from native_evidence import native_receipt
from motion_evidence import verified_motion
p=argparse.ArgumentParser()
p.add_argument('--native-gpu-receipt',type=Path,required=True)
p.add_argument('--motion-proof',type=Path,help='Successful corrected untimed proof; omission creates diagnostic-only freeze')
p.add_argument('environment',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists(): raise SystemExit('Freeze already exists; do not overwrite')
env=json.loads(a.environment.read_text())
required=('webkit','mesa','llvm','kernel','architecture','os','session','graphics','webgl_api_renderer','compositing_policy')
if any(not isinstance(env.get(k),str) or not env[k].strip() for k in required):
    raise SystemExit('Observe every required environment fact before freeze')
if not isinstance(env.get('rendering_env'),dict) or env['rendering_env'].get('LIBGL_ALWAYS_SOFTWARE')!='1':
    raise SystemExit('Copy actual rendering_env from untimed preflight')
base=Path(__file__).resolve().parent
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((base/'desktop-producer-manifest.json').read_text())
native=native_receipt(a.native_gpu_receipt)
if env['webgl_api_renderer']!=native['webgl_api_renderer']: raise SystemExit('WebGL API identity differs from reviewed source')
frozen=dict(env,purpose='untimed-diagnostic-only',zoom_units='absolute producer camera zoom',driver_revision='absolute-zoom-v3',initial_zoom=1,initial_zoom_tolerance=1e-5,projection_observer_during_timing=False,motion_evidence_code_sha256=digest(base/'motion_evidence.py'),native_evidence=native,native_evidence_code_sha256=digest(base/'native_evidence.py'),producer_sha=manifest['source'],manifest_sha256=digest(base/'desktop-producer-manifest.json'),
            fixture_sha256=digest(base/'fixture.json'),measure_sha256=digest(base/'measure.js'),
            runner_sha256=digest(base/'run-webkit.py'),run_five_sha256=digest(base/'run-five.py'),summarizer_sha256=digest(base/'summarize.py'),protocol_sha256=digest(base.parents[2]/'docs/acceptance/visual-protocol.json'),
            seed=98120261016,repeats=5,duration_seconds=60,warmup_seconds=30,p95_ms_max=33.3,
            viewport=[1440,900],device_scale=1,render_scale=1,appearance='light',
            projects=12,agents=48,tasks=180,frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
if a.motion_proof:
    raw,proof_digest=verified_motion(a.motion_proof)
    for key in ('measure_sha256','runner_sha256','fixture_sha256','manifest_sha256','protocol_sha256','native_evidence_code_sha256','motion_evidence_code_sha256'):
        if raw['freeze'].get(key)!=frozen[key]: raise SystemExit('Motion proof inputs differ: '+key)
    if raw.get('native_evidence')!=native or raw.get('rendering_env')!=env['rendering_env']: raise SystemExit('Motion proof environment differs')
    if raw.get('compositing_policy')!=env['compositing_policy']: raise SystemExit('Motion proof compositing policy differs')
    frozen.update(purpose='timing-candidate-with-motion-evidence',motion_proof_sha256=proof_digest)
a.output.write_text(json.dumps(frozen,indent=2)+'\n')
print(digest(a.output))
