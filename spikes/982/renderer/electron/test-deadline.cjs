'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const test=require('node:test');
const candidate=fs.readFileSync(path.join(__dirname,'main.cjs'),'utf8');
const flush=async()=>{for(let i=0;i<50;i++)await Promise.resolve();};
async function harness(source,{point,mode='pending',native=true,threads=native,receiptKind='preflight',writeFailure=false,stderrFailure=false}={}){
 let now=0,next=0,window,releasePending;
 const timers=new Map(),writes=[],exits=[],logs=[],calls=[],listeners={},ipc={};
 const versions={electron:'44.8.0',node:'mock'};
 const event={sender:null,senderFrame:{url:'campus-spike://renderer/Island/island.html'}};
 const operation=(name)=>{
  calls.push(name);
  if(point===name)return mode==='pending'?new Promise(resolve=>{releasePending=resolve;}):Promise.reject(Error('injected '+name));
  return Promise.resolve(name==='gpu'?{renderer:native?'llvmpipe (LLVM 20.1.2)':'other'}:undefined);
 };
 const setTimeout=(fn,ms)=>{const id=++next;timers.set(id,{fn,at:now+ms});return id;};
 const clearTimeout=id=>timers.delete(id);
 const mockFs={
  readFileSync(p){
   if(p.endsWith('source.json'))return '{"executable_sha256":"H"}';
   if(p.endsWith('manifest.json'))return '{"files":[]}';
   if(p==='/proc/10/comm')return 'electron';
   if(p==='/proc/11/comm')return 'electron';
   if(p==='/proc/10/task/10/children')return '11';
   if(p==='/proc/11/task/11/children')return '';
   if(p==='/proc/10/task/10/comm')return 'electron';
   if(p==='/proc/11/task/11/comm')return threads?'llvmpipe-0':'electron';
   return 'mock bytes';
  },
  readdirSync(p){return [p.includes('/10/')?'10':'11'];},
  existsSync(){return false;},lstatSync(){return {isSymbolicLink:()=>false};},
  mkdtempSync(){return '/tmp/mock';},mkdirSync(){},rmSync(){},
  writeFileSync(p,bytes){if(writeFailure)throw Error('disk failure');writes.push({path:p,payload:JSON.parse(bytes)});},
  writeSync(fd,bytes){if(stderrFailure)throw Error('stderr unavailable');assert.equal(fd,2);logs.push(JSON.parse(bytes));}
 };
 const webContents={
  mainFrame:event.senderFrame,
  setZoomFactor(){},setWindowOpenHandler(){},on(){},focus(){},
  once(name,fn){listeners[name]=fn;},
  debugger:{attach(){calls.push('attach');},sendCommand(name){return operation(name);}},
  executeJavaScript(){
   calls.push('renderer');
   ipc['spike-receipt'](event,JSON.stringify({kind:receiptKind,checks:{one:true},errors:[]}));
   return Promise.resolve();
  }
 };
 event.sender=webContents;
 const electron={
  app:{setPath(){},commandLine:{appendSwitch(){}},on(){},whenReady(){return operation('readiness');},
   getGPUInfo(){return operation('gpu');},getGPUFeatureStatus(){return {gpu:'mock'};},exit(code){exits.push(code);}},
  BrowserWindow:class{constructor(options){calls.push('window');assert.equal(options.webPreferences.sandbox,true);assert.equal(options.width,1440);assert.equal(options.height,900);this.webContents=webContents;window=this;}removeMenu(){}setContentSize(){}on(){}show(){}focus(){}
   async loadURL(){await operation('load');listeners['did-finish-load']();}},
  protocol:{registerSchemesAsPrivileged(){}},
  session:{fromPartition(){return {setPermissionRequestHandler(){},setPermissionCheckHandler(){},setProxy(){return operation('proxy');},webRequest:{onBeforeRequest(){}},protocol:{handle(){}}};}},
  ipcMain:{handle(){},on(name,fn){ipc[name]=fn;}},nativeTheme:{}
 };
 const context={require(name){if(name==='electron')return electron;if(name==='node:fs')return mockFs;if(name==='node:crypto')return {createHash(){return {update(){return this;},digest(){return 'H';}};}};return require(name);},
  process:{argv:['electron','main','--preflight','/export','ignored','/output.json'],platform:'linux',arch:'arm64',versions,env:{LIBGL_ALWAYS_SOFTWARE:'1'},execPath:'/electron',pid:10},
  __dirname:'/repo/electron',setTimeout,clearTimeout,console:{log(){}},URL,Response,Buffer,
  Date:class extends Date{constructor(...args){super(...(args.length?args:[now]));}static now(){return now;}}
 };
 vm.runInNewContext(source,context);await flush();
 async function advance(ms){
  const end=now+ms;
  for(;;){const due=[...timers].filter(([,t])=>t.at<=end).sort((a,b)=>a[1].at-b[1].at);if(!due.length)break;const[id,t]=due[0];timers.delete(id);now=t.at;t.fn();await flush();}
  now=end;await flush();
 }
 return {writes,exits,logs,calls,timers,advance,releasePending(){releasePending?.();},get now(){return now;},triggerReceipt(){ipc['spike-receipt'](event,JSON.stringify({kind:'preflight',errors:[]}));}};
}
for(const point of ['readiness','proxy','Page.enable','Page.addScriptToEvaluateOnNewDocument','load','gpu']){
 for(const mode of ['pending','reject'])test(`${point} ${mode}: bounded single failure`,async()=>{
  const h=await harness(candidate,{point,mode});await h.advance(115000);
  assert.equal(h.writes.length,1);assert.deepEqual(h.exits,[1]);
  const p=h.writes[0].payload;assert.equal(p.native_gpu,null);assert.ok(p.errors.length);assert.ok(p.diagnostics.last_phase);
  assert.ok(h.logs.every(x=>x.utc&&x.kind==='phase'));assert.ok(h.logs.some(x=>x.phase==='failure-write'));
  assert.ok(h.calls.filter(x=>x==='gpu').length<=1);
  await h.advance(200000);assert.equal(h.writes.length,1);assert.deepEqual(h.exits,[1]);
 });
}
test('GPU timeout occurs at 15 seconds, independent of global deadline',async()=>{
 const h=await harness(candidate,{point:'gpu'});await h.advance(14999);assert.equal(h.writes.length,0);await h.advance(1);assert.equal(h.writes.length,1);assert.match(h.writes[0].payload.errors.join(),/10 seconds/);assert.equal(h.writes[0].payload.diagnostics.last_phase,'native-gpu');
});
test('successful preflight retains its complete receipt schema and values',async()=>{
 const h=await harness(candidate);await h.advance(5000);
 assert.deepEqual(h.exits,[0]);assert.equal(h.writes.length,1);
 const expected={kind:'preflight',checks:{one:true},errors:[],freeze:{},
  input_hashes:Object.fromEntries(['measure.js','fixture.json','desktop-producer-manifest.json','summarize.py','electron/main.cjs','electron/preload.cjs','electron/run-five.py','electron/freeze.py','electron/source.json','motion_evidence.py','executable'].map(n=>[n,'H'])),
  rendering_env:{LIBGL_ALWAYS_SOFTWARE:'1',GDK_BACKEND:null,MESA_LOADER_DRIVER_OVERRIDE:null,GALLIUM_DRIVER:null,EGL_PLATFORM:null},
  runtime:{electron:'44.8.0',node:'mock'},native_gpu:{renderer:'llvmpipe (LLVM 20.1.2)'},gpu_feature_status:{gpu:'mock'},
  process_graphics:[{pid:10,comm:'electron',children:[11],software_threads:[]},{pid:11,comm:'electron',children:[],software_threads:['llvmpipe-0']}],resources:[],blocked_requests:[]};
 assert.deepEqual(h.writes,[{path:'/output.json',payload:expected}]);
 h.triggerReceipt();await h.advance(200000);assert.equal(h.writes.length,1);assert.deepEqual(h.exits,[0]);
});
test('missing native evidence still fails with actual native result',async()=>{
 const h=await harness(candidate,{native:false});await h.advance(5000);const p=h.writes[0].payload;
 assert.deepEqual(h.exits,[1]);assert.equal(p.native_gpu.renderer,'other');assert.equal(p.kind,'preflight_failure');assert.deepEqual(p.errors,['Native Mesa llvmpipe not proven before warmup','Actual candidate native llvmpipe evidence absent']);
});
test('receipt write error still exits nonzero once',async()=>{
 const h=await harness(candidate,{point:'readiness',writeFailure:true});await h.advance(115000);assert.equal(h.writes.length,0);assert.deepEqual(h.exits,[1]);assert.ok(h.logs.some(x=>x.phase==='receipt-write-failed'));
});
test('unavailable diagnostic stderr cannot suppress terminal receipt',async()=>{
 const h=await harness(candidate,{point:'readiness',stderrFailure:true});await h.advance(115000);assert.equal(h.writes.length,1);assert.deepEqual(h.exits,[1]);
});
test('late readiness cannot resume startup after deadline',async()=>{
 const h=await harness(candidate,{point:'readiness'});await h.advance(115000);h.releasePending();await flush();assert.deepEqual(h.calls,['readiness']);assert.equal(h.writes.length,1);assert.deepEqual(h.exits,[1]);
});
test('llvmpipe text without own descendant threads remains rejected',async()=>{
 const h=await harness(candidate,{threads:false});await h.advance(5000);assert.deepEqual(h.exits,[1]);assert.match(h.writes[0].payload.errors.join(),/llvmpipe/);assert.equal(h.writes[0].payload.native_gpu.renderer,'llvmpipe (LLVM 20.1.2)');
});
