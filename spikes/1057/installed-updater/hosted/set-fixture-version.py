import json
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
config.write_text(json.dumps(value, indent=2) + '\n')
(crate / 'resources/inert-helper.txt').write_text(f'Fixture 1057 inert identity\nversion={version}\nbehavior={behavior}\n')
