import pathlib,json,os,stat,hashlib
paths=[]
for base in ['/root/campus1057-10908-office391','/home/campusqa/campus1057-10908-office391']:
 p=pathlib.Path(base);assert p.is_dir();paths+=[p]+list(p.rglob('*'))
rows=[]
for p in sorted(paths):
 s=p.lstat();r=dict(path=str(p),uid=s.st_uid,gid=s.st_gid,mode=oct(s.st_mode&0o7777),device=s.st_dev,inode=s.st_ino,nlink=s.st_nlink)
 if stat.S_ISREG(s.st_mode):r.update(bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 elif p.is_symlink():r['link']=os.readlink(p)
 elif p.is_dir():r['entries']=sorted(x.name for x in p.iterdir())
 rows.append(r)
print(json.dumps(rows,indent=2))
