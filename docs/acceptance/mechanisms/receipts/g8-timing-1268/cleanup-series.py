import pathlib,json,datetime,sys
base=pathlib.Path('/home/campusqa/spike982/g8-timing-1268');folder=base/sys.argv[1];pids=set();commands=[]
for p in folder.glob('*-command.json'):
 j=json.loads(p.read_text());pids.add(j['launch']['pid']);commands.append(j)
for p in folder.glob('*-launch.json'):
 j=json.loads(p.read_text());pids.add(j['pid']['pid'])
for p in folder.rglob('*.json'):
 j=json.loads(p.read_text())
 if isinstance(j,dict):pids.update(r['pid'] for r in j.get('process_graphics',[]))
remaining=[]
for pid in sorted(pids):
 p=pathlib.Path('/proc')/str(pid)
 if p.exists():remaining.append({'pid':pid,'stat':(p/'stat').read_text(),'cgroup':(p/'cgroup').read_text()})
scopes=[]
for p in folder.glob('*-launch.json'):
 j=json.loads(p.read_text());scope=j['pid']['cgroup'].strip().split('::',1)[1];scopes.append({'cgroup':scope,'exists':(pathlib.Path('/sys/fs/cgroup')/scope.lstrip('/')).exists()})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observed_pids':sorted(pids),'remaining':remaining,'scopes':scopes,'cleanup_confirmed':not remaining and not any(s['exists'] for s in scopes),'signals_sent':[]}
print(json.dumps(result,indent=2));assert result['cleanup_confirmed']
