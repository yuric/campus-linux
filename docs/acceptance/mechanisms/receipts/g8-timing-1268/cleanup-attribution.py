import pathlib,json,datetime,subprocess,sys,os
base=pathlib.Path('/home/campusqa/spike982/g8-timing-1268');label=sys.argv[1];folder=base/label;pids=set();scopes=[]
for p in folder.glob('*-command.json'):
 j=json.loads(p.read_text());pids.add(j['launch']['pid'])
for p in folder.glob('*-launch.json'):
 j=json.loads(p.read_text());pids.add(j['pid']['pid']);own=j['pid']['cgroup'].strip().split('::',1)[1];parent=j['parent']['cgroup'].strip().split('::',1)[1];shared=own==parent and 'org.gnome.Shell@' in own
 scopes.append({'cgroup':own,'parent_cgroup':parent,'shared_graphical_parent':shared,'exists':(pathlib.Path('/sys/fs/cgroup')/own.lstrip('/')).exists()})
for p in folder.rglob('*.json'):
 j=json.loads(p.read_text())
 if isinstance(j,dict):
  pids.update(r['pid'] for r in j.get('process_graphics',[]))
  if j.get('kind')=='native_gpu_diagnostics':pids.add(j['pid'])
i=folder/'inhibitor-start.json';holder=None
if i.exists():
 holder=json.loads(i.read_text())['holder'];pids.add(holder['pid']);own=holder['cgroup'].strip().split('::',1)[1];scopes.append({'cgroup':own,'holder':True,'shared_graphical_parent':False,'exists':(pathlib.Path('/sys/fs/cgroup')/own.lstrip('/')).exists()})
remaining=[p for p in sorted(pids) if (pathlib.Path('/proc')/str(p)).exists()]
q=subprocess.run(['pgrep','-af','WebKit(Network|Web)|g8-timing-1268/(graphical-probe|idle-holder)|run-webkit.py|run-five.py|capture-gpu.py|authority-window.py|campus1057.*desktop.py'],capture_output=True,text=True)
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'label':label,'observed_pids':sorted(pids),'remaining':remaining,'scopes':scopes,'process_scan':{'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr},'signals_sent':[],'owned_processes_absent':not remaining,'owned_scopes_absent':all(not s['exists'] for s in scopes if not s['shared_graphical_parent']),'shared_parent_cgroup_not_owned':any(s['shared_graphical_parent'] for s in scopes)}
print(json.dumps(r,indent=2));assert r['owned_processes_absent'] and r['owned_scopes_absent'] and q.returncode==1
