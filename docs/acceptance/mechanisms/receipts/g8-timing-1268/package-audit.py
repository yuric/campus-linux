import subprocess,json,time,pathlib,datetime,os
start=time.monotonic();rows=[]
commands=[['du','-sx','-B1',p] for p in ['/var/log','/var/cache','/var/lib','/home/campusqa/.cache','/home/campusqa/spike982/g8-timing-1268']]
commands += [['tail','-n','60',p] for p in ['/var/log/apt/history.log','/var/log/dpkg.log','/var/log/unattended-upgrades/unattended-upgrades.log','/var/log/unattended-upgrades/unattended-upgrades-dpkg.log']]
commands += [['systemctl','show','apt-daily.service','apt-daily-upgrade.service','unattended-upgrades.service','-p','Id','-p','ActiveState','-p','SubState','-p','ExecMainStartTimestamp','-p','ExecMainExitTimestamp'],['dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\n','libwebkit2gtk-4.1-0','libegl-mesa0','libgl1-mesa-dri','libllvm20','mutter-common','gnome-shell','gdm3','systemd','systemd-resolved','systemd-timesyncd','libsystemd0','linux-image-6.8.0-142-generic'],['uname','-a'],['df','-B1','/']]
for c in commands:
 try:
  q=subprocess.run(c,capture_output=True,text=True,timeout=max(.1,55-(time.monotonic()-start)));rows.append({'argv':c,'returncode':q.returncode,'stdout':q.stdout[:200000],'stderr':q.stderr[:4000]})
 except subprocess.TimeoutExpired:rows.append({'argv':c,'timeout':True});break
processes=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  comm=(p/'comm').read_text().strip()
  if any(k in comm.lower() for k in ['apt','dpkg','unattended']):processes.append({'pid':int(p.name),'comm':comm,'exe':os.readlink(p/'exe'),'stat':(p/'stat').read_text(),'cgroup':(p/'cgroup').read_text()})
 except OSError:pass
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-start,'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'commands':rows,'package_processes':processes}
s=json.dumps(r,indent=2)+'\n';assert len(s.encode())<4*1024**2;print(s,end='')
