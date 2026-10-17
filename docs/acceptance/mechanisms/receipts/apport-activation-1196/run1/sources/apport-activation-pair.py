#!/usr/bin/env python3
"""One arm of the activation-only matched control. Never sends SIGABRT.

Run as root only inside the disposable guest. No ambient crash contents are read
or removed. All observations and cleanup concern the exact fixture/collector.
"""
import datetime
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import resource
import select
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPORTS = [Path('/var/crash/_usr_bin_sleep.1000' + ext) for ext in ('.crash', '.upload', '.uploaded')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, cap=65536, timeout=10):
    # Drain bounded output while running; overflow is failure, not silent truncation.
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = bytearray()
    deadline = time.monotonic() + timeout
    try:
        while True:
            if time.monotonic() > deadline:
                raise RuntimeError('command deadline')
            ready, _, _ = select.select([proc.stdout], [], [], .05)
            if ready:
                data = os.read(proc.stdout.fileno(), 8192)
                if not data:
                    break
                output.extend(data)
                if len(output) > cap:
                    raise RuntimeError('command output cap')
        code = proc.wait(timeout=1)
        if code:
            raise RuntimeError('fixed command failed: ' + output.decode(errors='replace')[:1000])
        return output.decode().strip()
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        proc.stdout.close()


def metadata():
    log = Path('/var/log/apport.log')
    st = log.stat() if log.exists() else None
    allocated = 0
    for root, dirs, files in os.walk('/var/log', followlinks=False):
        for name in files:
            path = Path(root) / name
            if not path.is_symlink():
                allocated += path.stat().st_blocks * 512
    return dict(guest_free_bytes=shutil.disk_usage('/var/crash').free,
                report_paths={str(p): os.path.lexists(p) for p in REPORTS},
                log_inode=st.st_ino if st else None, log_size=st.st_size if st else 0,
                all_var_log_allocated_bytes_upper_bound=allocated)


