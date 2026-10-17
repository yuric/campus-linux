import gi,json,pathlib,datetime
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
base=pathlib.Path('/home/campusqa/spike982/g8-native-1240')
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
def call(name,args=None):return bus.call_sync('org.gnome.Mutter.DisplayConfig','/org/gnome/Mutter/DisplayConfig','org.gnome.Mutter.DisplayConfig',name,args,None,Gio.DBusCallFlags.NONE,10000,None)
s=call('GetCurrentState');state=s.unpack(); serial=state[0]
assert len(state[1])==1
connector=state[1][0][0][0];mode=next(m[0] for m in state[1][0][1] if m[1]==1920 and m[2]==1200)
args=GLib.Variant('(uua(iiduba(ssa{sv}))a{sv})',(serial,1,[(0,0,1.0,0,True,[(connector,mode,{})])],{}))
r=call('ApplyMonitorsConfig',args)
p=base/('display-change-'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')+'.json');p.write_text(json.dumps({'before':str(s),'args':str(args),'result':str(r),'after':str(call('GetCurrentState'))},indent=2)+'\n')
