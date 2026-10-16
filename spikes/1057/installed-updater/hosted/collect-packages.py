import hashlib
import json
from pathlib import Path
import shutil
import sys

version = sys.argv[1]
output = Path('/output/packages')
bundle = Path('src-tauri/target/release/bundle')
for extension in ('deb', 'AppImage'):
    matches = [p for p in bundle.rglob('*.' + extension) if version in p.name]
    assert len(matches) == 1, (extension, matches)
    package = matches[0]
    # Pinned CLI 2.12.3 signs both requested formats with the configured version.
    # Missing automatic signatures are a build failure, never a different signer.
    assert Path(str(package) + '.sig').is_file(), 'Pinned bundler signature missing'
    shutil.copy2(package, output / package.name)
    shutil.copy2(str(package) + '.sig', output / (package.name + '.sig'))
    print(json.dumps({'artifact': package.name, 'bytes': package.stat().st_size,
                      'sha256': hashlib.sha256(package.read_bytes()).hexdigest()}))
