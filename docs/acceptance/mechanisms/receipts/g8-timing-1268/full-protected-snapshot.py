import pathlib,json,hashlib,os,datetime
paths=['/etc/gdm3/custom.conf','/usr/bin/campus-updater-1057','/usr/lib/campus-updater-1057/inert-helper.txt','/usr/lib/campus-updater-1057/install-deb.py','/usr/lib/campus-updater-1057/verify-signature','/etc/campus-updater-1057/admission.json','/etc/campus-updater-1057/public-key.txt','/usr/share/polkit-1/actions/dev.projectcampus.updater1057.policy','/run/systemd/system/polkit.service','/etc/systemd/system/polkit.service','/etc/polkit-1/rules.d/00-campus-updater-1057-deny.rules','/etc/polkit-1/rules.d/49-campus-updater-1057-headless.rules']
for d in ['/etc/polkit-1/rules.d','/usr/share/polkit-1/rules.d']:
 paths += [str(p) for p in pathlib.Path(d).iterdir() if p.is_file()]
paths += ['/etc/polkit-1/rules.d','/usr/share/polkit-1/rules.d','/etc/campus-updater-1057','/usr/lib/campus-updater-1057','/usr/share/polkit-1/actions']
paths += ['/etc/campus-updater-1057/admission.json', '/etc/campus-updater-1057/public-key.txt', '/etc/gdm3/custom.conf', '/etc/polkit-1/rules.d', '/etc/polkit-1/rules.d/00-campus-updater-1057-deny.rules', '/etc/systemd/system/polkit.service', '/home/campusqa/campus1057-10643-5176b9d7/probe/desktop.py', '/root/campus1057-10643-5176b9d7', '/root/campus1057-10643-5176b9d7/authority-window.py', '/root/campus1057-10643-5176b9d7/bootstrap', '/root/campus1057-1263-ea7d6086', '/root/campus1057-1263-ea7d6086/authority-window.py', '/run/systemd/system/polkit.service', '/usr/bin/campus-updater-1057', '/usr/bin/logger', '/usr/lib/campus-updater-1057/inert-helper.txt', '/usr/lib/campus-updater-1057/install-deb.py', '/usr/lib/campus-updater-1057/verify-signature', '/usr/share/polkit-1/actions/dev.projectcampus.updater1057.policy', '/usr/share/polkit-1/rules.d', '/usr/share/polkit-1/rules.d/49-ubuntu-admin.rules', '/usr/share/polkit-1/rules.d/50-default.rules', '/usr/share/polkit-1/rules.d/gnome-control-center.rules', '/usr/share/polkit-1/rules.d/org.freedesktop.GeoClue2.rules', '/usr/share/polkit-1/rules.d/org.freedesktop.bolt.rules', '/usr/share/polkit-1/rules.d/org.freedesktop.fwupd.rules', '/usr/share/polkit-1/rules.d/org.freedesktop.packagekit.rules', '/usr/share/polkit-1/rules.d/systemd-networkd.rules']
rows=[]
for name in sorted(set(paths)):
 p=pathlib.Path(name);r={'path':name,'exists':os.path.lexists(p)}
 if r['exists']:
  s=p.lstat();r.update(uid=s.st_uid,gid=s.st_gid,inode=s.st_ino,device=s.st_dev,mode=oct(s.st_mode&0o7777),link=os.readlink(p) if p.is_symlink() else None)
  if p.is_file() and not p.is_symlink():r.update(bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 if p.is_dir():r['entries']=sorted(x.name for x in p.iterdir())
 rows.append(r)
def alloc(p):
 return sum((pathlib.Path(root)/f).lstat().st_blocks*512 for root,dirs,files in os.walk(p) for f in files)
b=pathlib.Path('/home/campusqa/spike982');owned={str(p):alloc(p) for p in b.iterdir() if p.is_dir() and any(x in p.name for x in ['1200','1203','10470','1196','1213','1240','1268'])};logs=alloc('/var/log');consumed=sum(owned.values())+max(0,logs-114270208)+16777216
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_files':rows,'owned':owned,'var_log_allocated':logs,'historical_log_baseline':114270208,'overhead_reserve':16777216,'consumed_bytes':consumed,'remaining_bytes':256*1024**2-consumed,'guest_free_bytes':os.statvfs(b).f_bavail*os.statvfs(b).f_frsize},indent=2))
