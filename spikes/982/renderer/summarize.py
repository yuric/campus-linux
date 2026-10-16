#!/usr/bin/env python3
"""Nearest-rank summaries. Every raw run remains separate, including invalid runs."""
import json, math, sys
from pathlib import Path
results=[]
for name in sys.argv[1:]:
    raw=json.loads(Path(name).read_text())
    intervals=[b-a for a,b in zip(raw['frames'],raw['frames'][1:])]
    if not intervals or any(x < 0 or not math.isfinite(x) for x in intervals):
        raise SystemExit('Missing/nonmonotonic frame capture')
    ordered=sorted(intervals)
    rank=lambda q: ordered[max(0,math.ceil(q*len(ordered))-1)]
    valid=not raw['invalid'] and raw['duration_ms'] >= 60000 and raw['warmup_ms'] >= 30000
    results.append(dict(file=name,valid=valid,frames=len(raw['frames']),p50_ms=rank(.5),p95_ms=rank(.95),max_ms=max(intervals),
        intervals_over_33_3_ms=sum(x>33.3 for x in intervals),missed_60hz_frames=sum(max(0,math.floor(x/(1000/60))-1) for x in intervals),
        errors=raw['errors'],pass_run=valid and not raw['errors'] and rank(.95)<=33.3))
print(json.dumps(dict(runs=results,gate_pass=len(results)==5 and all(r['pass_run'] for r in results)),indent=2))
