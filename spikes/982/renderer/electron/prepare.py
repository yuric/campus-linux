#!/usr/bin/env python3
"""Verify/extract the bounded official v44.8.0 arm64 spike; no product installation."""
import argparse,hashlib,json,os,stat,zipfile
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('archive',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
expected='502296281cab3c333bd5193e2eaed11c3bb28eabd7a451a49776a3e5a9468f8c'
if a.output.exists(): raise SystemExit('Use a new disposable output')
if a.archive.stat().st_size!=124393671 or hashlib.sha256(a.archive.read_bytes()).hexdigest()!=expected: raise SystemExit('Official archive differs')
with zipfile.ZipFile(a.archive) as archive:
 entries=archive.infolist()
 total=sum(item.file_size for item in entries)
 if total!=302048805 or total+a.archive.stat().st_size>500000000: raise SystemExit('Exceeded500MB bounded archive+extraction budget')
 for item in entries:
  relative=Path(item.filename)
  if relative.is_absolute() or '..' in relative.parts or stat.S_ISLNK(item.external_attr>>16): raise SystemExit('Unexpected archive path/type')
 a.output.mkdir(mode=0o700,parents=True)
 for item in entries:
  target=a.output/item.filename
  if item.is_dir():target.mkdir(parents=True,exist_ok=True);continue
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(archive.read(item))
  target.chmod((item.external_attr>>16)&0o777 or 0o644)
files={str(file.relative_to(a.output)):hashlib.sha256(file.read_bytes()).hexdigest() for file in a.output.rglob('*') if file.is_file()}
receipt=dict(version='44.8.0',architecture='linux-arm64',archive_bytes=a.archive.stat().st_size,
 extracted_bytes=total,archive_sha256=expected,files=files)
(a.output/'spike-extraction.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({key:value for key,value in receipt.items() if key!='files'}))
