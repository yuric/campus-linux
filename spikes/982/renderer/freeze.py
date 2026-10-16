#!/usr/bin/env python3
"""Create immutable-input receipt before first run; never fills unobserved environment facts."""
import argparse,datetime,hashlib,json
from pathlib import Path
from native_evidence import native_receipt
p=argparse.ArgumentParser()
p.add_argument('--native-gpu-receipt',type=Path,required=True)
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
manifest=json.loads((base/'producer-manifest.json').read_text())
native=native_receipt(a.native_gpu_receipt)
if env['webgl_api_renderer']!=native['webgl_api_renderer']: raise SystemExit('WebGL API identity differs from reviewed source')
frozen=dict(env,native_evidence=native,native_evidence_code_sha256=digest(base/'native_evidence.py'),producer_sha=manifest['source'],manifest_sha256=digest(base/'producer-manifest.json'),
            fixture_sha256=digest(base/'fixture.json'),measure_sha256=digest(base/'measure.js'),
            runner_sha256=digest(base/'run-webkit.py'),protocol_sha256=digest(base.parents[2]/'docs/acceptance/visual-protocol.json'),
            seed=98120261016,repeats=5,duration_seconds=60,warmup_seconds=30,p95_ms_max=33.3,
            viewport=[1440,900],device_scale=1,render_scale=1,appearance='light',
            projects=12,agents=48,tasks=180,frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
a.output.write_text(json.dumps(frozen,indent=2)+'\n')
print(digest(a.output))
