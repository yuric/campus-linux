#!/usr/bin/env python3
"""Mac-side bounded disposable Lima probe runner. No install, compile or VM creation."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

PREFIX = ['/opt/homebrew/bin/limactl', 'shell', 'campus-linux-d5-noble-arm64', 'sudo']
GUEST = '/home/campusqa/spike982/core-sentinel-10470/probe.py'
SNAPSHOT = r'''
import os,json,pathlib,hashlib,subprocess,sys
meta={}
for root in ['/var/crash','/var/lib/systemd/coredump','/home/campusqa/spike982/core-sentinel-10470']:
 p=pathlib.Path(root)
 meta[root]=[{"name":f.name,"size":f.stat().st_size,"mtime_ns":f.stat().st_mtime_ns,"inode":f.stat().st_ino} for f in p.iterdir() if f.is_file()] if p.exists() else []
p=pathlib.Path('/var/log/apport.log')
print(json.dumps({'metadata':meta,'apport_log_size':p.stat().st_size if p.exists() else 0,'apport_log_inode':p.stat().st_ino if p.exists() else None,'utc':subprocess.check_output(['date','--iso-8601=ns'],text=True).strip()}))
'''
IDENTITY = r'''
import os,json,pathlib,hashlib,subprocess
def cmd(a):
 p=subprocess.run(a,capture_output=True,text=True);return {'argv':a,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
paths=['/usr/share/apport/apport','/usr/bin/python3.12','/home/campusqa/spike982/core-sentinel-10470/probe.py']
print(json.dumps({'uname':list(os.uname()),'packages':cmd(['dpkg-query','-W','-f=${binary:Package} ${Version} ${Architecture}\n','apport','systemd','linux-image-'+os.uname().release]),'files':{p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in paths},'core_pattern':pathlib.Path('/proc/sys/kernel/core_pattern').read_text(),'core_pipe_limit':pathlib.Path('/proc/sys/kernel/core_pipe_limit').read_text(),'apport_enabled':pathlib.Path('/etc/default/apport').read_text(),'user_bus_present':pathlib.Path('/run/user/1000/bus').exists()}))
'''
OBSERVE = r'''
import json,os,pathlib,subprocess,sys,time
arg=json.loads(sys.stdin.readline());pids=arg['pids'];before=arg['before'];unit=arg['unit'];seen=[]
# Observation includes a three-second quiet interval. Fast invocation could be missed;
# kernel exact-PID sentinel messages provide independent positive suppression evidence.
for _ in range(30):
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   comm=(p/'comm').read_text().strip()
   if comm not in ['apport','python3','python3.12']:continue
   a=(p/'cmdline').read_bytes().split(b'\0')
   if b'/usr/share/apport/apport' not in a:continue
   if any((b'-p'+str(pid).encode()) in a or (b'-p' in a and a[a.index(b'-p')+1]==str(pid).encode()) for pid in pids):seen.append(int(p.name))
  except (OSError,IndexError):pass
 time.sleep(.1)
k=subprocess.run(['journalctl','-k','--since',arg['since'],'--no-pager','-o','cat'],capture_output=True,text=True,timeout=5)
lines=k.stdout.splitlines();own=[]
for i,line in enumerate(lines):
 if any(('Process '+str(pid)+'(') in line or ('pid='+str(pid)+' ') in line for pid in pids):
  own.append(line)
  if i+1<len(lines) and lines[i+1]=='Aborting core':own.append(lines[i+1])
log=pathlib.Path('/var/log/apport.log');own_apport=[];delta=0;rotated=False
if log.exists():
 rotated=before['apport_log_inode'] is not None and log.stat().st_ino!=before['apport_log_inode']
 delta=log.stat().st_size-before['apport_log_size']
 if not rotated and 0<=delta<=1048576:
  with log.open('rb') as f:f.seek(before['apport_log_size']);new=f.read(1048576).decode(errors='replace')
  own_apport=[l for l in new.splitlines() if any(('pid '+str(pid)) in l or ('pid='+str(pid)) in l for pid in pids)]
cg=pathlib.Path('/sys/fs/cgroup/system.slice')/(unit+'.service')
print(json.dumps({'kernel_command_returncode':k.returncode,'kernel_pid_lines':own,'matched_collector_pids':sorted(set(seen)),'observation_seconds':3,'apport_new_bytes':delta,'apport_rotated':rotated,'apport_pid_lines':own_apport,'cgroup_exists':cg.exists(),'cgroup_procs':(cg/'cgroup.procs').read_text() if cg.exists() else '', 'original_pids_still_present':[pid for pid in pids if pathlib.Path('/proc/'+str(pid)).exists()]}))
'''


def guest(code, arg=None):
    # Code is passed as an argument; synthetic observation inputs use stdin.
    r = subprocess.run(PREFIX + ['/usr/bin/python3', '-c', code],
                       input='' if arg is None else json.dumps(arg)+'\n',
                       capture_output=True, text=True, timeout=10)
    if r.returncode:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)


def main():
    out = Path(sys.argv[1]); out.mkdir(exist_ok=False)
    identity = guest(IDENTITY)
    (out/'identity.json').write_text(json.dumps(identity, indent=2)+'\n')
    source = Path(__file__).with_name('core-sentinel-probe.py')
    assert identity['files'][GUEST] == hashlib.sha256(source.read_bytes()).hexdigest()
    for case in ['bare','filtered','descendants','fail-limit','fail-filter','foreign-abi',
                 'sentinel-abort','filtered-abort','descendants-abort']:
        free = shutil.disk_usage(out).free
        if free < 20*1024**3:
            raise RuntimeError('20 GiB host floor')
        if sum(p.stat().st_size for p in out.iterdir() if p.is_file()) > 16*1024**2:
            raise RuntimeError('16 MiB retained-output cap')
        unit = 'campus982-core-10470-final-'+case
        before = guest(SNAPSHOT)
        cmd = PREFIX + ['systemd-run','--unit='+unit,'--wait','--pipe','--collect',
            '-p','User=campusqa','-p','Group=campusqa','-p','LimitCORE=infinity',
            '-p','MemoryMax=64M','-p','MemorySwapMax=0','-p','TasksMax=8',
            '-p','RuntimeMaxSec=20','-p','TimeoutStopSec=2','-p','PrivateNetwork=yes',
            '-p','CPUQuota=100%','-p','UMask=0077','-p','WorkingDirectory=/home/campusqa/spike982/core-sentinel-10470',
            '/usr/bin/python3','-I','-S',GUEST,case]
        start=time.monotonic()
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
        objects=[json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
        pids=[]
        for obj in objects:
            if 'pid' in obj:pids.append(obj['pid'])
            if 'initial' in obj:pids.append(obj['initial']['pid'])
        pids=sorted(set(pids))
        observation=guest(OBSERVE,{'pids':pids,'before':before,'unit':unit,'since':before['utc']})
        result={'case':case,'command':cmd,'host_free_bytes_before':free,'before':before,
                'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,
                'observations':observation,'after':guest(SNAPSHOT),'wall_seconds':time.monotonic()-start}
        (out/(case+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(case,r.returncode,observation['kernel_pid_lines'],flush=True)
    (out/'positive-control.json').write_text(json.dumps({
        'case':'A','status':'inconclusive-not-run',
        'reason':'Installed Apport bounds CoreDump by 3/4 usable RAM, not the required 16 MiB. No adequate complete report footprint bound was established for this Python fixture. No normal zero-limit SIGABRT was launched. Exact-PID kernel sentinel diagnostics are separate evidence; missing reports alone are not a collector-positive-control pass.'},indent=2)+'\n')


if __name__ == '__main__':
    main()
