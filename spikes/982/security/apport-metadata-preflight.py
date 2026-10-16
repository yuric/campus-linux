#!/usr/bin/env python3
"""Non-crashing eight-MiB packaged ELF/metadata preflight for direction 1196.

Only SIGSTOP and SIGKILL are sent through an owned pidfd. This cannot establish
collector activation, and cannot authorize a later crash by itself.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import pwd
import signal
import subprocess
import time


LAUNCH = r'''
import ctypes,os,resource
if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64' or os.getuid()!=1000:
    raise SystemExit('wrong disposable host/user')
libc=ctypes.CDLL(None,use_errno=True)
libc.execve.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.POINTER(ctypes.c_char_p)]
argv=(ctypes.c_char_p*3)(b'/usr/bin/sleep',b'20',None)
env=(ctypes.c_char_p*4)(b'LANG=C',b'PATH=/usr/bin:/bin',b'CAMPUS982_SYNTHETIC=public-apport-positive-1196',None)
with open('/proc/self/coredump_filter','w') as f:f.write('1')
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
resource.setrlimit(resource.RLIMIT_AS,(8388608,8388608))
libc.execve(b'/usr/bin/sleep',argv,env)
os._exit(24)
'''


class Counter:
    def __init__(self):
        self.size = 0
        self.digest = hashlib.sha256()

    def write(self, data):
        self.size += len(data)
        if self.size > 1024**2:
            raise RuntimeError('non-core metadata exceeds 1 MiB')
        self.digest.update(data)
        return len(data)

    def tell(self):
        return self.size


def cmd(args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=10)
    if len(p.stdout) + len(p.stderr) > 65536:
        raise RuntimeError('unexpected command output size')
    if p.returncode:
        raise RuntimeError('fixed preflight command failed: ' + p.stderr[:1000])
    return p.stdout.strip()


def main():
    if os.uname().nodename != 'lima-campus-linux-d5-noble-arm64' or os.getuid() != 0:
        raise SystemExit('owned guest root control connection required')
    import apport.report
    unit = 'campus982-sleep-preflight-1196-' + str(os.getpid())
    command = ['systemd-run', '--unit=' + unit, '--collect', '-p', 'User=campusqa',
               '-p', 'Group=campusqa', '-p', 'NoNewPrivileges=yes',
               '-p', 'LimitCORE=infinity', '-p', 'MemoryMax=64M', '-p', 'MemorySwapMax=0',
               '-p', 'TasksMax=8', '-p', 'RuntimeMaxSec=20', '-p', 'TimeoutStopSec=2',
               '-p', 'PrivateNetwork=no', '-p', 'CPUQuota=100%', '-p', 'UMask=0077',
               '-p', 'WorkingDirectory=/home/campusqa/spike982/core-sentinel-10470',
               '/usr/bin/python3', '-B', '-I', '-S', '-c', LAUNCH]
    result = {'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'kind': 'non-crashing-sleep-preflight', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'command': command, 'collector_tested': False, 'unit_manager': 'system',
              'launch_source_sha256': hashlib.sha256(LAUNCH.encode()).hexdigest()}
    pidfd = procfd = None
    stage = "launch"
    original_groups = os.getgroups()
    try:
        cmd(command)
        deadline = time.monotonic() + 5
        while True:
            pid = int(cmd(['systemctl', 'show', unit, '-p', 'MainPID', '--value']))
            p = Path('/proc') / str(pid)
            if pid and p.exists() and (p/'exe').resolve() == Path('/usr/bin/sleep'):
                break
            if time.monotonic() > deadline:
                raise RuntimeError('sleep failed to exec within five seconds')
            time.sleep(.05)
        stage = 'stop-and-identify'
        pidfd = os.pidfd_open(pid)
        procfd = os.open(p, os.O_RDONLY | os.O_PATH | os.O_DIRECTORY)
        signal.pidfd_send_signal(pidfd, signal.SIGSTOP)
        for _ in range(100):
            status = dict(line.split(':', 1) for line in (p/'status').read_text().splitlines())
            if status['State'].strip().startswith('T'):
                break
            time.sleep(.01)
        maps = (p/'maps').read_text().splitlines()
        mapped = sum(int(line.split()[0].split('-')[1],16)-int(line.split()[0].split('-')[0],16) for line in maps)
        paths_bytes = sum(len(line.split(maxsplit=5)[5].encode())+1 for line in maps if len(line.split(maxsplit=5))==6)
        env = (p/'environ').read_bytes()
        argv = (p/'cmdline').read_bytes()
        expected_env = b'LANG=C\0PATH=/usr/bin:/bin\0CAMPUS982_SYNTHETIC=public-apport-positive-1196\0'
        predicates = {
            'stopped': status['State'].strip().startswith('T'), 'single_thread': int(status['Threads'])==1,
            'address_limit_8mib': resource.prlimit(pid,resource.RLIMIT_AS)==(8388608,8388608),
            'core_limit_zero': resource.prlimit(pid,resource.RLIMIT_CORE)==(0,0),
            'mapped_under_8mib': mapped<=8388608, 'at_most_64_vmas': len(maps)<=64,
            'pathnames_under_64kib': paths_bytes<=65536, 'allowlisted_environment': env==expected_env,
            'environment_under_4kib':len(env)<=4096,'fixed_argv':argv==b'/usr/bin/sleep\x0020\x00',
            'filter_one':(p/'coredump_filter').read_text().strip()=='00000001',
            'no_new_privileges':status['NoNewPrivs'].strip()=='1',
            'same_mount_namespace':(p/'ns/mnt').readlink()==Path('/proc/1/ns/mnt').readlink(),
            'same_pid_namespace':(p/'ns/pid').readlink()==Path('/proc/1/ns/pid').readlink(),
        }
        result.update(pid=pid,start_ticks=(p/'stat').read_text().rsplit(')',1)[1].split()[19],
                      boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                      mapped_bytes=mapped,vmas=len(maps),pathname_bytes=paths_bytes,environment_bytes=len(env),
                      predicates=predicates,executable_sha256=hashlib.sha256((p/'exe').read_bytes()).hexdigest())
        if not all(predicates.values()):
            raise RuntimeError('stopped ELF preflight predicates failed')
        stage = 'target-credentials'
        account = pwd.getpwnam('campusqa')
        uids = list(map(int, status['Uid'].split()))
        gids = list(map(int, status['Gid'].split()))
        target_uid, target_gid = uids[0], gids[0]
        result['target_credentials'] = dict(uids=uids, gids=gids,
            account_uid=account.pw_uid, account_gid=account.pw_gid)
        if uids != [account.pw_uid]*4 or gids != [account.pw_gid]*4:
            raise RuntimeError('target credentials differ from disposable account')
        stage = 'root-executable-path'
        executable = os.readlink('exe', dir_fd=procfd)
        if executable != '/usr/bin/sleep':
            raise RuntimeError('stopped target executable changed')
        if (p/'stat').read_text().rsplit(')',1)[1].split()[19] != result['start_ticks']:
            raise RuntimeError('target start identity changed')
        report = apport.report.Report('Crash')
        report.pid = pid
        report['Signal']='6'
        report['SignalName']='SIGABRT'
        # Apport 2.28.3 seeds this as root and retains the proc descriptor.
        report['ExecutablePath'] = executable
        stage = 'drop-credentials'
        try:
            os.setgroups([])
            os.setregid(-1, target_gid)
            os.setreuid(-1, target_uid)
            result['metadata_credentials'] = dict(euid=os.geteuid(), egid=os.getegid(),
                supplementary_groups=os.getgroups(), root_open_procfd=True,
                root_established_executable=executable)
            if os.getgroups() or os.geteuid()!=target_uid or os.getegid()!=target_gid:
                raise RuntimeError('metadata credential context mismatch')
            stage = 'add_proc_info'
            report.add_proc_info(proc_pid_fd=procfd)
            stage = 'add_user_info'
            report.add_user_info()
            stage = 'add_os_info'
            report.add_os_info()
            stage = 'add_package_info'
            report.add_package_info()
            report['_HooksRun']='no'
            stage = 'serialize-metadata'
            counter = Counter()
            report.write(counter)
            result['metadata']={'serialized_bytes':counter.size,'sha256':counter.digest.hexdigest(),
                                'field_bytes':{k:len(str(v).encode()) for k,v in report.items()},
                                'package':report.get('Package'),'executable':report.get('ExecutablePath')}
        finally:
            os.seteuid(0)
            os.setegid(0)
            os.setgroups(original_groups)
        stage = 'verify-target-identity'
        if (p/'stat').read_text().rsplit(')',1)[1].split()[19] != result['start_ticks']:
            raise RuntimeError('target start identity changed during metadata')
        result['preflight_pass']=True
    except Exception as exc:
        result['preflight_pass']=False
        result['failure_stage']=stage
        result['error_type']=type(exc).__name__
        result['error']=str(exc)
    finally:
        if pidfd is not None:
            try:
                signal.pidfd_send_signal(pidfd,signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.close(pidfd)
        if procfd is not None:
            os.close(procfd)
        subprocess.run(['systemctl','stop',unit],capture_output=True,timeout=5)
        result['unit_cgroup_remaining']=(Path('/sys/fs/cgroup/system.slice')/(unit+'.service')).exists()
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
