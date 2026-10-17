'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const test=require('node:test');
const candidate=fs.readFileSync(path.join(__dirname,'main.cjs'),'utf8');
const flush=async()=>{for(let i=0;i<50;i++)await Promise.resolve();};
async function harness(source,{point,mode='pending',native=true,threads=native,receiptKind='preflight',writeFailure=false,stderrFailure=false,navigationDependent=false,bootstrapURL='about:blank',gpuDiagnostic=false,compatibility=false,softwareCompositor=false}={}){
 let now=0,next=0,window,releasePending,navigated=false,instrumented=false,currentURL='',blankCallback=false;
 const timers=new Map(),writes=[],exits=[],logs=[],calls=[],listeners={},ipc={};
 const guards={switches:[],appEvents:{}};
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
  mainFrame:event.senderFrame,getURL(){return currentURL;},
  setZoomFactor(){},setWindowOpenHandler(fn){guards.open=fn;},on(name,fn){guards[name]=fn;},focus(){},
  once(name,fn){listeners[name]=fn;},
  debugger:{attach(){calls.push('attach');},sendCommand(name,params){if(name==='Page.addScriptToEvaluateOnNewDocument')guards.instrument=params.source;if(navigationDependent&&!navigated){calls.push(name);return new Promise(()=>{});}return operation(name).then(value=>{if(name==='Page.addScriptToEvaluateOnNewDocument')instrumented=true;return value;});}},
  executeJavaScript(){
   calls.push('renderer');
   ipc['spike-receipt'](event,JSON.stringify({kind:receiptKind,checks:{one:true},errors:[]}));
   return Promise.resolve();
  }
 };
 event.sender=webContents;
 const electron={
  app:{setPath(){},commandLine:{appendSwitch(...args){guards.switches.push(args);}},on(name,fn){guards.appEvents[name]=fn;},whenReady(){return operation('readiness');},
   getGPUInfo(){return operation('gpu');},getGPUFeatureStatus(){return {gpu:'mock'};},exit(code){exits.push(code);}},
  BrowserWindow:class{constructor(options){guards.preferences=options.webPreferences;calls.push('window');assert.equal(options.webPreferences.sandbox,true);assert.equal(options.width,1440);assert.equal(options.height,900);this.webContents=webContents;window=this;}removeMenu(){}setContentSize(){}on(){}show(){}focus(){}
   async loadURL(url){const blank=url==='about:blank';await operation(blank?'bootstrap':'load');navigated=true;currentURL=blank?bootstrapURL:url;if(!blank)assert.equal(instrumented,true,'producer scripts require prior instrumentation');if(listeners['did-finish-load']){if(blank)blankCallback=true;listeners['did-finish-load']();}}},
  protocol:{registerSchemesAsPrivileged(){}},
  session:{fromPartition(){return {setPermissionRequestHandler(fn){guards.permissionRequest=fn;},setPermissionCheckHandler(fn){guards.permissionCheck=fn;},setProxy(){return operation('proxy');},webRequest:{onBeforeRequest(fn){guards.request=fn;}},protocol:{handle(){}}};}},
  ipcMain:{handle(name,fn){ipc[name]=fn;},on(name,fn){ipc[name]=fn;}},nativeTheme:{}
 };
 const context={require(name){if(name==='electron')return electron;if(name==='node:fs')return mockFs;if(name==='node:crypto')return {createHash(){return {update(){return this;},digest(){return 'H';}};}};return require(name);},
  process:{argv:['electron','main','--preflight',...(gpuDiagnostic?['--gpu-diagnostic']:[]),...(compatibility?['--ignore-gpu-blocklist']:[]),...(softwareCompositor?['--disable-gpu-compositing']:[]),'/export','ignored','/output.json'],platform:'linux',arch:'arm64',versions,env:{LIBGL_ALWAYS_SOFTWARE:'1'},execPath:'/electron',pid:10},
  __dirname:'/repo/electron',setTimeout,clearTimeout,console:{log(){}},URL,Response,Buffer,
  Date:class extends Date{constructor(...args){super(...(args.length?args:[now]));}static now(){return now;}}
 };
 vm.runInNewContext(source,context);await flush();
 async function advance(ms){
  const end=now+ms;
  for(;;){const due=[...timers].filter(([,t])=>t.at<=end).sort((a,b)=>a[1].at-b[1].at);if(!due.length)break;const[id,t]=due[0];timers.delete(id);now=t.at;t.fn();await flush();}
  now=end;await flush();
 }
 return {guards,ipc,event,writes,exits,logs,calls,timers,advance,releasePending(){releasePending?.();},get blankCallback(){return blankCallback;},get now(){return now;},triggerReceipt(){ipc['spike-receipt'](event,JSON.stringify({kind:'preflight',errors:[]}));}};
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

