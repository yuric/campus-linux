import subprocess,sys,time,pathlib,json,datetime
root=pathlib.Path.cwd();command=sys.argv[1]
assert command.startswith(('env WEBKIT_DISABLE_DMABUF_RENDERER=1 python3 /home/campusqa/spike982/g8-timing-1268/', 'python3 /home/campusqa/spike982/g8-timing-1268/','gnome-session-quit --logout --no-prompt'))
subprocess.run(['python3',str(root/'spikes/982/environment/qmp-console.py'),'key','alt+f2'],check=True,stdout=subprocess.DEVNULL)
time.sleep(.6)
subprocess.run(['python3','/tmp/campus982-1268/qmp-type-env.py',command],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['python3',str(root/'spikes/982/environment/qmp-console.py'),'key','ret'],check=True,stdout=subprocess.DEVNULL)
with open('/tmp/campus982-1268/gui-launches.jsonl','a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':command,'actual_qmp_run_dialog':True})+'\n')
print('Launched through actual GNOME Run dialog:',command)
