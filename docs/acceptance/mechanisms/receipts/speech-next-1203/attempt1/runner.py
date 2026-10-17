#!/usr/bin/env python3
"""Bounded synthetic observations, not a product speech implementation."""
import array, ctypes as C, ctypes.util, hashlib, io, json, locale, os
from pathlib import Path
import resource, secrets, signal, subprocess, threading, time, wave
ROOT=Path(__file__).resolve().parent
BINARY=ROOT.parent/'speech-offline2/build/bin/whisper-cli'
MODEL=ROOT/'ggml-tiny.bin'
ENV={k:v for k,v in os.environ.items() if k in ('LANG','LC_ALL','LC_MESSAGES','LC_CTYPE')}
ENV.update(PATH='/usr/bin:/bin',HOME='/home/campusqa',XDG_RUNTIME_DIR='/run/user/1000',PULSE_SERVER='unix:/run/user/1000/pulse/native')
R={'events':[],'inferences':[],'fixtures':{},'scope':'public synthetic offline mechanism only; prefix-batch, not native streaming','runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
children=[]; module=None; cg=None

def event(kind,**kw):
    row={'event':kind,'monotonic':time.monotonic(),**kw};R['events'].append(row);return row

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(argv):
    p=subprocess.run(argv,env=ENV,capture_output=True,text=True,timeout=10)
    R.setdefault('commands',[]).append({'argv':argv,'returncode':p.returncode,'stdout':p.stdout[:32768],'stderr':p.stderr[:4096]})
    if p.returncode:raise RuntimeError('command failed: '+str(argv))
    return p.stdout

def wav(pcm):
    b=io.BytesIO()
    with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(pcm)
    return b.getvalue()

def synth(language,text):
    lib=C.CDLL(C.util.find_library('espeak-ng'))
    lib.espeak_Initialize.argtypes=[C.c_int,C.c_int,C.c_char_p,C.c_int];lib.espeak_Initialize.restype=C.c_int
    rate=lib.espeak_Initialize(1,0,None,0);assert rate>0
    chunks=[];cbtype=C.CFUNCTYPE(C.c_int,C.POINTER(C.c_short),C.c_int,C.c_void_p)
    @cbtype
    def cb(p,n,e):
        if p and n:chunks.append(C.string_at(p,n*2))
        return 0
    lib.espeak_SetSynthCallback.argtypes=[cbtype];lib.espeak_SetSynthCallback(cb)
    lib.espeak_SetVoiceByName.argtypes=[C.c_char_p];voice='en-us' if language=='en' else 'es'
    assert lib.espeak_SetVoiceByName(voice.encode())==0
    lib.espeak_Synth.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_int,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
    data=text.encode();buf=C.create_string_buffer(data)
    assert lib.espeak_Synth(buf,len(data)+1,0,1,0,1,None,None)==0
    lib.espeak_Synchronize();lib.espeak_Terminate()
    pcm=array.array('h');pcm.frombytes(b''.join(chunks));out=array.array('h')
    for i in range(int(len(pcm)*16000/rate)):
        pos=i*rate/16000;j=int(pos);f=pos-j
        out.append(round(pcm[j]*(1-f)+pcm[min(j+1,len(pcm)-1)]*f))
    data=out.tobytes();path=ROOT/(language+'.wav');path.write_bytes(wav(data))
    R['fixtures'][language]={'reference':text,'license':'CC0-1.0','voice':voice,'source_rate':rate,'source_samples':len(pcm),'samples':len(out),'resampling':'linear interpolation to mono PCM16 LE 16000Hz','wav_sha256':sha(path)}
    return data

def launch_infer(pcm,language,label,group=None):
    assert not any(x['child'].poll() is None for x in jobs)
    argv=[str(BINARY),'-m',str(MODEL),'-f','-','-t','2','-ng','-l',language,'-nt']
    files=[(ROOT/(label+s)).open('wb') for s in ('.stdout','.stderr')]
    before=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic()
    p=subprocess.Popen(argv,env=ENV,stdin=subprocess.PIPE,stdout=files[0],stderr=files[1],close_fds=True,
        start_new_session=group is None,preexec_fn=None if group is None else lambda:os.setpgid(0,group))
    children.append(p)
    def feed():
        try:p.communicate(wav(pcm),timeout=25)
        except (BrokenPipeError,ValueError):pass
        except subprocess.TimeoutExpired:p.kill();p.wait()
    th=threading.Thread(target=feed);th.start()
    row={'label':label,'argv':argv,'pid':p.pid,'start':t,'samples':[0,len(pcm)//2],'language_selection':'explicit forced-language observation','translation':False,'max_rss_sampled_kib':0}
    job={'child':p,'thread':th,'files':files,'row':row,'cpu_before':before,'done':False};jobs.append(job)
    event('inference_start',label=label,pid=p.pid,samples=row['samples']);return job

def sample(job):
    p=job['child'];row=job['row']
    try:
        for line in Path('/proc/%d/status'%p.pid).read_text().splitlines():
            if line.startswith(('VmRSS:','VmHWM:')):row['max_rss_sampled_kib']=max(row['max_rss_sampled_kib'],int(line.split()[1]))
    except FileNotFoundError:pass
    for f in job['files']:
        if os.fstat(f.fileno()).st_size>65536:raise RuntimeError('inference output exceeded 64KiB stream bound')
    if p.poll() is not None and not job['done']:
        job['thread'].join(timeout=3)
        if job['thread'].is_alive():raise RuntimeError('stdin feeder did not exit')
        for f in job['files']:f.close()
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        row.update(returncode=p.returncode,wall_seconds=time.monotonic()-row['start'],cpu_seconds=after.ru_utime+after.ru_stime-job['cpu_before'].ru_utime-job['cpu_before'].ru_stime,
            stdout=(ROOT/(row['label']+'.stdout')).read_text(errors='replace'),stderr_sha256=sha(ROOT/(row['label']+'.stderr')))
        R['inferences'].append(row);job['done']=True
        event('inference_collected',label=row['label'],returncode=p.returncode)
    return job['done']

def wait_job(job):
    while not sample(job):time.sleep(.01)
    if job['row']['returncode']!=0:raise RuntimeError('inference nonzero: '+job['row']['label'])

def stop_group(rec,play,job,reason):
    running={str(p.pid):p.poll() is None for p in [rec,play]+([job['child']] if job else [])}
    t=time.monotonic();event(reason,workers_running=running)
    if rec.poll() is None:os.killpg(rec.pid,signal.SIGTERM)
    for p in [rec,play]+([job['child']] if job else []):
        try:p.wait(timeout=2)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    event(reason+'_reaped',elapsed=time.monotonic()-t,returncodes={str(p.pid):p.returncode for p in [rec,play]+([job['child']] if job else [])})
    return running

def capture(pcm,cancel=False):
    label='cancel' if cancel else 'prefix';raw=bytearray();started=time.monotonic()
    err=(ROOT/(label+'-recorder.stderr')).open('wb')
    rec=subprocess.Popen(['/usr/bin/python3',str(ROOT/'recorder.py'),'/run/user/1000/pulse/native',sink+'.monitor'],env=ENV,stdout=subprocess.PIPE,stderr=err,stdin=subprocess.DEVNULL,preexec_fn=os.setpgrp)
    children.append(rec);os.set_blocking(rec.stdout.fileno(),False)
    # Wait for actual exact-device ready acknowledgment before playback.
    while 'CONNECTED_SYNTHETIC_SOURCE='+sink+'.monitor' not in (ROOT/(label+'-recorder.stderr')).read_text():
        if rec.poll() is not None or time.monotonic()-started>3:raise RuntimeError('synthetic recorder not ready')
        time.sleep(.01)
    play=subprocess.Popen(['paplay','--device='+sink,'--raw','--rate=16000','--channels=1','--format=s16le'],env=ENV,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,preexec_fn=lambda:os.setpgid(0,rec.pid))
    children.append(play)
    playback=(pcm*(int(20*32000/len(pcm))+1))[:20*32000]
    def feed_playback():
        try:play.communicate(playback,timeout=30)
        except BrokenPipeError:pass
        except subprocess.TimeoutExpired:play.kill();play.wait()
    th=threading.Thread(target=feed_playback);th.start();event('capture_started',label=label,recorder_pid=rec.pid,playback_pid=play.pid)
    active=None;checkpoint=0
    try:
        while time.monotonic()-started<27:
            try:
                chunk=os.read(rec.stdout.fileno(),16384)
                if chunk:raw.extend(chunk)
            except BlockingIOError:pass
            if len(raw)>30*32000:raise RuntimeError('capture buffer cap exceeded')
            if active and not active['done']:
                if cancel and time.monotonic()-active['row']['start']>.1:
                    running=stop_group(rec,play,active,'cancel_requested')
                    while not sample(active):time.sleep(.01)
                    R['cancellation']={'all_three_actually_running':all(running.values()),'ignored_output_bytes':len(active['row'].pop('stdout').encode()),'observed_returncode':active['child'].returncode}
                    # Preserve raw public stdout, but never deliver it as a hypothesis.
                    event('cancel_output_discarded');break
                sample(active)
                if active['done']:
                    if active['row']['returncode']:raise RuntimeError('prefix inference failed')
                    event('provisional_collected',capture_active=rec.poll() is None,label=active['row']['label'])
            points=(48000,96000)
            if checkpoint<2 and len(raw)//2>=points[checkpoint] and (active is None or active['done']):
                n=points[checkpoint];active=launch_infer(bytes(raw[:n*2]),'en',label+str(checkpoint+1),rec.pid);checkpoint+=1
            if not cancel and checkpoint==2 and active['done']:
                stop_group(rec,play,None,'Stop');event('input_sealed',samples=len(raw)//2)
                R['capture']={'samples':len(raw)//2,'pcm_sha256':hashlib.sha256(raw).hexdigest(),'nonzero':any(raw),'prefix_count':checkpoint,'language':'forced en; independent of current locale'}
                wait_job(launch_infer(bytes(raw),'en','final'));break
            if rec.poll() is not None:raise RuntimeError('recorder exited before requested Stop')
            time.sleep(.005)
        else:raise RuntimeError('capture deadline exceeded')
    finally:
        if rec.poll() is None:os.killpg(rec.pid,signal.SIGTERM)
        for p in (rec,play):
            try:p.wait(timeout=2)
            except subprocess.TimeoutExpired:p.kill();p.wait()
        th.join(timeout=3);err.close();rec.stdout.close()

jobs=[]
try:
    assert os.uname().nodename=='lima-campus-linux-d5-noble-arm64' and os.getuid()==1000
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
    cg=Path('/sys/fs/cgroup'+Path('/proc/self/cgroup').read_text().strip().split(':')[-1])
    R['cgroup']=str(cg);R['memory_max']=(cg/'memory.max').read_text().strip();R['swap_max']=(cg/'memory.swap.max').read_text().strip()
    assert R['memory_max']=='536870912' and R['swap_max']=='0'
    R['interfaces']=[x.split(':')[0].strip() for x in Path('/proc/net/dev').read_text().splitlines() if ':' in x];assert R['interfaces']==['lo']
    R['net_namespace']=os.readlink('/proc/self/ns/net')
    assert sha(BINARY)=='50712621452d3ab5f0d7b2a2c5dbaad5100c8d9b86538da1e1a192074b3ec2a2'
    assert MODEL.stat().st_size==77691713 and sha(MODEL)=='be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21'
    R['binary_sha256']=sha(BINARY);R['model_sha256']=sha(MODEL);R['recorder_sha256']=sha(ROOT/'recorder.py')
    R['graphical_locale_observation']=json.loads((ROOT/'session.json').read_text())
    R['locale_mapping']={'input':'effective LC_MESSAGES in graphical session observer','effective':R['graphical_locale_observation'].get('effective',{}).get('LC_MESSAGES')}
    current=R['locale_mapping']['effective'];lang=current.split('_')[0].split('.')[0].lower() if current else None
    R['locale_mapping']['language']=None if lang in (None,'c','posix') else lang
    R['locale_mapping']['observed_language_tested']=lang in ('en','es')
    R['process_local_locale_tests']=[]
    for value in ('en_US.UTF-8','es_ES.UTF-8'):
        try:locale.setlocale(locale.LC_ALL,value);row={'input':value,'initialized':True,'LC_MESSAGES':locale.setlocale(locale.LC_MESSAGES),'LC_CTYPE':locale.setlocale(locale.LC_CTYPE)}
        except locale.Error as e:row={'input':value,'initialized':False,'error':str(e)}
        R['process_local_locale_tests'].append(row)
    R['packages']=command(['dpkg-query','-W','-f=${binary:Package} ${Version} ${Architecture}\n','libespeak-ng1','espeak-ng-data','libpulse0','pulseaudio-utils'])
    R['synthesizer_files']={str(p):sha(p) for p in [Path('/usr/lib/aarch64-linux-gnu/libespeak-ng.so.1').resolve(),Path('/var/lib/dpkg/info/espeak-ng-data:arm64.md5sums')]}
    en=synth('en','The blue notebook is beside the window. Please keep these words as a draft.')
    es=synth('es','El cuaderno azul está junto a la ventana. Guarda estas palabras como borrador.')
    wait_job(launch_infer(en,'en','observation-en'));wait_job(launch_infer(es,'es','observation-es'))
    sink='campus982_synthetic_'+secrets.token_hex(4)
    module=command(['pactl','load-module','module-null-sink','sink_name='+sink,'sink_properties=device.description=Campus982SyntheticOnly']).strip();assert module.isdigit()
    sources=json.loads(command(['pactl','--format=json','list','sources']))
    source=next(x for x in sources if x['name']==sink+'.monitor');R['source_identity']=source
    assert source['driver']=='module-null-sink.c' and str(source['owner_module'])==module
    capture(en);capture(en,True);R['completed']=True
except Exception as e:
    R['completed']=False;R['failure']={'type':type(e).__name__,'message':str(e)};event('failure',**R['failure'])
finally:
    for p in children:
        if p.poll() is None:p.terminate()
        try:p.wait(timeout=2)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    R['owned_workers_remaining']=[p.pid for p in children if p.poll() is None]
    if module is not None:
        try:
            command(['pactl','unload-module',module]);remaining=json.loads(command(['pactl','--format=json','list','sources']))
            R['source_absent_after_cleanup']=not any(x['name']==sink+'.monitor' for x in remaining)
        except Exception as e:R['cleanup_failure']=repr(e)
    if cg:
        R['tree_memory_peak_bytes']=int((cg/'memory.peak').read_text());R['memory_events']=(cg/'memory.events').read_text();R['memory_swap_peak']=(cg/'memory.swap.peak').read_text()
    R['output_allocated_bytes']=sum(p.stat().st_blocks*512 for p in ROOT.iterdir() if p.is_file() and p.name!='ggml-tiny.bin')
    event('cleanup_complete');(ROOT/'receipt.json').write_text(json.dumps(R,indent=2,ensure_ascii=False)+'\n')
raise SystemExit(0 if R.get('completed') and not R['owned_workers_remaining'] and R.get('source_absent_after_cleanup') else 1)
