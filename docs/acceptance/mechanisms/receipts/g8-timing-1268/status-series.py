import subprocess,json,pathlib,datetime,os,sys
label=sys.argv[1]
code='''import pathlib,json,datetime,os,sys
base=pathlib.Path('/home/campusqa/spike982/g8-timing-1268');p=base/sys.argv[1];sys.path.insert(0,str(base/'repo/spikes/982/renderer'));from summarize import summarize
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'label':sys.argv[1],'complete':(p/'timing-complete.json').exists(),'command_finished':(p/'five-command.json').exists(),'guest_free':os.statvfs(p).f_bavail*os.statvfs(p).f_frsize,'runs':[],'inhibitor_released':(p/'inhibitor-release.json').exists()}
for f in sorted((p/'five').glob('run-*.json')):r['runs'].append(summarize(json.loads(f.read_text()),f.name))
if (p/'inhibitor-samples.jsonl').exists():r['latest_inhibitor']=json.loads((p/'inhibitor-samples.jsonl').read_text().splitlines()[-1])
print(json.dumps(r))'''
r=json.loads(subprocess.check_output(['limactl','shell','campus-linux-d5-noble-arm64','sudo','python3','-B','-',label],input=code.encode()))
p=pathlib.Path('/Users/yuri/.lima/campus-linux-d5-noble-arm64/disk');r['host_free']=os.statvfs(p.parent).f_bavail*os.statvfs(p.parent).f_frsize;r['disk_allocated']=p.stat().st_blocks*512;r['disk_growth_since_resume']=r['disk_allocated']-7388856320
with open('/tmp/campus982-1268/series-progress.jsonl','a') as f:f.write(json.dumps(r)+'\n')
print(json.dumps(r));assert r['host_free']>=20*1024**3 and r['guest_free']>=2*1024**3 and r['disk_growth_since_resume']<1024**3
