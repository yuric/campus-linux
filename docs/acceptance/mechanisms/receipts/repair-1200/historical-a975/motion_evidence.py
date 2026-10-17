"""Acceptance-timing admission requires a separate corrected untimed motion capture."""
import hashlib,json,math
from pathlib import Path

def pose(seconds):
    t=min(60,max(0,seconds))
    if t<=10: return [40*t,0,1]
    if t<=20: return [400-80*(t-10),0,1]
    if t<=30: return [-400+40*(t-20),30*(t-20),1]
    if t<=40: return [0,300,1+.05*(t-30)]
    if t<=50: return [0,300,1.5-.075*(t-40)]
    return [0,300-30*(t-50),.75+.025*(t-50)]

def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def requested_pose(row):
    seconds=row.get('seconds')
    actual=row.get('requested')
    if not finite(seconds) or not isinstance(actual,list) or len(actual)!=3:
        raise ValueError('Missing finite motion pose')
    if any(not finite(a) or abs(a-b)>1e-8 for a,b in zip(actual,pose(seconds))):
        raise ValueError('Input differs from fixed six-segment protocol')

def verified_trace(raw):
    inputs=raw.get('inputs',[])
    if not inputs or any(row.get('phase') not in ('warmup','measurement') for row in inputs):
        raise ValueError('Complete warmup and measurement input traces required')
    if any(not finite(row.get('at')) for row in inputs) or any(b['at']<a['at'] for a,b in zip(inputs,inputs[1:])):
        raise ValueError('Monotonic input timestamps required')
    for phase in ('warmup','measurement'):
        rows=[row for row in inputs if row['phase']==phase]
        for row in rows: requested_pose(row)
        # The timer may first observe >60s; the final rAF then emits explicit60.
        # Both have the same clamped terminal pose in the unchanged driver.
        if not rows or rows[0]['seconds']!=0 or rows[-1]['seconds']<60 or any(min(60,b['seconds'])<min(60,a['seconds']) for a,b in zip(rows,rows[1:])):
            raise ValueError('Full monotonic six-segment input trace required')
        if any(not any(segment*10<row['seconds']<(segment+1)*10 for row in rows) for segment in range(6)):
            raise ValueError('Missing exercised input segment')
        if rows[-1]['at']-rows[0]['at']<(30000 if phase=='warmup' else 60000):
            raise ValueError('Input trace does not span its required clock')
    phases=[row['phase'] for row in inputs]
    if phases!=sorted(phases,key=lambda phase:0 if phase=='warmup' else 1):
        raise ValueError('Warmup must precede measurement')
    gestures=raw.get('gestures',[])
    dragging=False
    counts={name:0 for name in ('pointerdown','pointermove','pointercancel')}
    previous=-math.inf
    for row in gestures:
        kind=row.get('type')
        if kind not in counts or any(not finite(row.get(k)) for k in ('at','x','y')) or row['at']<previous:
            raise ValueError('Invalid gesture or timestamp')
        if (kind=='pointerdown' and dragging) or (kind!='pointerdown' and not dragging):
            raise ValueError('Gesture continuity violated')
        dragging=kind!='pointercancel';counts[kind]+=1;previous=row['at']
    if dragging or not all(counts.values()): raise ValueError('Complete continuous pan/cancel trace required')
    checkpoints=raw.get('checkpoints',[])
    if [row.get('index') for row in checkpoints]!=list(range(7)):
        raise ValueError('All seven motion checkpoints required')
    prior_draws=-1
    prior_at=-math.inf
    for index,row in enumerate(checkpoints):
        requested_pose(row)
        if not finite(row.get('at')) or row['at']<=prior_at or not index*10<=row['seconds']<(index+1)*10:
            raise ValueError('Invalid checkpoint clock')
        draws=row.get('draws',{})
        count=draws.get('drawCalls')
        matrices=draws.get('matrices',[])
        if not finite(count) or count<=prior_draws or not matrices:
            raise ValueError('Fresh diagnostic draws and matrices required')
        if not any(m.get('name')=='projectionMatrix' and len(m.get('values',[]))==16 and all(finite(v) for v in m['values']) and abs(m['values'][10]+.001818181830458343)<1e-9 for m in matrices):
            raise ValueError('Main projection diagnostic absent')
        if not any(m.get('name')=='viewMatrix' and len(m.get('values',[]))==16 and all(finite(v) for v in m['values']) for m in matrices):
            raise ValueError('View matrix diagnostic absent')
        prior_draws=count;prior_at=row['at']
    if raw.get('frames')!=[]: raise ValueError('Motion proof must not contain performance samples')

def verified_motion(path):
    raw=json.loads(Path(path).read_text())
    if raw.get('kind')!='motion_proof' or raw.get('errors') or raw.get('invalid'):
        raise ValueError('Successful foreground untimed motion proof required')
    if raw.get('zoom_units')!='absolute producer camera zoom' or raw.get('projection_observer_active') is not False:
        raise ValueError('Absolute zoom proof and restored projection observer required')
    if raw.get('warmup_ms',0)<30000 or raw.get('duration_ms',0)<60000:
        raise ValueError('Full fixed sequence/warmup proof required')
    checks=[raw.get('initialReset',{}).get('absoluteZoom'),raw.get('measurementReset',{}).get('absoluteZoom'),*raw.get('absoluteZoomChecks',[])]
    if len(checks)!=5 or [check and check.get('target') for check in checks]!=[1,1,1.5,.75,1]:
        raise ValueError('Both absolute1 resets plus1.5/0.75/1 settled proofs required')
    for check in checks:
        settled=check.get('settled',{})
        if check.get('deltaMode')!=0 or check.get('ctrlKey') is not False or check.get('active_drag') is not False:
            raise ValueError('Normal production wheel path required')
        if not math.isfinite(settled.get('absolute_zoom',float('nan'))) or abs(settled['absolute_zoom']-check['target'])>1e-5:
            raise ValueError('Actual settled main-camera projection missed absolute target')
        if settled.get('at',0)<check.get('sent',float('inf')):
            raise ValueError('Newly rendered projection after wheel required')
    if any(reset.get('projection_observer_active') is not False for reset in [raw['initialReset'],raw['measurementReset']]):
        raise ValueError('Observer must be removed before both clocks')
    if any(item.get('type')=='pointerup' for item in raw.get('gestures',[])):
        raise ValueError('Click-generating pointerup forbidden in diagnostic input path')
    verified_trace(raw)
    return raw,hashlib.sha256(Path(path).read_bytes()).hexdigest()
