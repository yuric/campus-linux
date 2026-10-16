#!/usr/bin/env python3
"""Disposable WebKitGTK renderer probe, run inside the actual GDM user session.
Dependencies: python3-gi gir1.2-webkit2-4.1. No account/network authority.
"""
import argparse, hashlib, json, os, mimetypes
from urllib.parse import urlsplit
from native_evidence import native_receipt,candidate_software_processes
from pathlib import Path
import gi
gi.require_version('Gtk','3.0')
gi.require_version('WebKit2','4.1')
gi.require_version('Soup','3.0')
gi.require_version('JavaScriptCore','4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib, Gio, Soup, JavaScriptCore

parser=argparse.ArgumentParser()
parser.add_argument('--native-gpu-receipt',type=Path,required=True)
parser.add_argument('--preflight', action='store_true', help='Observe actual WebGL identity without timing; frozen positional is ignored')
parser.add_argument('--compositing-policy',choices=('on-demand','always'),default='on-demand')
parser.add_argument('export',type=Path)
parser.add_argument('frozen',type=Path)
parser.add_argument('output',type=Path)
a=parser.parse_args()
base=Path(__file__).resolve().parent
native=native_receipt(a.native_gpu_receipt)
runtime_version='.'.join(str(v) for v in (WebKit2.get_major_version(),WebKit2.get_minor_version(),WebKit2.get_micro_version()))
if runtime_version!=native['webkit_runtime']: raise SystemExit('Actual WebKit version differs from reviewed native/source receipt')
display_type='Wayland' if 'Wayland' in Gdk.Display.get_default().__gtype__.name else 'X11' if 'X11' in Gdk.Display.get_default().__gtype__.name else 'unknown'
if display_type!=native['display_type']: raise SystemExit('Native receipt and actual GTK backend differ')
frozen={} if a.preflight else json.loads(a.frozen.read_text())
rendering_env={key:os.environ.get(key) for key in ('LIBGL_ALWAYS_SOFTWARE','GDK_BACKEND','WEBKIT_DISABLE_COMPOSITING_MODE','WEBKIT_DISABLE_DMABUF_RENDERER','WEBKIT_SKIA_ENABLE_CPU_RENDERING','GSK_RENDERER','MESA_LOADER_DRIVER_OVERRIDE','GALLIUM_DRIVER','EGL_PLATFORM')}
if not a.preflight and frozen.get('rendering_env')!=rendering_env: raise SystemExit('Rendering environment differs from freeze')
required=('producer_sha','manifest_sha256','fixture_sha256','measure_sha256','runner_sha256','webkit','mesa','llvm','kernel','architecture','os','session','graphics','webgl_api_renderer','native_evidence','compositing_policy','frozen_at')
if not a.preflight and any(not frozen.get(k) for k in required): raise SystemExit('Incomplete premeasurement freeze')
if not a.preflight and frozen.get('native_evidence')!=native: raise SystemExit('Native GPU evidence differs from freeze')
if os.environ.get('LIBGL_ALWAYS_SOFTWARE')!='1': raise SystemExit('Software rendering required')
if a.output.exists(): raise SystemExit('Preserve existing raw capture; choose fresh output')
a.output.parent.mkdir(parents=True,exist_ok=True)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
for path,key in [(a.export/'manifest.json','manifest_sha256'),(base/'fixture.json','fixture_sha256'),(base/'measure.js','measure_sha256'),(base/'run-webkit.py','runner_sha256'),(base/'native_evidence.py','native_evidence_code_sha256')]:
    expected=digest(base/'producer-manifest.json') if a.preflight and key=='manifest_sha256' else digest(path) if a.preflight else frozen[key]
    if digest(path)!=expected: raise SystemExit('Frozen bytes changed: '+key)
manifest=json.loads((a.export/'manifest.json').read_text())
if manifest['source'] != json.loads((base/'producer-manifest.json').read_text())['source']: raise SystemExit('Producer pin mismatch')
for entry in manifest['files']:
    path=a.export/entry['path']
    if not path.is_file() or path.is_symlink() or digest(path)!=entry['sha256']:
        raise SystemExit('Producer artifact byte mismatch')
# The producer's independent verifier must also run before this host starts.
context=WebKit2.WebContext.new_ephemeral()
# An inert proxy prevents outbound HTTP transport even if the CSP regresses.
context.set_network_proxy_settings(WebKit2.NetworkProxyMode.CUSTOM,WebKit2.NetworkProxySettings.new('http://127.0.0.1:9',None))
assets={entry['path']:(a.export/entry['path']).read_bytes() for entry in manifest['files']}
resources=[]
def resource(request,*_):
    uri=urlsplit(request.get_uri())
    path=uri.path.lstrip('/')
    if uri.scheme!='campus-spike' or uri.netloc!='renderer' or uri.query or uri.fragment or path not in assets:
        request.finish_error(GLib.Error('Unlisted renderer resource'))
        return
    data=assets[path]
    resources.append(path)
    response=WebKit2.URISchemeResponse.new(Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data)),len(data))
    response.set_status(200,None)
    response.set_content_type(mimetypes.guess_type(path)[0] or 'application/octet-stream')
    headers=Soup.MessageHeaders.new(Soup.MessageHeadersType.RESPONSE)
    headers.append('Content-Type',mimetypes.guess_type(path)[0] or 'application/octet-stream')
    headers.append('Access-Control-Allow-Origin','*')
    headers.append('Cache-Control','no-store')
    response.set_http_headers(headers)
    request.finish_with_response(response)