// Model the documented target-not-navigated CDP wait, not a generic injected failure.
test('prior ordering deadlocks while bootstrap orders instrumentation before producer',async()=>{
 const old=candidate.replace(/ \/\/ Initialize an empty target[^]*? phase\('debugger-attach'\);/," phase('debugger-attach');");
 assert.notEqual(old,candidate);
 const before=await harness(old,{navigationDependent:true});await before.advance(115000);
 assert.equal(before.writes[0].payload.diagnostics.last_phase,'debugger-enable');
 assert.equal(before.calls.includes('load'),false);assert.deepEqual(before.exits,[1]);
 const after=await harness(candidate,{navigationDependent:true});
 assert.deepEqual(after.calls,['readiness','proxy','window','bootstrap','attach','Page.enable','Page.addScriptToEvaluateOnNewDocument','load']);
 assert.equal(after.blankCallback,false);assert.equal(after.calls.includes('gpu'),false);assert.equal(after.calls.includes('renderer'),false);
 await after.advance(5000);assert.deepEqual(after.exits,[0]);assert.equal(after.calls.filter(x=>x==='load').length,1);assert.equal(after.calls.filter(x=>x==='renderer').length,1);
});
for(const mode of ['pending','reject'])test(`bootstrap ${mode} fails once without debugger or producer`,async()=>{
 const h=await harness(candidate,{point:'bootstrap',mode,navigationDependent:true});await h.advance(115000);
 assert.deepEqual(h.exits,[1]);assert.equal(h.writes.length,1);assert.equal(h.writes[0].payload.diagnostics.last_phase,'bootstrap-load');
 assert.equal(h.calls.includes('attach'),false);assert.equal(h.calls.includes('load'),false);assert.equal(h.calls.includes('gpu'),false);
 h.releasePending();await flush();await h.advance(200000);assert.deepEqual(h.exits,[1]);assert.equal(h.writes.length,1);assert.equal(h.calls.includes('attach'),false);
});
test('bootstrap URL mismatch rejects before debugger and producer',async()=>{
 const h=await harness(candidate,{bootstrapURL:'https://unexpected.invalid'});await h.advance(115000);
 assert.deepEqual(h.exits,[1]);assert.match(h.writes[0].payload.errors.join(),/Unexpected bootstrap/);assert.equal(h.calls.includes('attach'),false);assert.equal(h.calls.includes('load'),false);
});

