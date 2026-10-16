import pathlib,hashlib,json,subprocess
base=pathlib.Path('/home/campusqa/spike982/g8-timing-1268');files=[]
for p in sorted(base.rglob('*')):
 s=p.lstat();files.append({'path':str(p.relative_to(base)),'mode':oct(s.st_mode&0o7777),'bytes':s.st_size,'allocated':s.st_blocks*512,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None})
print(json.dumps({'files':files,'services':subprocess.run(['systemctl','show','polkit','gdm3','-p','Id','-p','ActiveState','-p','SubState','-p','UnitFileState'],capture_output=True,text=True).stdout,'bus':subprocess.run(['busctl','--system','status','org.freedesktop.PolicyKit1'],capture_output=True,text=True).stdout},indent=2))
