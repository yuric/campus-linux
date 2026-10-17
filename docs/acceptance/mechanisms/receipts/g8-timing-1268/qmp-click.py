import json,socket,pathlib,sys,time
s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect(str(pathlib.Path.home()/'.lima/campus-linux-d5-noble-arm64/qmp.sock'));f=s.makefile('rwb',buffering=0);f.readline()
def call(n,a={}):
 f.write((json.dumps({'execute':n,'arguments':a})+'\n').encode())
 while True:
  r=json.loads(f.readline())
  if 'error' in r:raise RuntimeError(r['error'])
  if 'return' in r:return r['return']
call('qmp_capabilities');x,y,w,h=map(int,sys.argv[1:]);call('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':int(x*32767/w)}},{'type':'abs','data':{'axis':'y','value':int(y*32767/h)}}]});call('input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':'left'}}]});time.sleep(.1);call('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'left'}}]})