test('bootstrap retains navigation, network, IPC, sandbox and instrumentation boundaries',async()=>{
 const h=await harness(candidate);
 assert.equal(h.guards.preferences.nodeIntegration,false);assert.equal(h.guards.preferences.contextIsolation,true);
 assert.equal(h.guards.preferences.sandbox,true);assert.equal(h.guards.preferences.webSecurity,true);assert.equal(h.guards.preferences.backgroundThrottling,true);
 assert.equal(h.guards.open().action,'deny');
 for(const url of ['https://example.invalid/','file:///tmp/example','data:text/html,test','about:blank']){
  let prevented=false;h.guards['will-navigate']({preventDefault(){prevented=true;}},url);assert.equal(prevented,true);
  let canceled;h.guards.request({url},r=>{canceled=r.cancel;});assert.equal(canceled,true);
 }
 const blank={sender:h.event.sender,senderFrame:{url:'about:blank'}};
 assert.throws(()=>h.ipc['spike-presentation'](blank,{kind:'presentation'}),/Unexpected fixture/);
 h.ipc['spike-receipt'](blank,JSON.stringify({kind:'preflight',errors:[]}));assert.equal(h.writes.length,0);
 assert.equal(h.guards.instrument,'const SPIKE_DIAGNOSTICS=false;const SPIKE_NATIVE_LLVMPIPE_PROVEN=false;const SPIKE_EXPECTED_RENDERER=null;\nmock bytes');
 assert.equal([...h.timers.values()].some(t=>t.at===115000),true);
});

 test('GPU diagnostic events are filtered, bounded and do not alter terminal evidence',async()=>{
 const h=await harness(candidate,{point:'readiness',gpuDiagnostic:true});
 const emit=d=>h.guards.appEvents['child-process-gone']({},d);
 emit({type:'Utility',reason:'crashed',exitCode:8,secret:'excluded'});
 for(const reason of ['crashed','launch-failed','oom','clean-exit'])emit({type:'GPU',reason,exitCode:9,secret:'excluded'});
 emit({type:'GPU',reason:'x'.repeat(100000),exitCode:NaN});
 for(let i=0;i<50;i++)emit({type:'GPU',reason:'crashed',exitCode:1});
 const events=h.logs.filter(x=>x.kind==='gpu-process');
 assert.equal(events.length,16);assert.equal(h.logs.filter(x=>x.kind==='gpu-process-overflow').length,1);
 assert.deepEqual(events.slice(0,4).map(x=>x.reason),['crashed','launch-failed','oom','clean-exit']);
 assert.equal(events[4].reason,'unknown');assert.equal(events[4].exitCode,null);
 for(const row of events){assert.deepEqual(Object.keys(row).sort(),['exitCode','kind','reason','type','utc']);assert.ok(JSON.stringify(row).length<200);}
 assert.ok(h.guards.switches.some(x=>x[0]==='enable-logging'&&x[1]==='stderr'));
 assert.ok(h.guards.switches.some(x=>x[0]==='log-level'&&x[1]==='2'));
 await h.advance(115000);assert.equal(h.writes.length,1);assert.equal(h.writes[0].payload.native_gpu,null);
 assert.equal(h.writes[0].payload.diagnostics.last_phase,'readiness');assert.deepEqual(h.exits,[1]);
 });
 test('GPU diagnostic stderr errors do not obstruct terminal failure',async()=>{
 const h=await harness(candidate,{point:'readiness',gpuDiagnostic:true,stderrFailure:true});
 h.guards.appEvents['child-process-gone']({},{type:'GPU',reason:'oom',exitCode:7});
 await h.advance(115000);assert.equal(h.writes.length,1);assert.deepEqual(h.exits,[1]);
 });
 test('ordinary preflight has no GPU logging switches or event hook',async()=>{
 const h=await harness(candidate);assert.equal(h.guards.appEvents['child-process-gone'],undefined);
 assert.ok(!h.guards.switches.some(x=>['enable-logging','log-level'].includes(x[0])));
 });

test('successful GPU diagnostic stays explicitly ineligible for freeze',async()=>{
 const h=await harness(candidate,{gpuDiagnostic:true});await h.advance(5000);
 assert.equal(h.writes[0].payload.kind,'preflight');
 assert.equal(h.writes[0].payload.diagnostic_only,'gpu-startup');
 assert.deepEqual(h.exits,[0]);
});

for(const [mode,flags] of [['timing',[]],['motion',['--motion-proof']]]){
 test(`GPU diagnostic rejects ${mode} before installing hooks or switches`,()=>{
  const effects=[];
  const electron={app:{on(){effects.push('hook');},commandLine:{appendSwitch(){effects.push('switch');}}}};
  const context={__dirname:'/repo/electron',require(name){return name==='electron'?electron:require(name);},
   process:{argv:['electron','main','--gpu-diagnostic',...flags,'/export','/freeze','/output']}};
  assert.throws(()=>vm.runInNewContext(candidate,context),/GPU diagnostics require preflight; never timing evidence/);
  assert.deepEqual(effects,[]);
 });
}