def cleanup(unit, pidfd):
    if pidfd is not None:
        try:
            signal.pidfd_send_signal(pidfd, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.close(pidfd)
    command(['systemctl', 'stop', unit], timeout=5)
    return not (Path('/sys/fs/cgroup/system.slice') / (unit + '.service')).exists()


def main():
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64' or os.getuid() != 0:
        raise SystemExit('owned guest root required')
    arm = sys.argv[1]
    if arm not in ('positive', 'negative'):
        raise SystemExit('unknown arm')
    unit = 'campus982-activation-1196-' + arm + '-' + str(os.getpid())
    result = dict(kind='SIGQUIT-activation-only', arm=arm, unit_manager='system',
                  utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source_sha256={p.name: digest(p) for p in [Path(__file__), HERE/'apport-activation-launch.py', HERE/'core-sentinel-probe.py', HERE/'apport-positive-preflight.py']},
                  cleanup_source_sha256=hashlib.sha256(inspect.getsource(cleanup).encode()).hexdigest(),
                  full_report_proved=False, crash_sent=False)
    pidfd = None
    started = False
    try:
        spec = importlib.util.spec_from_file_location('identity', HERE/'apport-positive-preflight.py')
        identity = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(identity)
        for path, (_, expected) in identity.EXPECTED.items():
            if expected and digest(Path(path)) != expected:
                raise RuntimeError('installed source mismatch')
        before = result['before'] = metadata()
        if before['guest_free_bytes'] < 2*1024**3 or any(before['report_paths'].values()):
            raise RuntimeError('guest floor or preexisting exact report path')
        pattern = Path('/proc/sys/kernel/core_pattern').read_text().strip()
        result['core_pattern'] = pattern
        if pattern != '|/usr/share/apport/apport -p%p -s%s -c%c -d%d -P%P -u%u -g%g -F%F -- %E':
            raise RuntimeError('unexpected collector pattern')
        cmd = ['systemd-run', '--unit='+unit, '--collect', '-p', 'User=campusqa', '-p', 'Group=campusqa',
               '-p', 'NoNewPrivileges=yes', '-p', 'LimitCORE=infinity', '-p', 'MemoryMax=64M',
               '-p', 'MemorySwapMax=0', '-p', 'TasksMax=8', '-p', 'RuntimeMaxSec=90',
               '-p', 'TimeoutStopSec=2', '-p', 'PrivateNetwork=no', '-p', 'CPUQuota=100%',
               '-p', 'UMask=0077', '-p', 'WorkingDirectory='+str(HERE),
               '/usr/bin/python3', '-B', '-I', '-S', str(HERE/'apport-activation-launch.py'), arm]
        result['command'] = cmd
        command(cmd)
        started = True
        deadline = time.monotonic()+5
        while True:
            pid = int(command(['systemctl', 'show', unit, '-p', 'MainPID', '--value']))
            p = Path('/proc')/str(pid)
            if pid and (p/'exe').resolve() == Path('/usr/bin/sleep'):
                break
            if time.monotonic()>deadline:
                raise RuntimeError('ELF exec deadline')
            time.sleep(.05)
        pidfd = os.pidfd_open(pid)
        signal.pidfd_send_signal(pidfd, signal.SIGSTOP)
        for _ in range(100):
            status = dict(row.split(':', 1) for row in (p/'status').read_text().splitlines())
            if status['State'].strip().startswith('T'):
                break
            time.sleep(.01)
        maps = (p/'maps').read_text().splitlines()
        mapped = sum(int(row.split()[0].split('-')[1],16)-int(row.split()[0].split('-')[0],16) for row in maps)
        env = (p/'environ').read_bytes()
        fds = {f.name: str(f.readlink()) for f in (p/'fd').iterdir()}
        expected = b'LANG=C\0PATH=/usr/bin:/bin\0CAMPUS982_SYNTHETIC=public-apport-activation-1196\0'
        namespaces = {n: [str((p/('ns/'+n)).readlink()), str(Path('/proc/1/ns/'+n).readlink())] for n in ('mnt','pid')}
        limits = resource.prlimit(pid,resource.RLIMIT_CORE)
        predicates = dict(stopped=status['State'].strip().startswith('T'), single_thread=int(status['Threads'])==1,
                          same_mount_namespace=namespaces['mnt'][0]==namespaces['mnt'][1],
                          same_pid_namespace=namespaces['pid'][0]==namespaces['pid'][1],
                          core_limit=limits==((0,0) if arm=='positive' else (1,1)),
                          address_limit=resource.prlimit(pid,resource.RLIMIT_AS)==(8388608,8388608),
                          map_bound=mapped<=8388608, vma_bound=len(maps)<=64,
                          environment=env==expected, argv=(p/'cmdline').read_bytes()==b'/usr/bin/sleep\x0090\0',
                          filter_one=(p/'coredump_filter').read_text().strip()=='00000001',
                          nnp=status['NoNewPrivs'].strip()=='1', only_standard_fds=set(fds)<= {'0','1','2'},
                          seccomp=status['Seccomp'].strip()==('0' if arm=='positive' else '2'))
        start_ticks=(p/'stat').read_text().rsplit(')',1)[1].split()[19]
        result.update(pid=pid, start_ticks=start_ticks, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                      predicates=predicates, namespaces=namespaces, mapped_bytes=mapped, vmas=len(maps),
                      environment_bytes=len(env), fd_targets=fds, core_limit=limits, executable_sha256=digest(p/'exe'))
        if not all(predicates.values()):
            raise RuntimeError('ELF preflight failed')
        since = command(['date','-u','+%Y-%m-%d %H:%M:%S UTC'])
        # Still stopped: repeat identity/limit checks directly before the only crash signal.
        if (p/'stat').read_text().rsplit(')',1)[1].split()[19] != start_ticks or resource.prlimit(pid,resource.RLIMIT_CORE)!=limits:
            raise RuntimeError('identity/limits changed')
        signal.pidfd_send_signal(pidfd, signal.SIGQUIT)
        signal.pidfd_send_signal(pidfd, signal.SIGCONT)
        result['crash_sent']=True
        start=time.monotonic(); seen={}; quiet=None
        while time.monotonic()-start < 60:
            active=[]
            for candidate in Path('/proc').iterdir():
                if not candidate.name.isdigit():
                    continue
                try:
                    argv=(candidate/'cmdline').read_bytes()[:8192].split(b'\0')
                    if b'/usr/share/apport/apport' not in argv or ('-p'+str(pid)).encode() not in argv:
                        continue
                    ticks=(candidate/'stat').read_text().rsplit(')',1)[1].split()[19]
                    active.append(candidate.name)
                    seen[candidate.name]=dict(start_ticks=ticks,argv=[a.decode() for a in argv if a])
                except (OSError,UnicodeError,IndexError):
                    continue
            exited=bool(select.select([pidfd],[],[],0)[0])
            if exited and not active:
                quiet=quiet or time.monotonic()
                if time.monotonic()-quiet>=3:
                    break
            else:
                quiet=None
            time.sleep(.02)
        result.update(observation_seconds=time.monotonic()-start, collectors=seen, quiet_complete=quiet is not None and time.monotonic()-quiet>=3)
        after=result['after']=metadata()
        delta=after['log_size']-before['log_size']
        if after['log_inode'] != before['log_inode'] or not 0<=delta<=1048576:
            raise RuntimeError('collector log rotation/size: inconclusive')
        with open('/var/log/apport.log','rb') as stream:
            stream.seek(before['log_size']); data=stream.read(delta)
        own=[line for line in data.decode().splitlines() if ('pid '+str(pid)+',') in line]
        kernel=command(['journalctl','-k','--since',since,'--no-pager','-o','cat'],cap=1048576,timeout=5)
        own_kernel=[line for line in kernel.splitlines() if ('Process '+str(pid)+'(') in line]
        result.update(apport_pid_lines=own,kernel_pid_lines=own_kernel,log_delta_bytes=delta)
        positive=any('signal 3, core limit 0, dump mode 1' in line for line in own)
        negative=any('RLIMIT_CORE set to 1' in line for line in own_kernel) and not own and not seen
        result['activation_only_pass']=bool(result['quiet_complete'] and not any(after['report_paths'].values()) and (positive if arm=='positive' else negative))
        if after['guest_free_bytes']<2*1024**3 or max(0,after['all_var_log_allocated_bytes_upper_bound']-before['all_var_log_allocated_bytes_upper_bound'])>256*1024**2:
            raise RuntimeError('post-case operational storage threshold')
    except Exception as exc:
        result.update(activation_only_pass=False,error_type=type(exc).__name__,error=str(exc))
    finally:
        if started:
            result['cgroup_absent_after_cleanup']=cleanup(unit,pidfd)
            if not result['cgroup_absent_after_cleanup']:
                result['activation_only_pass']=False
        print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
