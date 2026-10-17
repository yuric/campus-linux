#!/usr/bin/env python3
"""Untimed built-in WebKit native GPU report, separate from the renderer benchmark."""
import json,os
import gi
gi.require_version('Gtk','3.0')
gi.require_version('WebKit2','4.1')
from gi.repository import Gtk,WebKit2,GLib
if os.environ.get('LIBGL_ALWAYS_SOFTWARE')!='1': raise SystemExit('Software-rendering environment required')
context=WebKit2.WebContext.new_ephemeral()
view=WebKit2.WebView(web_context=context)
view.get_settings().set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.ON_DEMAND)
window=Gtk.Window()
window.add(view)
window.set_default_size(1000,800)
finished=False
def capture(web,result,*_):
    global finished
    if finished: return
    finished=True
    try:
        print(json.dumps({'kind':'native_gpu_diagnostics','uri':web.get_uri(),'body':web.evaluate_javascript_finish(result).to_string(),'pid':os.getpid(),'LIBGL_ALWAYS_SOFTWARE':os.environ['LIBGL_ALWAYS_SOFTWARE']},indent=2))
    except GLib.Error as error: print(json.dumps({'kind':'native_gpu_failure','error':str(error)}))
    Gtk.main_quit()
def inspect():
    view.evaluate_javascript('document.body.innerText',-1,None,None,None,capture,None)
    return False
view.connect('load-changed',lambda _v,event:GLib.timeout_add_seconds(3,inspect) if event==WebKit2.LoadEvent.FINISHED else None)
window.show_all()
view.load_uri('webkit://gpu')
GLib.timeout_add_seconds(15,lambda:(print(json.dumps({'kind':'native_gpu_timeout'})),Gtk.main_quit(),False)[2])
Gtk.main()