test('compatibility arm adds only the whole-list switch and discloses it',async()=>{
 const control=await harness(candidate,{gpuDiagnostic:true});
 const arm=await harness(candidate,{gpuDiagnostic:true,compatibility:true});
 assert.deepEqual(arm.guards.switches.filter(x=>x[0]!=='ignore-gpu-blocklist'),control.guards.switches);
 assert.deepEqual(arm.guards.switches.filter(x=>x[0]==='ignore-gpu-blocklist'),[['ignore-gpu-blocklist']]);
 await arm.advance(5000);const p=arm.writes[0].payload;
 assert.equal(p.diagnostic_only,'gpu-compatibility');
 assert.deepEqual(JSON.parse(JSON.stringify(p.gpu_compatibility)),{arm:'mesa-blocklist-override',switch:'ignore-gpu-blocklist',value:'',scope:'whole-gpu-feature-compatibility-list',timing_eligible:false});
 assert.deepEqual(arm.exits,[0]);
 assert.equal(control.guards.switches.some(x=>x[0]==='ignore-gpu-blocklist'),false);
 const ordinary=await harness(candidate);await ordinary.advance(5000);
 assert.equal(ordinary.writes[0].payload.gpu_compatibility,undefined);
 assert.equal(ordinary.guards.switches.some(x=>x[0]==='ignore-gpu-blocklist'),false);
});
for(const flags of [[],['--preflight'],['--motion-proof'],['--lifecycle-proof'],['--preflight','--gpu-diagnostic','--motion-proof'],['--preflight','--gpu-diagnostic','--lifecycle-proof']]){
 test('compatibility refuses non-diagnostic-preflight '+JSON.stringify(flags),()=>{
  const effects=[];const electron={app:{on(){effects.push('hook');},commandLine:{appendSwitch(){effects.push('switch');}}}};
  const context={__dirname:'/repo/electron',require(name){return name==='electron'?electron:require(name);},process:{argv:['electron','main','--ignore-gpu-blocklist',...flags,'/export','/freeze','/output']}};
  assert.throws(()=>vm.runInNewContext(candidate,context),/GPU compatibility override requires diagnostic preflight only/);
  assert.deepEqual(effects,[]);
 });
}
for(const settings of [{native:false},{threads:false},{point:'gpu',mode:'reject'},{point:'gpu',mode:'pending'},{point:'readiness',mode:'pending'}]){
 test('compatibility retains native/deadline failure '+JSON.stringify(settings),async()=>{
  const h=await harness(candidate,{gpuDiagnostic:true,compatibility:true,...settings});await h.advance(115000);
  assert.deepEqual(h.exits,[1]);assert.equal(h.writes.length,1);
  assert.equal(h.writes[0].payload.kind,'preflight_failure');assert.equal(h.writes[0].payload.diagnostic_only,'gpu-compatibility');
  assert.equal(h.writes[0].payload.gpu_compatibility.scope,'whole-gpu-feature-compatibility-list');
 });
}
test('compatibility retains sandbox, isolation, IPC and network boundaries',async()=>{
 const h=await harness(candidate,{gpuDiagnostic:true,compatibility:true});
 for(const [key,value] of Object.entries({sandbox:true,nodeIntegration:false,contextIsolation:true,webSecurity:true,backgroundThrottling:true}))assert.equal(h.guards.preferences[key],value);
 assert.equal(h.guards.open().action,'deny');
 for(const url of ['https://example.invalid/','file:///tmp/example','data:text/html,test','about:blank']){
  let prevented=false;h.guards['will-navigate']({preventDefault(){prevented=true;}},url);assert.equal(prevented,true);
  let canceled;h.guards.request({url},r=>{canceled=r.cancel;});assert.equal(canceled,true);
 }
 const blank={sender:h.event.sender,senderFrame:{url:'about:blank'}};
 assert.throws(()=>h.ipc['spike-presentation'](blank,{kind:'presentation'}),/Unexpected fixture/);
 h.ipc['spike-receipt'](blank,JSON.stringify({kind:'preflight',errors:[]}));assert.equal(h.writes.length,0);
 assert.ok(!h.guards.switches.some(x=>/swiftshader|sandbox|crash-limit|watchdog|disable-gpu|disable-hardware|disable-gpu-driver-bug-workarounds/.test(x[0])));
 assert.ok(h.guards.switches.some(x=>x[0]==='use-gl'&&x[1]==='angle'));
 assert.ok(h.guards.switches.some(x=>x[0]==='use-angle'&&x[1]==='gl'));
});

