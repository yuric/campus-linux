#!/usr/bin/env python3
"""Bounded Mac controller for direction1196; existing Lima must already be running."""
import datetime
import hashlib
import json
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PREFIX = ['/opt/homebrew/bin/limactl', 'shell', 'campus-linux-d5-noble-arm64', 'sudo']
GUEST = '/home/campusqa/spike982/apport-activation-1196'
FILES = ['apport-activation-pair.py','apport-activation-launch.py','core-sentinel-probe.py',
         'apport-positive-preflight.py','apport-metadata-preflight.py']


def run(args, data=None, timeout=75):
    p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if data:
        p.stdin.write(data)
    p.stdin.close()
    out=bytearray(); deadline=time.monotonic()+timeout
    try:
        while True:
            if time.monotonic()>deadline:
                raise RuntimeError('host command timeout; retain failure and inspect owned unit')
            if select.select([p.stdout],[],[],.05)[0]:
                chunk=p.stdout.read1(8192)
                if not chunk:
                    break
                out.extend(chunk)
                if len(out)>1048576:
                    raise RuntimeError('host 1 MiB output cap')
        return p.wait(timeout=1),out.decode()
    finally:
        if p.poll() is None:
            p.kill()
        p.wait();p.stdout.close()


def main():
    out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
    hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in FILES}
    record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                host_runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                sources=hashes, guest_directory=GUEST, mode='activation-only SIGQUIT',commands=[])
    def save():
        (out/'host-runner.json').write_text(json.dumps(record,indent=2)+'\n')
    def invoke(args, data=None):
        free=shutil.disk_usage(out).free
        if free<20*1024**3:
            raise RuntimeError('20 GiB host floor')
        code,text=run(args,data)
        record['commands'].append(dict(argv=args,returncode=code,host_free_before=free,host_free_after=shutil.disk_usage(out).free))
        save()
        if code:
            (out/'failed-command.txt').write_text(text)
            raise RuntimeError('guest operation failed; see failed-command.txt')
        return text
    try:
        # Refuse reuse/overwrite. Guest files are public source, never credentials.
        invoke(PREFIX+['mkdir','-m','755',GUEST])
        for name in FILES:
            invoke(PREFIX+['tee',GUEST+'/'+name],(HERE/name).read_bytes())
        actual=invoke(PREFIX+['sha256sum',*[GUEST+'/'+name for name in FILES]])
        (out/'guest-source-hashes.txt').write_text(actual)
        assert {Path(line.split()[1]).name:line.split()[0] for line in actual.splitlines()}==hashes
        for name,script,args in [('identity','apport-positive-preflight.py',[]),('metadata','apport-metadata-preflight.py',[]) ,('positive','apport-activation-pair.py',['positive']),('negative','apport-activation-pair.py',['negative'])]:
            text=invoke(PREFIX+['/usr/bin/python3','-B',GUEST+'/'+script,*args])
            (out/(name+'.json')).write_text(text)
            value=json.loads(text)
            if name=='identity':
                assert all(v['package_md5_matches'] for v in value['files'].values())
                assert value['guest_free_bytes']>=2*1024**3
                record['installed_kernel_note_bound']='UNVERIFIED: installed /usr/src contains headers only; no full Ubuntu ptrace.c source. No source downloads authorized. SIGABRT not run.'
            if name=='metadata':
                record['metadata_preflight_pass']=value['preflight_pass']
                # Metadata is not used by SIGQUIT's early return; retain its failure.
            if name in ('positive','negative') and not value.get('activation_only_pass'):
                raise RuntimeError(name+' activation arm failed; no next arm')
        record['matched_activation_pair_pass']=True
    except Exception as exc:
        record.update(error_type=type(exc).__name__,error=str(exc),matched_activation_pair_pass=False)
    finally:
        record['host_free_final']=shutil.disk_usage(out).free
        record['explicit_receipt_bytes']=sum(p.stat().st_size for p in out.iterdir() if p.is_file())
        save()
    return 0 if record.get('matched_activation_pair_pass') else 1


if __name__=='__main__':
    sys.exit(main())
