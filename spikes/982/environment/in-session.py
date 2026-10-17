#!/usr/bin/env python3
"""Guest-only probe launcher using the actual campusqa GDM session environment."""
import os
import pwd
import subprocess
import sys

assert os.geteuid() == 0 and os.uname().nodename == 'lima-campus-linux-d5-noble-arm64'
account = pwd.getpwnam('campusqa')
env = {'HOME':account.pw_dir, 'USER':account.pw_name, 'PATH':'/usr/bin:/bin', 'LANG':'C.UTF-8',
       'XDG_RUNTIME_DIR':f'/run/user/{account.pw_uid}',
       'DBUS_SESSION_BUS_ADDRESS':f'unix:path=/run/user/{account.pw_uid}/bus'}
def drop():
    os.initgroups(account.pw_name, account.pw_gid)
    os.setgid(account.pw_gid)
    os.setuid(account.pw_uid)
raw = subprocess.check_output(['systemctl','--user','show-environment'],env=env,preexec_fn=drop,text=True)
for line in raw.splitlines():
    key,_,value=line.partition('=')
    if key in {'DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','XDG_SESSION_TYPE','XDG_CURRENT_DESKTOP'}: env[key]=value
env['LIBGL_ALWAYS_SOFTWARE']='1'
raise SystemExit(subprocess.call(sys.argv[1:],env=env,preexec_fn=drop,close_fds=True))
