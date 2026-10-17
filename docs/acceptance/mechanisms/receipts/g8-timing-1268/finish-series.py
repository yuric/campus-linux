import subprocess,pathlib,sys,time,json,tarfile,io,datetime
label=sys.argv[1];root=pathlib.Path('/tmp/campus982-1268');base='/home/campusqa/spike982/g8-timing-1268';ssh=['limactl','shell','campus-linux-d5-noble-arm64']
end=time.monotonic()+660
while time.monotonic()<end:
 if subprocess.run(ssh+['sudo','test','-f',base+'/'+label+'/five-command.json'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
 time.sleep(10)
else:raise SystemExit('Series completion observation timed out; holder retains independent absolute bound')
subprocess.run(['python3',str(root/'host-sample.py'),str(root/('host-'+label+'-after-series.json'))],check=True)
subprocess.run(ssh+['sudo','-u','campusqa','touch',base+'/'+label+'/inhibitor.stop'],check=True)
time.sleep(3)
data=subprocess.check_output(ssh+['sudo','tar','-cf','-','-C',base,label]);tarfile.open(fileobj=io.BytesIO(data)).extractall(root)
p=root/label
release=json.loads((p/'inhibitor-release.json').read_text());print('Inhibitor release:',json.dumps(release))
q=subprocess.run(ssh+['sudo','python3','-B',base+'/cleanup-series.py',label],capture_output=True,text=True);(p/'process-cleanup.json').write_text(q.stdout);assert q.returncode==0,q.stderr
start=json.loads((p/'inhibitor-start.json').read_text());print('holder start keys',list(start))
cmd=json.loads((p/'five-command.json').read_text());print('series command',cmd['returncode'],cmd['finished_utc'])
sys.path.insert(0,str(pathlib.Path.cwd()/'spikes/982/renderer'));from summarize import summarize
runs=[summarize(json.loads(f.read_text()),f.name) for f in sorted((p/'five').glob('run-*.json'))]
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':runs,'all_five_valid':len(runs)==5 and all(x['valid'] and x['errors']==[] for x in runs),'gate_pass':len(runs)==5 and all(x['pass_run'] for x in runs),'command_returncode':cmd['returncode']}
(p/'external-series-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
