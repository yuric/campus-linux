import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

version = sys.argv[1]
output = Path('/output/packages')
bundle = Path('src-tauri/target/release/bundle')
for extension in ('deb', 'AppImage'):
    matches = [p for p in bundle.rglob('*.' + extension) if version in p.name]
    assert len(matches) == 1, (extension, matches)
    package = matches[0]
    # Explicit trusted-version signing also covers deb on CLI variants that only
    # automatically emit an AppImage signature. It does not change package bytes.
    subprocess.run(['cargo', 'tauri', 'signer', 'sign', '--private-key-path', '/private/signing.key',
                    '--password', '', '--app-version', version, str(package)],
                   check=True, stdout=subprocess.DEVNULL)
    shutil.copy2(package, output / package.name)
    shutil.copy2(str(package) + '.sig', output / (package.name + '.sig'))
    print(json.dumps({'artifact': package.name, 'bytes': package.stat().st_size,
                      'sha256': hashlib.sha256(package.read_bytes()).hexdigest()}))
