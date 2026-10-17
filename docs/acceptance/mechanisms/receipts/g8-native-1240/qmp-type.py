import json,socket,sys,time,pathlib
s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect(str(pathlib.Path.home()/'.lima/campus-linux-d5-noble-arm64/qmp.sock'));f=s.makefile('rwb',buffering=0);f.readline()
def cmd(name,args={}):
 f.write((json.dumps({'execute':name,'arguments':args})+'\n').encode())
 while True:
  r=json.loads(f.readline())
  if 'error' in r:raise RuntimeError('QMP failed')
  if 'return' in r:return
cmd('qmp_capabilities')
normal={' ':'spc','/':'slash','.':'dot','-':'minus',':':'semicolon','_':'minus'}
for c in sys.argv[1]:
 keys=(['shift'] if c.isupper() or c in ':_' else [])+[normal.get(c,c.lower())]
 cmd('send-key',{'keys':[{'type':'qcode','data':x} for x in keys],'hold-time':30});time.sleep(.045)
