#!/usr/bin/env python3
"""Select GDM's session at the greeter; never enables autologin.

Finish through the actual GDM password field using qmp-console.py or manual entry.
This restarts only GDM inside the named disposable guest and will end its desktop.
"""
import subprocess
import sys

if len(sys.argv)!=2 or sys.argv[1] not in ('wayland','x11'):
    raise SystemExit('usage: select-authenticated-session.py wayland|x11')
script = '''
import configparser
from pathlib import Path
path=Path('/etc/gdm3/custom.conf')
config=configparser.ConfigParser(); config.optionxform=str; config.read(path)
if 'daemon' not in config: config['daemon']={}
daemon=config['daemon']
daemon.pop('AutomaticLoginEnable',None); daemon.pop('AutomaticLogin',None)
daemon.pop('WaylandEnable',None)
if SESSION=='x11': daemon['WaylandEnable']='false'
with path.open('w') as f: config.write(f)
account=Path('/var/lib/AccountsService/users/campusqa')
user=configparser.ConfigParser(); user.optionxform=str; user.read(account)
if 'User' not in user:user['User']={}
user['User']['XSession']='ubuntu-xorg' if SESSION=='x11' else 'ubuntu-wayland'
with account.open('w') as f:user.write(f)
'''.replace('SESSION',repr(sys.argv[1]))
cmd=['/opt/homebrew/bin/limactl','shell','campus-linux-d5-noble-arm64','sudo']
subprocess.run(cmd+['python3','-'],input=script.encode(),check=True)
subprocess.run(cmd+['systemctl','restart','gdm'],check=True)
print('Selected authenticated '+sys.argv[1]+'; password entry still required.')
