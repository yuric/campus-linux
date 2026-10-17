#!/usr/bin/python3
"""Direction1240 observation/launch wrapper; benchmark source is unchanged."""
import ctypes,datetime,hashlib,json,os,pathlib,socket,struct,subprocess,sys,time,signal
BASE=pathlib.Path('/home/campusqa/spike982/g8-native-1240')
REPO=BASE/'repo'; R=REPO/'spikes/982/renderer'; EXPORT=BASE/'desktop-first'
session,stage,label=sys.argv[1:]; OUT=BASE/label; OUT.mkdir(exist_ok=True)
assert os.getuid()==1000 and session in ('wayland','x11') and stage in ('preflight','motion')
os.environ['LIBGL_ALWAYS_SOFTWARE']='1'
def command(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=15);return {'argv':args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def proc(pid):
 p=pathlib.Path('/proc')/str(pid)
 try:
  raw=(p/'stat').read_text();fields=raw[raw.rfind(')')+2:].split();out={'pid':pid,'stat':raw,'starttime':int(fields[19]),'ppid':int(fields[1]),'cgroup':(p/'cgroup').read_text(),'uid':p.stat().st_uid,'comm':(p/'comm').read_text().strip()}
  lib=ctypes.CDLL('libsystemd.so.0');s=ctypes.c_char_p();rc=lib.sd_pid_get_session(pid,ctypes.byref(s));out['sd_pid_get_session']={'returncode':rc,'session':s.value.decode() if rc==0 else None};return out
 except OSError as e:return {'pid':pid,'error':str(e)}
def observation():
 env={k:os.environ.get(k) for k in ['DISPLAY','WAYLAND_DISPLAY','XDG_RUNTIME_DIR','XDG_SESSION_ID','XDG_SESSION_TYPE','GDK_BACKEND','LIBGL_ALWAYS_SOFTWARE','XDG_CURRENT_DESKTOP','XDG_SESSION_DESKTOP']}
 sid=command(['loginctl','show-user','1000','-p','Display','--value'])['stdout'].strip()
 data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'uid':os.getuid(),'pid':proc(os.getpid()),'parent':proc(os.getppid()),'environment':env,'active_session':command(['loginctl','show-session',sid]),'sessions':command(['loginctl','list-sessions']),'uname':command(['uname','-a']),'os_release':pathlib.Path('/etc/os-release').read_text(),'packages':command(['dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\n','libwebkit2gtk-4.1-0','libegl-mesa0','libgl1-mesa-dri','libllvm20','mutter-common','gnome-shell','gdm3']),'cpu_count':os.cpu_count(),'meminfo':pathlib.Path('/proc/meminfo').read_text(),'display_state':command(['gdbus','call','--session','--dest','org.gnome.Mutter.DisplayConfig','--object-path','/org/gnome/Mutter/DisplayConfig','--method','org.gnome.Mutter.DisplayConfig.GetCurrentState']),'animations':command(['gsettings','get','org.gnome.desktop.interface','enable-animations']),'guest_free_bytes':os.statvfs(BASE).f_bavail*os.statvfs(BASE).f_frsize,'wrapper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
 peers={}
 for kind,path in [('wayland',str(pathlib.Path(env['XDG_RUNTIME_DIR'])/env['WAYLAND_DISPLAY']) if env['WAYLAND_DISPLAY'] else None),('x11','\0/tmp/.X11-unix/X'+env['DISPLAY'].split(':')[-1].split('.')[0] if env['DISPLAY'] else None)]:
  if not path:continue
  try:
   s=socket.socket(socket.AF_UNIX);s.settimeout(2);s.connect(path);pid,uid,gid=struct.unpack('3i',s.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12));peers[kind]={'pid':pid,'uid':uid,'gid':gid,'process':proc(pid)};s.close()
  except OSError as e:peers[kind]={'error':str(e)}
 data['display_peers']=peers
 leader=[line.split('=',1)[1] for line in data['active_session']['stdout'].splitlines() if line.startswith('Leader=')]
 data['session_leader']=proc(int(leader[0])) if leader else None
 return data
(OUT/(stage+'-launch.json')).write_text(json.dumps(observation(),indent=2)+'\n')
def run(name,args,limit):
 assert not (OUT/(name+'-command.json')).exists()
 rec={'argv':args,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_seconds':limit}
 with (OUT/(name+'.stdout')).open('wb') as stdout,(OUT/(name+'.stderr')).open('wb') as stderr:
  child=subprocess.Popen(args,stdout=stdout,stderr=stderr,cwd=REPO,start_new_session=True)
  rec['launch']=proc(child.pid)
  try:rec['returncode']=child.wait(timeout=limit)
  except subprocess.TimeoutExpired:
   rec['timeout']=True;os.killpg(child.pid,signal.SIGKILL);rec['returncode']=child.wait(timeout=10)
 rec['after']=proc(child.pid);rec['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (OUT/(name+'-command.json')).write_text(json.dumps(rec,indent=2)+'\n')
 if rec['returncode']!=0:raise SystemExit(rec['returncode'])
if stage=='preflight':
 run('gpu',['python3','-B',str(R/'capture-gpu.py')],25)
 (OUT/'gpu.json').write_bytes((OUT/'gpu.stdout').read_bytes())
 run('preflight',['python3','-B',str(R/'run-webkit.py'),'--preflight','--compositing-policy','on-demand','--native-gpu-receipt',str(OUT/'gpu.json'),str(EXPORT),'ignored',str(OUT/'preflight.json')],125)
else:
 run('diagnostic-freeze',['python3','-B',str(R/'freeze.py'),'--native-gpu-receipt',str(OUT/'gpu.json'),str(OUT/'environment.json'),str(OUT/'diagnostic-freeze.json')],15)
 run('motion',['python3','-B',str(R/'run-webkit.py'),'--motion-proof','--compositing-policy','on-demand','--native-gpu-receipt',str(OUT/'gpu.json'),str(EXPORT),str(OUT/'diagnostic-freeze.json'),str(OUT/'motion.json')],190)
 run('proof-bound-freeze',['python3','-B',str(R/'freeze.py'),'--native-gpu-receipt',str(OUT/'gpu.json'),'--motion-proof',str(OUT/'motion.json'),str(OUT/'environment.json'),str(OUT/'timing-freeze.json')],15)
(OUT/(stage+'-complete.json')).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'stage':stage})+'\n')
