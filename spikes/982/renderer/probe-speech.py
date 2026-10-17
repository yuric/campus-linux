#!/usr/bin/env python3
"""Report JS capability without requesting capture; deny any unexpected permission request."""
import json
import gi
gi.require_version('Gtk','3.0')
gi.require_version('WebKit2','4.1')
from gi.repository import Gtk, WebKit2, GLib
window=Gtk.Window()
view=WebKit2.WebView()
window.add(view)
receipt={'capture_granted':False,'audio_recorded':False,'network_recognition_attempted':False,'permissions':[]}
def permission(_view,request):
    receipt['permissions'].append(type(request).__name__)
    request.deny()
    return True
view.connect('permission-request',permission)
def done(web,result,*_):
    try: receipt['capability']=json.loads(web.evaluate_javascript_finish(result).to_string())
    except GLib.Error as error: receipt['error']=str(error)
    print(json.dumps(receipt,indent=2))
    Gtk.main_quit()
def loaded(web,event):
    if event==WebKit2.LoadEvent.FINISHED:
        web.evaluate_javascript("JSON.stringify({speechRecognition:typeof SpeechRecognition,webkitSpeechRecognition:typeof webkitSpeechRecognition,mediaDevices:!!navigator.mediaDevices,getUserMedia:typeof navigator.mediaDevices?.getUserMedia,isSecureContext})",-1,None,None,None,done,None)
view.connect('load-changed',loaded)
window.show_all()
view.load_html('<!doctype html><title>Disposable speech feature detection</title><p>No audio is captured.</p>','http://localhost/')
GLib.timeout_add_seconds(15,lambda:(print(json.dumps({'blocked':'capability timeout'})),Gtk.main_quit(),False)[2])
Gtk.main()
