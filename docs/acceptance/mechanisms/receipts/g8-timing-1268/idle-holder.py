#!/usr/bin/python3
"""10774: one transient idle-only GNOME connection, bounded below20minutes."""
import ctypes,datetime,hashlib,json,os,pathlib,signal,socket,subprocess,sys,time
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
assert os.getuid()==1000 and socket.gethostname()=='lima-campus-linux-d5-noble-arm64'
label=sys.argv[1];assert label in ('wayland-final-base','wayland-final-always','x11-final-base','x11-final-always')
p=pathlib.Path('/home/campusqa/spike982/g8-timing-1268')/label;p.mkdir(exist_ok=True)
assert not (p/'inhibitor-start.json').exists()
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None);start=time.monotonic();deadline=start+1170
app='campus-g8-982-'+label;cookie=None;reason='normal completion';released=False
stop=False
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def call(method,args=None,path='/org/gnome/SessionManager',iface='org.gnome.SessionManager'):
 return bus.call_sync('org.gnome.SessionManager',path,iface,method,args,None,Gio.DBusCallFlags.NONE,3000,None).unpack()
def listing():
 result=[]
 for path in call('GetInhibitors')[0]:
  result.append({'path':path,'app_id':call('GetAppId',path=path,iface='org.gnome.SessionManager.Inhibitor')[0],'flags':call('GetFlags',path=path,iface='org.gnome.SessionManager.Inhibitor')[0]})
 return result
def proc(pid):
 q=pathlib.Path('/proc')/str(pid);raw=(q/'stat').read_text();parts=raw[raw.rfind(')')+2:].split();s=ctypes.c_char_p();rc=ctypes.CDLL('libsystemd.so.0').sd_pid_get_session(pid,ctypes.byref(s))
 return {'pid':pid,'starttime':int(parts[19]),'stat':raw,'cgroup':(q/'cgroup').read_text(),'sd_pid_get_session':{'returncode':rc,'session':s.value.decode() if rc==0 else None}}
def command(c):return subprocess.check_output(c,text=True,timeout=3).strip()
def signal_stop(sig,_frame):
 global stop,reason
 stop=True;reason='signal '+str(sig)
for sig in [signal.SIGTERM,signal.SIGINT,signal.SIGALRM]:signal.signal(sig,signal_stop)
signal.setitimer(signal.ITIMER_REAL,1190)
before=listing();sid=command(['loginctl','show-user','1000','-p','Display','--value'])
record={'utc':utc(),'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'holder':proc(os.getpid()),'parent':proc(os.getppid()),'session':command(['loginctl','show-session',sid]),'connection_unique_name':bus.get_unique_name(),'idle_delay':command(['gsettings','get','org.gnome.desktop.session','idle-delay']),'lock_enabled':command(['gsettings','get','org.gnome.desktop.screensaver','lock-enabled']),'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'before':before,'flags':8,'absolute_lifetime_bound_seconds':1200,'normal_deadline_seconds':1170,'api_documentation':'https://gnome.pages.gitlab.gnome.org/gnome-session/re04.html'}
try:
 cookie=call('Inhibit',GLib.Variant('(susu)',(app,0,'Campus G8 fixed foreground series',8)))[0]
 after=listing();ours=[r for r in after if r['app_id']==app];assert len(ours)==1 and ours[0]['flags']==8
 record.update(cookie=cookie,after=after,idle_inhibited=call('IsInhibited',GLib.Variant('(u)',(8,)))[0]);assert record['idle_inhibited']
 (p/'inhibitor-start.json').write_text(json.dumps(record,indent=2)+'\n');next_sample=0
 while not stop and time.monotonic()<deadline:
  if (p/'inhibitor.stop').exists():reason='owned stop file';break
  if time.monotonic()>=next_sample:
   with (p/'inhibitor-samples.jsonl').open('a') as f:f.write(json.dumps({'utc':utc(),'elapsed':time.monotonic()-start,'inhibitors':listing(),'idle_inhibited':call('IsInhibited',GLib.Variant('(u)',(8,)))[0]})+'\n')
   next_sample=time.monotonic()+30
  time.sleep(.25)
 else:
  if not stop:reason='absolute lifetime deadline'
except BaseException as e:
 reason=type(e).__name__+': '+str(e);raise
finally:
 result={'utc':utc(),'reason':reason,'elapsed_seconds':time.monotonic()-start,'holder_pid':os.getpid(),'cookie':cookie}
 try:
  if cookie is not None:call('Uninhibit',GLib.Variant('(u)',(cookie,)))
  result.update(after=listing(),idle_inhibited=call('IsInhibited',GLib.Variant('(u)',(8,)))[0]);result['owned_inhibitor_absent']=not any(r['app_id']==app for r in result['after'])
 except Exception as e:result['release_error']=str(e)
 (p/'inhibitor-release.json').write_text(json.dumps(result,indent=2)+'\n');bus.close_sync(None)
