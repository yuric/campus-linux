"""One authorized SIGABRT arm. Guest-owned watchdog survives loss of host SSH."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import resource
import signal
import stat
import sys
import time
from watchdog import Watchdog, identity, read
from report_scan import scan

HERE = Path(__file__).resolve().parent
MIB = 1024**2
MARKER = b'public-apport-activation-1196'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

legacy = module('activation', HERE/'apport-activation-pair.py')
metadata = module('metadata', HERE/'metadata.py')
expected = module('expected', HERE/'apport-positive-preflight.py')
cmd = legacy.command


def allocations(root):
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not Path(parent,d).is_symlink()]
        for name in files:
            p = Path(parent,name)
            try:
                st = p.lstat()
                if stat.S_ISREG(st.st_mode):
                    result[str(p)] = st.st_blocks*512
            except FileNotFoundError:
                pass
    return result


def proc_metadata(pid, target_uid, target_gid):
    import apport.report
    fd = os.open('/proc/'+str(pid),os.O_PATH|os.O_DIRECTORY)
    groups = os.getgroups()
    try:
        r = apport.report.Report('Crash')
        r.pid = pid
        r['Signal']='6'; r['SignalName']='SIGABRT'
        r['ExecutablePath']=os.readlink('exe',dir_fd=fd)
        os.setgroups([]); os.setregid(-1,target_gid); os.setreuid(-1,target_uid)
        r.add_proc_info(proc_pid_fd=fd);r.add_user_info();r.add_os_info();r.add_package_info()
        r['_HooksRun']='no'
        required=('ProcEnviron','ProcStatus','ProcCmdline','ProcMaps','ExecutablePath','ExecutableTimestamp','ProcCwd')
        checks={k:k in r and bool(str(r[k])) and not str(r[k]).startswith('Error:') for k in required}
        if not all(checks.values()) or any(str(v).startswith('Error:') for v in r.values()):
            raise RuntimeError('required metadata missing/error')
        counter=metadata.Counter();r.write(counter)
        return dict(serialized_bytes=counter.size,sha256=counter.digest.hexdigest(),
                    required_readable=checks,euid=os.geteuid(),egid=os.getegid(),groups=os.getgroups(),
                    root_open_procfd=True,root_established_executable=r['ExecutablePath'])
    finally:
        os.seteuid(0);os.setegid(0);os.setgroups(groups);os.close(fd)


def main():
    if os.getuid()!=0 or os.uname().nodename!='lima-campus-linux-d5-noble-arm64':
        raise SystemExit('owned guest root required')
    arm=sys.argv[1]
    if arm not in ('positive','negative'):raise SystemExit('invalid arm')
    out=HERE/(arm+'.json')
    if out.exists():raise SystemExit('refuse repeated arm')
    account=pwd.getpwnam('campusqa')
    uid,gid=account.pw_uid,account.pw_gid
    unit='campus982-full-1213-'+arm
    result=dict(arm=arm,kind='bounded-SIGABRT',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),crash_sent=False,
                source_sha256={p.name:legacy.digest(p) for p in HERE.glob('*.py')},
                runtime_pass=False,cleanup_confirmed=False)
    crashdir=os.open('/var/crash',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    cgroup=Path('/sys/fs/cgroup/system.slice')/(unit+'.service')
    names=['_usr_bin_sleep.'+str(uid)+ext for ext in ('.crash','.upload','.uploaded')]
    reportfd=None; report_identity=None; collector_report_match=False
    watch=None; pid=None; collectors=[]; started=False; attribution_uncertain=False
    before_log=Path('/var/log/apport.log').stat()
    log_alloc=allocations('/var/log')
    owned_baseline=json.loads((HERE/'allocation-baseline.json').read_text())
    base_consumed=owned_baseline['consumed_bytes']
    last_account=0; accounting={}; samples=[]
    def exact_names():
        found={}
        for name in names:
            try:
                st=os.stat(name,dir_fd=crashdir,follow_symlinks=False)
                found[name]={'device':st.st_dev,'inode':st.st_ino,'uid':st.st_uid,
                             'mode':st.st_mode,'bytes':st.st_size,'allocated':st.st_blocks*512}
            except FileNotFoundError:pass
        return found
    def guard():
        nonlocal last_account,accounting
        now=time.monotonic()
        if (HERE/'STOP').exists():raise RuntimeError('host requested bounded stop')
        if not (HERE/'heartbeat').exists() or time.time()-(HERE/'heartbeat').stat().st_mtime>10:
            raise RuntimeError('host heartbeat lost')
        free=os.statvfs('/var/crash').f_bavail*os.statvfs('/var/crash').f_frsize
        found=exact_names()
        for name,v in found.items():
            if name!=names[0]:raise RuntimeError('unexpected exact sidecar; attribution uncertain')
            if max(v['bytes'],v['allocated'])>=32*MIB:raise RuntimeError('report early-stop threshold')
        if free<2*1024**3:raise RuntimeError('guest free-space floor')
        log=Path('/var/log/apport.log').stat()
        if log.st_ino!=before_log.st_ino or not 0<=log.st_size-before_log.st_size<=MIB:
            raise RuntimeError('collector log rotated/grew beyond bound')
        if now-last_account>=.5:
            explicit=sum(allocations(HERE).values())+sum(v['allocated'] for v in found.values())
            current=allocations('/var/log')
            growth=sum(max(0,v-log_alloc.get(k,0)) for k,v in current.items())
            accounting=dict(explicit_allocated=explicit,log_positive_deltas_unattributed=growth,
                            conservative_total=base_consumed+explicit+growth,guest_free=free)
            if explicit>=48*MIB or accounting['conservative_total']>=192*MIB:
                raise RuntimeError('explicit/cumulative early-stop threshold')
            samples.append(dict(monotonic=now,**accounting));last_account=now
            if len(samples)>160:raise RuntimeError('monitor sample bound')
    def discover(expected_argv, baseline, crash_ticks):
        nonlocal attribution_uncertain,collector_report_match
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():continue
            try:
                argv=read(entry/'cmdline').rstrip(b'\0').split(b'\0')
                if b'/usr/share/apport/apport' not in argv:continue
                if ('-p'+str(pid)).encode() not in argv and ('-P'+str(pid)).encode() not in argv:continue
                ident=identity(int(entry.name))
                if argv!=expected_argv or (entry/'exe').resolve()!=Path('/usr/bin/python3').resolve():
                    attribution_uncertain=True;raise RuntimeError('collector target match but unexpected exact argv/executable')
                if legacy.digest(Path('/usr/share/apport/apport'))!=expected.EXPECTED['/usr/share/apport/apport'][1]:
                    attribution_uncertain=True;raise RuntimeError('collector source changed')
                if (ident['pid'],ident['start_ticks']) in baseline or ident['start_ticks']<crash_ticks:
                    attribution_uncertain=True;raise RuntimeError('collector outside crash window')
                if ident['pid'] not in watch.owned:
                    watch.retain(ident['pid'],expected=ident)
                    collectors.append(dict(pid=ident['pid'],start_ticks=ident['start_ticks'],
                        argv=[v.decode() for v in argv],executable_sha256=legacy.digest(entry/'exe'),
                        namespaces={n:str((entry/'ns'/n).readlink()) for n in ('pid','mnt')}))
                if report_identity:
                    for f in (entry/'fd').iterdir():
                        try:
                            st=f.stat()
                            if (st.st_dev,st.st_ino)==report_identity:collector_report_match=True
                        except FileNotFoundError:pass
            except (FileNotFoundError,ProcessLookupError):pass
    try:
        if exact_names():raise RuntimeError('preexisting exact crash/sidecar path')
        for path,(_,sha) in expected.EXPECTED.items():
            if sha and legacy.digest(Path(path))!=sha:raise RuntimeError('installed source mismatch')
        if Path('/proc/sys/kernel/core_pattern').read_text().strip()!='|/usr/share/apport/apport -p%p -s%s -c%c -d%d -P%P -u%u -g%g -F%F -- %E':
            raise RuntimeError('unexpected core pattern')
        guard()
        launch=['systemd-run','--unit='+unit,'--collect','-p','User=campusqa','-p','Group=campusqa',
            '-p','NoNewPrivileges=yes','-p','LimitCORE=infinity','-p','MemoryMax=64M',
            '-p','MemorySwapMax=0','-p','TasksMax=8','-p','RuntimeMaxSec=90','-p','TimeoutStopSec=2',
            '-p','PrivateNetwork=no','-p','CPUQuota=100%','-p','UMask=0077',
            '-p','WorkingDirectory='+str(HERE),'/usr/bin/python3','-B','-I','-S',str(HERE/'apport-activation-launch.py'),arm]
        result['command']=launch;cmd(launch);started=True
        end=time.monotonic()+5
        while time.monotonic()<end:
            pid=int(cmd(['systemctl','show',unit,'-p','MainPID','--value']))
            p=Path('/proc')/str(pid)
            if pid and (p/'exe').resolve()==Path('/usr/bin/sleep'):break
            time.sleep(.02)
        else:raise RuntimeError('ELF launch deadline')
        watch=Watchdog(75,guard);watch.retain(pid);watch.send(pid,signal.SIGSTOP)
        end=time.monotonic()+1
        while True:
            status=dict(line.split(':',1) for line in read(p/'status').decode().splitlines())
            if status['State'].strip().startswith('T'):break
            if time.monotonic()>end:raise RuntimeError('target failed to stop')
            time.sleep(.01)
        names.append('_usr_bin_sleep.'+str(uid)+'.'+str(pid)+'.hanging')
        if exact_names():raise RuntimeError('preexisting PID-specific report/sidecar')
        maps=read(p/'maps',65536).decode().splitlines()
        mapped=sum(int(row.split()[0].split('-')[1],16)-int(row.split()[0].split('-')[0],16) for row in maps)
        pathbytes=sum(len(row.split(maxsplit=5)[5].encode())+1 for row in maps if len(row.split(maxsplit=5))==6)
        namespaces={n:[str((p/'ns'/n).readlink()),str(Path('/proc/1/ns',n).readlink())] for n in ('pid','mnt')}
        predicates=dict(stopped=status['State'].strip().startswith('T'),one_thread=int(status['Threads'])==1,
            core_limit=resource.prlimit(pid,resource.RLIMIT_CORE)==((0,0) if arm=='positive' else (1,1)),
            as_limit=resource.prlimit(pid,resource.RLIMIT_AS)==(8388608,8388608),maps=mapped<=8388608,
            vmas=len(maps)<=64,pathnames=pathbytes<=65536,nnp=status['NoNewPrivs'].strip()=='1',
            seccomp=status['Seccomp'].strip()==('0' if arm=='positive' else '2'),
            same_namespaces=all(a==b for a,b in namespaces.values()),
            environment=read(p/'environ',4096)==b'LANG=C\0PATH=/usr/bin:/bin\0CAMPUS982_SYNTHETIC='+MARKER+b'\0',
            argv=read(p/'cmdline')==b'/usr/bin/sleep\x0090\0',
            uid=list(map(int,status['Uid'].split()))==[uid]*4,gid=list(map(int,status['Gid'].split()))==[gid]*4,
            filter=read(p/'coredump_filter').strip()==b'00000001',
            descriptors=set(f.name for f in (p/'fd').iterdir())<={'0','1','2'})
        result.update(pid=pid,start_ticks=watch.owned[pid]['identity']['start_ticks'],predicates=predicates,
            namespaces=namespaces,cgroup=read(p/'cgroup').decode(),mapped_bytes=mapped,vmas=len(maps),pathname_bytes=pathbytes,
            executable_sha256=legacy.digest(p/'exe'),target_uid=uid,target_gid=gid)
        if not all(predicates.values()):raise RuntimeError('stopped target admission failed')
        result['metadata']=proc_metadata(pid,uid,gid)
        expected_argv=[b'/usr/bin/python3',b'/usr/share/apport/apport',('-p'+str(pid)).encode(),b'-s6',
                      b'-c0' if arm=='positive' else b'-c1',b'-d1',('-P'+str(pid)).encode(),
                      ('-u'+str(uid)).encode(),('-g'+str(gid)).encode(),b'-F',b'--',b'!usr!bin!sleep']
        baseline=set()
        for entry in Path('/proc').iterdir():
            if entry.name.isdigit():
                try:
                    i=identity(int(entry.name));baseline.add((i['pid'],i['start_ticks']))
                except (FileNotFoundError,ProcessLookupError):pass
        since=cmd(['date','-u','+%Y-%m-%d %H:%M:%S UTC'])
        guard()
        if exact_names() or identity(pid)!=watch.owned[pid]['identity']:raise RuntimeError('last identity/collision check')
        crash_ticks=int(float(read('/proc/uptime').split()[0])*os.sysconf('SC_CLK_TCK'))
        watch.deadline=time.monotonic()+60
        watch.send(pid,signal.SIGABRT);watch.send(pid,signal.SIGCONT);result['crash_sent']=True
        quiet=None
        while True:
            discover(expected_argv,baseline,crash_ticks)
            found=exact_names()
            if names[0] in found and reportfd is None:
                reportfd=os.open(names[0],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=crashdir)
                st=os.fstat(reportfd)
                if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or st.st_uid!=uid:raise RuntimeError('report ownership/type')
                report_identity=(st.st_dev,st.st_ino)
                result['report_created']=dict(device=st.st_dev,inode=st.st_ino,uid=st.st_uid)
            watch.tick()
            if all(not watch.live(p) for p in watch.owned):
                quiet=quiet or time.monotonic()
                if time.monotonic()-quiet>=3:break
            else:quiet=None
            time.sleep(.02)
        result['collectors']=collectors;result['quiet_complete']=True
        log=Path('/var/log/apport.log').stat();delta=log.st_size-before_log.st_size
        with open('/var/log/apport.log','rb') as stream:
            stream.seek(before_log.st_size);lines=stream.read(delta).decode().splitlines()
        own=[line for line in lines if ('pid '+str(pid)+',') in line]
        kernel=cmd(['journalctl','-k','--since',since,'--no-pager','-o','cat'],cap=MIB,timeout=5)
        own_kernel=[line for line in kernel.splitlines() if ('Process '+str(pid)+'(') in line]
        result.update(apport_pid_lines=own,kernel_pid_lines=own_kernel,log_delta_bytes=delta,
                      marker_in_attributable_log=any(MARKER.decode() in line for line in own+own_kernel))
        if arm=='positive':
            if reportfd is None or not any('signal 6, core limit 0, dump mode 1' in line for line in own):
                raise RuntimeError('no complete attributable positive report/collector log')
            st=os.fstat(reportfd)
            if st.st_uid!=uid or stat.S_IMODE(st.st_mode)!=0o640:raise RuntimeError('report not completed')
            with os.fdopen(os.dup(reportfd),'rb') as stream:inspection=scan(stream,MARKER)
            binding=inspection.pop('binding')
            proc=dict(line.split(':',1) for line in binding['ProcStatus'].splitlines())
            bound=(binding['ExecutablePath']=='/usr/bin/sleep' and binding['Signal']=='6' and
                   binding['ProcCmdline']=='/usr/bin/sleep 90' and int(proc['Pid'])==pid and
                   list(map(int,proc['Uid'].split()))==[uid]*4 and binding['_HooksRun']=='no')
            result['report_scan']=inspection;result['report_binding_verified']=bound
            result['collector_open_report_inode_observed']=collector_report_match
            if not bound or inspection['marker_count']<1:raise RuntimeError('positive binding/decoded marker absent')
        else:
            if collectors or own or exact_names() or not any('RLIMIT_CORE set to 1' in line for line in own_kernel):
                raise RuntimeError('negative sentinel suppression not proved')
        result['runtime_pass']=True
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc),runtime_pass=False)
    finally:
        result['collectors']=collectors
        stopped=True
        if watch:
            try:
                stopped=watch.stop();result['retained_identities']=watch.receipt()
            except Exception as exc:
                stopped=False;result['watchdog_cleanup_error']=str(exc)
        if started:
            try:cmd(['systemctl','stop',unit],timeout=5)
            except Exception as exc:stopped=False;result['unit_cleanup_error']=str(exc)
        result['cgroup_absent']=not cgroup.exists()
        # Never remove an unbound/partial report merely because its name matches.
        if reportfd is not None:
            try:
                current=os.stat(names[0],dir_fd=crashdir,follow_symlinks=False)
                if stopped and result.get('report_binding_verified') and (current.st_dev,current.st_ino)==report_identity and stat.S_ISREG(current.st_mode) and current.st_nlink==1 and current.st_uid==uid:
                    os.unlink(names[0],dir_fd=crashdir);result['owned_report_removed']=True
                else:result['owned_report_removed']=False
            except Exception as exc:result['report_cleanup_error']=str(exc)
            os.close(reportfd)
        remaining=exact_names();result['remaining_exact_paths']=remaining
        result['cleanup_confirmed']=stopped and result['cgroup_absent'] and not remaining and not attribution_uncertain
        result['runtime_pass']=result['runtime_pass'] and result['cleanup_confirmed']
        result['accounting_samples']=samples
        result['collector_stop_exercised']=False # ordinary completion is not forced collector-stop evidence
        if watch:watch.close()
        os.close(crashdir)
        payload=json.dumps(result,indent=2)+'\n'
        if len(payload)>MIB:raise RuntimeError('receipt cap')
        with open(out,'x') as stream:stream.write(payload)
    return 0 if result['runtime_pass'] else 1

if __name__=='__main__':sys.exit(main())
