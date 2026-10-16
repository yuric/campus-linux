#!/usr/bin/env python3
"""Check this speech evidence's byte bindings and observed sequence; no product pass."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'docs/acceptance/mechanisms/receipts/speech-next-1203'
sys.path.insert(0,str(ROOT/'scripts'))
from check_mechanism_evidence import verify
manifest=str((BASE/'index.json').relative_to(ROOT))
verify(ROOT,(manifest,))
for directory in [BASE,*(BASE/name for name in ('attempt1','attempt2','attempt3'))]:
    launch=json.loads((directory/'launch.json').read_text())
    for name,digest in launch['source_hashes'].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest
    assert launch['cgroup_absent']
for p in (ROOT/'spikes/982/speech-next').glob('*.py'):
    if (BASE/p.name).exists():assert p.read_bytes()==(BASE/p.name).read_bytes()
r=json.loads((BASE/'receipt.json').read_text());events=r['events']
assert r['completed'] and not r['owned_workers_remaining'] and r['source_absent_after_cleanup']
assert r['memory_max']=='536870912' and r['swap_max']=='0' and r['interfaces']==['lo']
assert 0<r['tree_memory_peak_bytes']<536870912 and int(r['memory_swap_peak'])==0
assert r['locale_mapping']['language'] is None
assert r['cancellation']['all_three_actually_running'] and r['cancellation']['observed_returncode']==-15
stop=next(x['monotonic'] for x in events if x['event']=='Stop')
partials=[x for x in events if x['event']=='provisional_collected']
assert len(partials)==2 and all(x['capture_active'] and x['monotonic']<stop for x in partials)
assert next(x['monotonic'] for x in events if x['event']=='inference_start' and x['label']=='final')>stop
active=set()
for event in events:
    if event['event']=='inference_start':
        assert not active;active.add(event['label'])
    if event['event']=='inference_collected':active.remove(event['label'])
assert not active
assert [x['samples'][1] for x in r['inferences'] if x['label'] in ('prefix1','prefix2')]==[48000,96000]
for row in r['inferences']:
    assert row['argv'][row['argv'].index('-t')+1]=='2'
    if row['label']!='cancel1':assert row['returncode']==0 and row['stdout'].strip()
collection=json.loads((BASE/'collection.json').read_text())
assert collection['allocated_bytes']<128*1024**2 and collection['output_allocated_bytes']<4*1024**2
assert all(collection['cgroups_absent'].values())
assert 'Stopped' in json.loads((BASE/'host-after.json').read_text())['status']
if '--head' in sys.argv:
    head=sys.argv[sys.argv.index('--head')+1]
    for row in json.loads((BASE/'index.json').read_text())['files']:
        data=subprocess.check_output(['git','show',head+':'+row['path']],cwd=ROOT)
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
print('PASS source bindings, actual prefix/Stop/cancel sequence and resource observations; no quality/product acceptance')
