"""Reinspect the retained positive report after a host-independent parser failure.

No crash, target launch, collector launch or global policy change. Exact captured
inode and exited stable identities required before inspection and owned unlink.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from watchdog import identity, read
from report_scan import scan

if os.getuid()!=0 or os.uname().nodename!='lima-campus-linux-d5-noble-arm64':
    raise SystemExit('owned guest root required')
HERE=Path(__file__).resolve().parent
old=json.loads((HERE/'positive.json').read_text())
r={'kind':'same-report-reinspection-no-new-crash','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'report_scan.py',HERE/'watchdog.py')},'original_receipt_sha256':hashlib.sha256((HERE/'positive.json').read_bytes()).hexdigest(),'crash_sent':False,'pass':False}
fd=directory=None
try:
    assert old['crash_sent'] and old['cgroup_absent'] and old['quiet_complete']
    assert old['error']=='dictionary update sequence element #0 has length 1; 2 is required'
    assert old['boot_id']==read('/proc/sys/kernel/random/boot_id').decode().strip()
    for item in old['retained_identities']:
        assert item['exited']
        try:
            now=identity(item['pid'])
            assert now['start_ticks']!=item['start_ticks'], 'original retained process remains'
        except FileNotFoundError:pass
    assert not Path('/sys/fs/cgroup/system.slice/campus982-full-1213-positive.service').exists()
    pid=old['pid'];uid=old['target_uid']
    name='_usr_bin_sleep.'+str(uid)+'.crash'
    directory=os.open('/var/crash',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    for suffix in ('.upload','.uploaded','.'+str(pid)+'.hanging'):
        try:os.stat('_usr_bin_sleep.'+str(uid)+suffix,dir_fd=directory,follow_symlinks=False)
        except FileNotFoundError:continue
        raise RuntimeError('unexpected sidecar')
    fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
    st=os.fstat(fd);original=old['report_created']
    assert (st.st_dev,st.st_ino,st.st_uid)==(original['device'],original['inode'],uid)
    assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o640
    with os.fdopen(os.dup(fd),'rb') as stream:
        inspection=scan(stream,b'public-apport-activation-1196')
    binding=inspection.pop('binding')
    proc=dict(line.split(':',1) for line in binding['ProcStatus'].splitlines() if line.strip())
    assert binding['ExecutablePath']=='/usr/bin/sleep' and binding['Signal']=='6'
    assert binding['ProcCmdline']=='/usr/bin/sleep 90' and int(proc['Pid'])==pid
    assert list(map(int,proc['Uid'].split()))==[uid]*4 and binding['_HooksRun']=='no'
    assert inspection['marker_count']>0
    assert any('signal 6, core limit 0, dump mode 1' in line for line in old['apport_pid_lines'])
    r.update(report_scan=inspection,report_binding_verified=True,report_identity=original,
             exact_collector=old['collectors'],prior_retained_identities_exited=old['retained_identities'])
    current=os.stat(name,dir_fd=directory,follow_symlinks=False)
    assert (current.st_dev,current.st_ino,current.st_size,current.st_mtime_ns)==(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
    assert stat.S_ISREG(current.st_mode) and current.st_nlink==1 and current.st_uid==uid
    os.unlink(name,dir_fd=directory)
    try:os.stat(name,dir_fd=directory,follow_symlinks=False)
    except FileNotFoundError:r['owned_report_removed']=True
    r['pass']=r.get('owned_report_removed',False)
except Exception as exc:r.update(error_type=type(exc).__name__,error=str(exc))
finally:
    if fd is not None:os.close(fd)
    if directory is not None:os.close(directory)
    print(json.dumps(r,indent=2))
sys.exit(0 if r['pass'] else 1)
