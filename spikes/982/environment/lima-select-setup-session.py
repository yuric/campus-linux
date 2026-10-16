#!/usr/bin/env python3
"""Provision a real GDM autologin session for setup only, not PAM/keyring acceptance."""
import subprocess
import sys

session = sys.argv[1] if len(sys.argv) == 2 else ""
if session not in {"x11", "wayland", "off"}:
    raise SystemExit("usage: lima-select-setup-session.py x11|wayland|off")
script = r'''
from pathlib import Path
import configparser
session = SESSION
path = Path('/etc/gdm3/custom.conf')
config = configparser.ConfigParser()
config.optionxform = str
config.read(path)
if 'daemon' not in config: config['daemon'] = {}
daemon = config['daemon']
if session == 'off':
    daemon.pop('AutomaticLoginEnable', None)
    daemon.pop('AutomaticLogin', None)
    daemon.pop('WaylandEnable', None)
else:
    daemon['AutomaticLoginEnable'] = 'true'
    daemon['AutomaticLogin'] = 'campusqa'
    if session == 'x11': daemon['WaylandEnable'] = 'false'
    else: daemon.pop('WaylandEnable', None)
    account = Path('/var/lib/AccountsService/users/campusqa')
    user = configparser.ConfigParser()
    user.optionxform = str
    user.read(account)
    if 'User' not in user: user['User'] = {}
    user['User']['XSession'] = 'ubuntu-xorg' if session == 'x11' else 'ubuntu-wayland'
    with account.open('w') as output: user.write(output)
with path.open('w') as output: config.write(output)
'''.replace("SESSION", repr(session))
subprocess.run(
    ["/opt/homebrew/bin/limactl", "shell", "campus-linux-d5-noble-arm64", "sudo", "python3", "-"],
    input=script.encode(), check=True,
)
subprocess.run(
    ["/opt/homebrew/bin/limactl", "shell", "campus-linux-d5-noble-arm64", "sudo", "systemctl", "restart", "gdm"],
    check=True,
)
print("GDM setup mode:", session, "(autologin is setup evidence only)")
