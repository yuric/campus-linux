"""Read only this experiment's identities/receipts; no ambient content scan."""
import hashlib
import json
import os
from pathlib import Path
import stat
from watchdog import identity

if os.getuid()!=0 or os.uname().nodename!='lima-campus-linux-d5-noble-arm64':
    raise SystemExit('owned guest root required')
HERE=Path(__file__).resolve().parent
r={'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
   'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'owned_sources':{},'support_receipt_scans':{}}
for p in HERE.glob('*.py'):r['owned_sources'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('positive.json','negative.json','reinspection.json'):
    data=(HERE/name).read_bytes()
    assert len(data)<=1024**2
    r['support_receipt_scans'][name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                                     'public_marker_count':data.count(b'public-apport-activation-1196')}
r['identities_exited']=[]
for name in ('positive.json','negative.json'):
    receipt=json.loads((HERE/name).read_text())
    for item in receipt['retained_identities']:
        try:gone=identity(item['pid'])['start_ticks']!=item['start_ticks']
        except FileNotFoundError:gone=True
        r['identities_exited'].append(dict(pid=item['pid'],start_ticks=item['start_ticks'],exited=gone))
r['owned_cgroups_absent']={name:not (Path('/sys/fs/cgroup/system.slice')/(name+'.service')).exists() for name in (
    'campus982-full-1213-positive','campus982-full-1213-negative',
    'campus982-full-monitor-1213-positive','campus982-full-monitor-1213-negative','campus982-metadata-1213-2318')}
r['exact_report_paths_absent']={name:not os.path.lexists('/var/crash/'+name) for name in (
    '_usr_bin_sleep.1000.crash','_usr_bin_sleep.1000.upload','_usr_bin_sleep.1000.uploaded',
    '_usr_bin_sleep.1000.2445.hanging','_usr_bin_sleep.1000.2610.hanging')}
r['guest_free_bytes']=os.statvfs('/').f_bavail*os.statvfs('/').f_frsize
r['owned_files']={str(p.relative_to(HERE)):{'bytes':p.stat().st_size,'allocated':p.stat().st_blocks*512}
                  for p in HERE.rglob('*') if p.is_file() and not p.is_symlink()}
r['owned_allocated_bytes']=sum(x['allocated'] for x in r['owned_files'].values())
r['pass']=all(r['owned_cgroups_absent'].values()) and all(r['exact_report_paths_absent'].values()) and all(x['exited'] for x in r['identities_exited']) and r['guest_free_bytes']>=2*1024**3
print(json.dumps(r,indent=2))
