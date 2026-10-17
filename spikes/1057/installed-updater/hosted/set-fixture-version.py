import json
import os
import hashlib
from pathlib import Path
import re
import sys

version, behavior = sys.argv[1:]
assert version in ('1.0.0', '2.0.0', '3.0.0')
crate = Path('src-tauri')
manifest = crate / 'Cargo.toml'
manifest.write_text(re.sub(r'(?m)^version = "[123]\.0\.0"$', f'version = "{version}"', manifest.read_text(), count=1))
# Only the local fixture's package version changes; resolved dependencies stay locked.
lock = crate / 'Cargo.lock'
lock.write_text(re.sub(r'(\[\[package\]\]\nname = "campus-updater-1057"\nversion = )"[123]\.0\.0"', r'\g<1>"' + version + '"', lock.read_text(), count=1))
config = crate / 'tauri.conf.json'
value = json.loads(config.read_text())
value['version'] = version
value['plugins']['updater']['pubkey'] = os.environ['SPIKE_UPDATER_PUBLIC_KEY']
config.write_text(json.dumps(value, indent=2) + '\n')
(crate / 'resources/inert-helper.txt').write_text(f'Fixture 1057 inert identity\nversion={version}\nbehavior={behavior}\n')
receipt = {'version': version, 'behavior': behavior, 'source_head': os.environ['EXACT_HEAD'],
           'command': 'cargo tauri build --ci --bundles deb,appimage -- --locked',
           'inputs': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (manifest, lock, config, crate / 'resources/inert-helper.txt')}}
Path(f'/output/receipts/build-inputs-{version}.json').write_text(json.dumps(receipt, indent=2)+'\n')
