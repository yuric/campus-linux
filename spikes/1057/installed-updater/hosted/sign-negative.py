"""Sign one integration negative while the disposable hosted key still exists.

Only metadata is retained: smoke reconstructs these public bytes from the real v2
AppImage. The mutated ELF is never executed or counted as an installed artifact.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

package, = Path('/output/packages').glob('*2.0.0*.AppImage')
original = package.read_bytes()
assert original[:4] == b'\x7fELF' and original[8:11] == b'AI\x02'
machine = int.from_bytes(original[18:20], 'little')
assert machine == {'amd64': 62, 'arm64': 183}[os.environ['FIXTURE_ARCH']]
replacement = (183 if machine == 62 else 62).to_bytes(2, 'little')
mutated = original[:18] + replacement + original[20:]
with tempfile.TemporaryDirectory(prefix='signed-negative-') as directory:
    candidate = Path(directory) / 'wrong-architecture.AppImage'
    candidate.write_bytes(mutated)
    env = dict(os.environ)
    env.pop('TAURI_SIGNING_PRIVATE_KEY', None)
    subprocess.run(['cargo', 'tauri', 'signer', 'sign', '--private-key-path', '/private/signing.key',
                    '--password', '', '--app-version', '2.0.0', str(candidate)],
                   env=env, check=True, stdout=subprocess.DEVNULL)
    receipt = {'version': '2.0.0', 'format': 'appimage', 'filename': package.name,
               'offset': 18, 'replacement_hex': replacement.hex(), 'bytes': len(mutated),
               'sha256': hashlib.sha256(mutated).hexdigest(),
               'signature': Path(str(candidate) + '.sig').read_text().strip()}
Path('/output/receipts/signed-negative.json').write_text(json.dumps(receipt, indent=2)+'\n')
