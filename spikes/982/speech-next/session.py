#!/usr/bin/env python3
"""Run from GNOME's Run dialog/terminal; record only the four locale variables."""
import json, locale, os, subprocess, time
from pathlib import Path
root = Path(__file__).resolve().parent
assert os.uname().nodename == 'lima-campus-linux-d5-noble-arm64' and os.getuid() == 1000
r = {'launch_origin': 'GNOME Run dialog -> gnome-terminal -> session.py',
     'pid': os.getpid(), 'ppid': os.getppid(), 'monotonic': time.monotonic(),
     'environment': {k: os.environ[k] for k in ('LANG','LC_ALL','LC_MESSAGES','LC_CTYPE') if k in os.environ}}
sid = subprocess.check_output(['loginctl','show-user','campusqa','-p','Display','--value'], text=True).strip()
r['session_id'] = sid
r['session'] = subprocess.check_output(['loginctl','show-session',sid,'-p','Id','-p','User','-p','Type','-p','Class','-p','Service','-p','Remote','-p','Active'], text=True)
try:
    locale.setlocale(locale.LC_ALL, '')
    r['effective'] = {k: locale.setlocale(getattr(locale,k)) for k in ('LC_MESSAGES','LC_CTYPE')}
except locale.Error as e: r['locale_error'] = str(e)
(root/'session.json').write_text(json.dumps(r,indent=2)+'\n')
print('Public locale observation recorded; bounded supervisor performs inference separately.')