test('compatibility rejects alternate switch values rather than hiding their scope',()=>{
 for(const flag of ['--ignore-gpu-blocklist=3','--ignore-gpu-blocklist=']){
  const effects=[];const electron={app:{on(){effects.push('hook');},commandLine:{appendSwitch(){effects.push('switch');}}}};
  const context={__dirname:'/repo/electron',require(name){return name==='electron'?electron:require(name);},process:{argv:['electron','main','--preflight','--gpu-diagnostic',flag,'/export','/freeze','/output']}};
  assert.throws(()=>vm.runInNewContext(candidate,context),/exact valueless switch/);assert.deepEqual(effects,[]);
 }
});
test('compatibility permission requests and checks remain denied',async()=>{
 const h=await harness(candidate,{gpuDiagnostic:true,compatibility:true});
 let allowed;h.guards.permissionRequest(null,'media',value=>{allowed=value;});
 assert.equal(allowed,false);assert.equal(h.guards.permissionCheck(),false);
});

test('software compositor adds exactly one switch and marks diagnostic receipts',async()=>{
 const control=await harness(candidate,{gpuDiagnostic:true,compatibility:true});
 const arm=await harness(candidate,{gpuDiagnostic:true,compatibility:true,softwareCompositor:true});
 assert.deepEqual(arm.guards.switches.filter(x=>x[0]!=='disable-gpu-compositing'),control.guards.switches);
 assert.deepEqual(arm.guards.switches.filter(x=>x[0]==='disable-gpu-compositing'),[['disable-gpu-compositing']]);
 for(const key of ['sandbox','nodeIntegration','contextIsolation','webSecurity','backgroundThrottling','preload'])assert.equal(arm.guards.preferences[key],control.guards.preferences[key]);
 await arm.advance(5000);const p=arm.writes[0].payload;
 assert.deepEqual(arm.exits,[0]);assert.equal(p.diagnostic_only,'software-compositor');
 assert.deepEqual(JSON.parse(JSON.stringify(p.software_compositor)),{switch:'disable-gpu-compositing',value:'',timing_eligible:false});
 await control.advance(5000);assert.equal(control.writes[0].payload.software_compositor,undefined);
});
for(const flags of [[],['--preflight'],['--preflight','--gpu-diagnostic'],['--gpu-diagnostic'],['--preflight','--gpu-diagnostic','--ignore-gpu-blocklist','--motion-proof'],['--preflight','--gpu-diagnostic','--ignore-gpu-blocklist','--lifecycle-proof']]){
 test('software compositor rejects unsupported mode '+JSON.stringify(flags),()=>{
  const effects=[];const electron={app:{on(){effects.push('hook');},commandLine:{appendSwitch(){effects.push('switch');}}}};
  const context={__dirname:'/repo/electron',require(name){return name==='electron'?electron:require(name);},process:{argv:['electron','main','--disable-gpu-compositing',...flags,'/export','/freeze','/output']}};
  assert.throws(()=>vm.runInNewContext(candidate,context),/requires|require/);assert.deepEqual(effects,[]);
 });
}
for(const flag of ['--disable-gpu-compositing=','--disable-gpu-compositing=true'])test('software compositor rejects valued switch '+flag,()=>{
 const effects=[];const electron={app:{on(){effects.push('hook');},commandLine:{appendSwitch(){effects.push('switch');}}}};
 const context={__dirname:'/repo/electron',require(name){return name==='electron'?electron:require(name);},process:{argv:['electron','main','--preflight','--gpu-diagnostic','--ignore-gpu-blocklist',flag,'/export','/freeze','/output']}};
 assert.throws(()=>vm.runInNewContext(candidate,context),/exact valueless switch/);assert.deepEqual(effects,[]);
});
for(const settings of [{native:false},{threads:false},{point:'gpu',mode:'reject'},{point:'gpu',mode:'pending'},{point:'readiness',mode:'pending'}])test('software compositor retains failure gate '+JSON.stringify(settings),async()=>{
 const h=await harness(candidate,{gpuDiagnostic:true,compatibility:true,softwareCompositor:true,...settings});await h.advance(115000);
 assert.deepEqual(h.exits,[1]);assert.equal(h.writes.length,1);assert.equal(h.writes[0].payload.kind,'preflight_failure');
 assert.equal(h.writes[0].payload.software_compositor.timing_eligible,false);
});