context.register_uri_scheme('campus-spike',resource,None)
security=context.get_security_manager()
security.register_uri_scheme_as_secure('campus-spike')
security.register_uri_scheme_as_local('campus-spike')
security.register_uri_scheme_as_cors_enabled('campus-spike')
manager=WebKit2.UserContentManager()
manager.register_script_message_handler('spikeReceipt')
fixture_text=(base/'fixture.json').read_text()
def presentation(_manager,value,reply):
    try:
        if json.loads(value.to_json(0))!={'kind':'presentation'}:
            reply.return_error_message('Unexpected stub action')
        else:
            payload=json.dumps(dict(reachable=True,status=200,body=fixture_text))
            reply.return_value(JavaScriptCore.Value.new_from_json(value.get_context(),payload))
    except Exception as error:
        reply.return_error_message(str(error))
    return True
manager.connect('script-message-with-reply-received::campusIslandAPI',presentation)
if not manager.register_script_message_handler_with_reply('campusIslandAPI',None): raise SystemExit('Could not register rendering-only presentation stub')
script='const SPIKE_NATIVE_LLVMPIPE_PROVEN=true;const SPIKE_EXPECTED_RENDERER='+json.dumps(native['webgl_api_renderer'])+';\n'+(base/'measure.js').read_text()
manager.add_script(WebKit2.UserScript.new(script,WebKit2.UserContentInjectedFrames.TOP_FRAME,WebKit2.UserScriptInjectionTime.START,None,None))
view=WebKit2.WebView(web_context=context,user_content_manager=manager)
entry_uri='campus-spike://renderer/Island/island.html'
def policy(_view,decision,kind):
    if kind in (WebKit2.PolicyDecisionType.NAVIGATION_ACTION,WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION):
        if kind==WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION or decision.get_navigation_action().get_request().get_uri()!=entry_uri:
            decision.ignore()
            return True
    return False
view.connect('decide-policy',policy)
policy_value=WebKit2.HardwareAccelerationPolicy.ALWAYS if a.compositing_policy=='always' else WebKit2.HardwareAccelerationPolicy.ON_DEMAND
view.get_settings().set_hardware_acceleration_policy(policy_value)
if not a.preflight and frozen['compositing_policy']!=a.compositing_policy: raise SystemExit('Compositing policy differs from freeze')
window=Gtk.Window()
window.set_title('Campus #982 disposable renderer measurement')
window.set_default_size(1440,900)
window.add(view)
view.get_settings().set_enable_write_console_messages_to_stdout(True)
completed=False
def process_graphics():
    pending=[os.getpid()]
    found=[]
    while pending:
        pid=pending.pop()
        if any(item['pid']==pid for item in found): continue
        record={'pid':pid}
        proc=Path('/proc')/str(pid)
        try:
            record['comm']=(proc/'comm').read_text().strip()
            children=sorted(set(child for path in (proc/'task').glob('*/children') for child in path.read_text().split()),key=int)
            pending.extend(int(child) for child in children)
            record['children']=[int(child) for child in children]
            record['software_threads']=[thread.read_text().strip() for thread in (proc/'task').glob('*/comm') if thread.read_text().strip().startswith(('llvmpipe','softpipe'))]
            try:
                maps=(proc/'maps').read_text().splitlines()
                record['graphics_libraries']=sorted(set(line.split()[-1] for line in maps if any(key in line for key in ('/dri/','libEGL','libGL','libLLVM','libgallium'))))
            except OSError as error: record['maps_error']=str(error)
        except OSError as error: record['error']=str(error)
        found.append(record)
    return found
def finish(payload):
    global completed
    if completed: return
    completed=True
    payload['freeze']=frozen
    payload['resources']=resources
    payload['process_graphics']=process_graphics()
    payload['native_evidence']=native
    payload['native_software_process_ids']=candidate_software_processes(payload['process_graphics'])
    if not payload['native_software_process_ids']:
        payload['kind']='preflight_failure'
        payload.setdefault('errors',[]).append('No live candidate WebKit llvmpipe thread evidence')
    payload['rendering_env']=rendering_env
    payload['compositing_policy']=a.compositing_policy
    payload['webgl_enabled']=view.get_settings().get_enable_webgl()
    payload['hardware_acceleration_policy']=str(view.get_settings().get_hardware_acceleration_policy())
    payload['webkit_runtime']='.'.join(str(v) for v in (WebKit2.get_major_version(),WebKit2.get_minor_version(),WebKit2.get_micro_version()))
    a.output.write_text(json.dumps(payload,indent=2)+'\n')
    Gtk.main_quit()
def received(_manager,result):
    value=json.loads(result.get_js_value().to_string())
    finish(value)
manager.connect('script-message-received::spikeReceipt',received)
view.connect('web-process-terminated',lambda *_: finish(dict(kind='renderer_crash',errors=['WebKit process terminated'])))
def evaluated(web,result,*_):
    try: web.evaluate_javascript_finish(result)
    except GLib.Error as error: finish(dict(kind='preflight_failure',errors=[str(error)]))
def start():
    native_process_ok=bool(candidate_software_processes(process_graphics()))
    view.evaluate_javascript('window.spikePreflight()' if a.preflight or not native_process_ok else 'window.spikeStart()',-1,None,None,None,evaluated,None)
    return False
def loaded(web,event):
    if event==WebKit2.LoadEvent.FINISHED: GLib.timeout_add_seconds(5,start)
view.connect('load-changed',loaded)
# No microphone request is granted by this benchmark host.
view.connect('permission-request',lambda _v,request:(request.deny(),True)[1])
window.connect('destroy',lambda *_: finish(dict(kind='window_closed',errors=['Window closed before capture'])))
window.show_all()
window.present()
view.grab_focus()
view.load_uri(entry_uri)
GLib.timeout_add_seconds(115,lambda:(finish(dict(kind='timeout',errors=['No complete capture in 115 seconds'])),False)[1])
Gtk.main()
