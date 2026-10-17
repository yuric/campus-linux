"""Exact-version native evidence for WebKit's hardcoded WebGL API identity."""
import hashlib,json,re
from pathlib import Path
WEBKIT_SOURCE='4fb33923db2f945803df49546f75867980365c08'

def native_receipt(path):
    path=Path(path)
    raw=json.loads(path.read_text())
    if raw.get('kind')!='native_gpu_diagnostics' or raw.get('uri')!='webkit://gpu' or raw.get('LIBGL_ALWAYS_SOFTWARE')!='1':
        raise ValueError('Native WebKit GPU receipt missing software environment/provenance')
    lines=raw['body'].splitlines()
    version=lines[lines.index('WebKit version')+1]
    if version!='WebKitGTK 2.52.6 (tarball)': raise ValueError('Unreviewed WebKit version')
    start=next(i for i,line in enumerate(lines) if line.lower()=='hardware acceleration information (render process)')
    native=lines[start:]
    field=lambda key:native[native.index(key)+1]
    renderer=field('GL_RENDERER')
    if not re.fullmatch(r'llvmpipe \(LLVM [0-9.]+, [0-9]+ bits\)',renderer) or field('GL_VENDOR')!='Mesa':
        raise ValueError('Native render process does not prove Mesa llvmpipe')
    display=lines[lines.index('Display Information'):lines.index('View Information')]
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),renderer=renderer,vendor=field('GL_VENDOR'),
        gl_version=field('GL_VERSION'),webkit_runtime='2.52.6',display_type=display[display.index('Type')+1],
        webkit_source=WEBKIT_SOURCE,webgl_api_renderer='Apple GPU',webgl_api_vendor='Apple Inc.')

def candidate_software_processes(records):
    return [item['pid'] for item in records if item.get('comm','').startswith(('WebKitWebProces','WebKitGPUProces'))
            and any(name.startswith('llvmpipe') for name in item.get('software_threads',[]))]
