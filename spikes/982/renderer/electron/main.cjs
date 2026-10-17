/* #982 disposable Electron fallback host; unchanged pinned renderer, no product bridge. */
'use strict';
const {app,BrowserWindow,protocol,session,ipcMain,nativeTheme}=require('electron');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const os=require('node:os');
const args=process.argv.slice(2);
const options=new Set(args.filter(a=>a.startsWith('--')));
const positionals=args.filter(a=>!a.startsWith('--'));
if(positionals.length!==3) throw Error('Usage: electron main.cjs [--preflight|--motion-proof|--lifecycle-proof] EXPORT FROZEN OUTPUT');
const [exportPath,freezePath,outputPath]=positionals.map(p=>path.resolve(p));
const base=path.resolve(__dirname,'..');
const preflight=options.has('--preflight');
const diagnostic=options.has('--motion-proof')||options.has('--lifecycle-proof');
const timeoutSeconds=diagnostic?180:115;
const digest=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const freeze=preflight?{}:JSON.parse(fs.readFileSync(freezePath));
if(!preflight&&!diagnostic&&(freeze.purpose!=='timing-candidate-with-motion-evidence'||!freeze.motion_proof_sha256)) throw Error('Successful corrected untimed motion proof must precede timing');
if(fs.existsSync(outputPath)) throw Error('Preserve existing capture');
if(process.platform!=='linux'||process.arch!=='arm64'||process.versions.electron!=='44.8.0') throw Error('Pinned Linux arm64 Electron runtime required');
if(process.env.LIBGL_ALWAYS_SOFTWARE!=='1') throw Error('Mesa software rendering required');
if(options.has('--no-sandbox')||process.argv.includes('--no-sandbox')) throw Error('Sandbox downgrade forbidden');
const renderingEnv=Object.fromEntries(['LIBGL_ALWAYS_SOFTWARE','GDK_BACKEND','MESA_LOADER_DRIVER_OVERRIDE','GALLIUM_DRIVER','EGL_PLATFORM'].map(key=>[key,process.env[key]??null]));
const hashes=Object.fromEntries(['measure.js','fixture.json','desktop-producer-manifest.json','summarize.py','electron/main.cjs','electron/preload.cjs','electron/run-five.py','electron/freeze.py','electron/source.json','motion_evidence.py'].map(file=>[file,digest(path.join(base,file))]));
hashes.executable=digest(process.execPath);
if(hashes.executable!==JSON.parse(fs.readFileSync(path.join(__dirname,'source.json'))).executable_sha256) throw Error('Official pinned runtime executable differs');
if(!preflight&&JSON.stringify(freeze.runtime)!==JSON.stringify(process.versions)) throw Error('Actual runtime differs from successful frozen preflight');
if(!preflight&&(JSON.stringify(freeze.input_hashes)!==JSON.stringify(hashes)||JSON.stringify(freeze.rendering_env)!==JSON.stringify(renderingEnv))) throw Error('Electron frozen inputs/environment changed');
const manifest=JSON.parse(fs.readFileSync(path.join(exportPath,'manifest.json')));
if(digest(path.join(exportPath,'manifest.json'))!==hashes['desktop-producer-manifest.json']) throw Error('Producer manifest differs');
const assets=new Map();
for(const item of manifest.files){
 const full=path.resolve(exportPath,item.path);
 if(!full.startsWith(exportPath+path.sep)||fs.lstatSync(full).isSymbolicLink()||digest(full)!==item.sha256) throw Error('Artifact byte mismatch');
 assets.set('/'+item.path,fs.readFileSync(full));
}
const islandURI='campus-spike://renderer/Island/island.html';
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'campus-982-electron-'));
app.setPath('userData',temporary);
app.setPath('crashDumps',path.join(temporary,'crashes'));
app.commandLine.appendSwitch('use-gl','angle');
app.commandLine.appendSwitch('use-angle','gl');
app.commandLine.appendSwitch('force-device-scale-factor','1');
app.commandLine.appendSwitch('disable-background-networking');
app.commandLine.appendSwitch('disable-component-update');
app.commandLine.appendSwitch('disable-sync');
app.commandLine.appendSwitch('disable-domain-reliability');
protocol.registerSchemesAsPrivileged([{scheme:'campus-spike',privileges:{standard:true,secure:true,supportFetchAPI:true,corsEnabled:true}}]);
let win;
let completed=false;
let GPU;
let lastPhase='initialization';
let overallTimer;
const gpuQueryTimeoutMs=10000;
function phase(name){
 lastPhase=name;
 // Synchronous bounded records survive an outer kill after a stalled await.
 try{fs.writeSync(2,JSON.stringify({kind:'phase',utc:new Date().toISOString(),phase:name})+'\n');}catch{}
}
async function runPhase(name,operation){
 if(completed)throw Error('Capture already terminated');
 phase(name);
 const result=await operation();
 if(completed)throw Error('Capture already terminated');
 phase(name+'-complete');
 return result;
}
async function nativeGPU(){
 return runPhase('native-gpu',()=>new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(Error('Native GPU query exceeded 10 seconds')),gpuQueryTimeoutMs);
  Promise.resolve().then(()=>app.getGPUInfo('complete')).then(
   value=>{clearTimeout(timer);resolve(value);},
   error=>{clearTimeout(timer);reject(error);});
 }));
}
const resources=[];
const blocked=[];
function processGraphics(){
 const pending=[process.pid],found=[];
 while(pending.length){
  const pid=pending.pop();if(found.some(item=>item.pid===pid))continue;
  const proc='/proc/'+pid,record={pid};
  try{
   record.comm=fs.readFileSync(proc+'/comm','utf8').trim();
   const tasks=fs.readdirSync(proc+'/task');
   const children=new Set(tasks.flatMap(t=>fs.readFileSync(proc+'/task/'+t+'/children','utf8').trim().split(/\s+/).filter(Boolean).map(Number)));
   pending.push(...children);record.children=[...children];
   record.software_threads=tasks.map(t=>fs.readFileSync(proc+'/task/'+t+'/comm','utf8').trim()).filter(t=>t.startsWith('llvmpipe'));
  }catch(error){record.error=String(error);}
  found.push(record);
 }
 return found;
}
function finish(payload){
 if(completed)return;completed=true;
 clearTimeout(overallTimer);
 const terminalPhase=lastPhase;
 phase('receipt');
 let status=1;
 try{
  payload.freeze=freeze;payload.input_hashes=hashes;payload.rendering_env=renderingEnv;
  // Never await GPU enrichment on any terminal path. Unknown stays unknown.
  payload.runtime=process.versions;payload.native_gpu=GPU??null;
  payload.gpu_feature_status=app.getGPUFeatureStatus();payload.process_graphics=processGraphics();
  payload.resources=resources;payload.blocked_requests=blocked;
  if(!JSON.stringify(payload.native_gpu).match(/llvmpipe/i)||!payload.process_graphics.some(p=>p.pid!==process.pid&&p.software_threads?.length)){
   payload.kind='preflight_failure';payload.errors??=[];payload.errors.push('Actual candidate native llvmpipe evidence absent');
  }
  const validKind=['preflight','motion_proof','measurement','lifecycle_proof'].includes(payload.kind);
  const validChecks=payload.kind!=='lifecycle_proof'||payload.checks&&Object.keys(payload.checks).length>0&&Object.values(payload.checks).every(Boolean);
  status=validKind&&validChecks&&!payload.errors?.length&&!payload.invalid?.length?0:1;
 }catch(error){
  payload.kind='preflight_failure';payload.errors??=[];payload.errors.push(String(error));
 }
 if(status!==0)payload.diagnostics={last_phase:terminalPhase,utc:new Date().toISOString()};
 try{
  phase(status===0?'receipt-write':'failure-write');
  fs.mkdirSync(path.dirname(outputPath),{recursive:true});fs.writeFileSync(outputPath,JSON.stringify(payload,null,2)+'\n');
 }catch(error){
  status=1;
  phase('receipt-write-failed');
 }finally{
  try{fs.rmSync(temporary,{recursive:true,force:true});}catch{}
  app.exit(status);
 }
}
app.on('will-quit',()=>{try{fs.rmSync(temporary,{recursive:true,force:true});}catch{}});
// Covers readiness and every later asynchronous startup stage, not only load.
overallTimer=setTimeout(()=>finish({kind:'timeout',errors:[`No complete capture in ${timeoutSeconds} seconds`]}),timeoutSeconds*1000);
runPhase('readiness',()=>app.whenReady()).then(async()=>{
 nativeTheme.themeSource='light';
 const ses=session.fromPartition('campus-982-disposable');
 ses.setPermissionRequestHandler((_web,_permission,callback)=>callback(false));
 ses.setPermissionCheckHandler(()=>false);
 await runPhase('proxy',()=>ses.setProxy({proxyRules:'http=127.0.0.1:9;https=127.0.0.1:9',proxyBypassRules:'<-loopback>'}));
 ses.webRequest.onBeforeRequest((details,callback)=>{
  const requested=new URL(details.url);
  const allow=requested.protocol==='campus-spike:'&&requested.hostname==='renderer';
  if(!allow)blocked.push(details.url);callback({cancel:!allow});
 });
 ses.protocol.handle('campus-spike',request=>{
  const url=new URL(request.url),body=assets.get(url.pathname);
  if(url.host!=='renderer'||url.search||url.hash||!body)return new Response('Blocked',{status:403});
  resources.push(url.pathname);
  const type=url.pathname.endsWith('.html')?'text/html':url.pathname.endsWith('.js')?'text/javascript':url.pathname.endsWith('.css')?'text/css':'application/octet-stream';
  return new Response(body,{headers:{'Content-Type':type,'Cache-Control':'no-store'}});
 });
 win=new BrowserWindow({width:1440,height:900,useContentSize:true,show:true,title:'Campus #982 disposable Electron renderer',webPreferences:{session:ses,preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,backgroundThrottling:true}});
 win.removeMenu();win.setContentSize(1440,900);win.webContents.setZoomFactor(1);
 const senderOK=event=>event.sender===win.webContents&&event.senderFrame===win.webContents.mainFrame&&event.senderFrame.url===islandURI;
 ipcMain.handle('spike-presentation',(event,value)=>{
  if(!senderOK(event)||JSON.stringify(value)!=='{"kind":"presentation"}')throw Error('Unexpected fixture request');
  return {reachable:true,status:200,body:fs.readFileSync(path.join(base,'fixture.json'),'utf8')};
 });
 ipcMain.on('spike-receipt',(event,value)=>{
  if(!senderOK(event))return;
  const payload=JSON.parse(value);
  if(payload.kind==='motion_checkpoint'){console.log(JSON.stringify(payload));return;}
  void finish(payload);
 });
 win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
 win.webContents.on('will-navigate',(event,url)=>{if(url!==islandURI)event.preventDefault();});
 win.webContents.on('render-process-gone',(_event,details)=>void finish({kind:'renderer_crash',errors:[details.reason]}));
 win.on('close',()=>void finish({kind:'window_closed',errors:['Window closed before capture']}));
 // Initialize an empty target before awaiting renderer-dependent CDP commands.
 // Producer instrumentation is still registered before its first navigation.
 await runPhase('bootstrap-load',()=>win.loadURL('about:blank'));
 if(win.webContents.getURL()!=='about:blank')throw Error('Unexpected bootstrap document');
 phase('debugger-attach');
 win.webContents.debugger.attach('1.3');
 await runPhase('debugger-enable',()=>win.webContents.debugger.sendCommand('Page.enable'));
 const instrument='const SPIKE_DIAGNOSTICS='+JSON.stringify(diagnostic)+';const SPIKE_NATIVE_LLVMPIPE_PROVEN=false;const SPIKE_EXPECTED_RENDERER='+JSON.stringify(freeze.webgl_api_renderer??null)+';\n'+fs.readFileSync(path.join(base,'measure.js'),'utf8')+(options.has('--lifecycle-proof')?'\n'+fs.readFileSync(path.join(base,'lifecycle.js'),'utf8'):'');
 await runPhase('debugger-instrument',()=>win.webContents.debugger.sendCommand('Page.addScriptToEvaluateOnNewDocument',{source:instrument}));
 win.webContents.once('did-finish-load',()=>setTimeout(async()=>{
  if(completed)return;
  try{
   GPU=await nativeGPU();
   if(!JSON.stringify(GPU).match(/llvmpipe/i)||!processGraphics().some(p=>p.pid!==process.pid&&p.software_threads?.length)){
    await finish({kind:'preflight_failure',errors:['Native Mesa llvmpipe not proven before warmup']});return;
   }
   const expression=preflight?'window.spikePreflight()':options.has('--lifecycle-proof')?'window.spikeLifecycleProof()':options.has('--motion-proof')?'void window.spikeStart(true)':'void window.spikeStart()';
   await runPhase('renderer-invocation',()=>win.webContents.executeJavaScript(expression));
  }catch(error){await finish({kind:'preflight_failure',errors:[String(error)]});}
 },5000));
 await runPhase('load-url',()=>win.loadURL(islandURI));win.show();win.focus();win.webContents.focus();
}).catch(error=>void finish({kind:'preflight_failure',errors:[String(error)]}));
