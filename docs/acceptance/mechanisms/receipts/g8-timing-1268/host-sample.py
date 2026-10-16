import subprocess,json,datetime,pathlib,os,sys
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'free_bytes':os.statvfs('/Users/yuri').f_bavail*os.statvfs('/Users/yuri').f_frsize,'commands':[]}
for cmd in [['uptime'],['vm_stat'],['sysctl','vm.swapusage'],['df','-k','/Users/yuri'],['top','-l','2','-n','0','-s','1']]:
 q=subprocess.run(cmd,capture_output=True,text=True);r['commands'].append({'argv':cmd,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
pathlib.Path(sys.argv[1]).write_text(json.dumps(r,indent=2)+'\n');print(r['utc'],r['free_bytes']);assert r['free_bytes']>=20*1024**3
