/* Disposable #982 instrument; unchanged producer bytes load after this user script. */
(() => {
  'use strict';
  const traces = {inputs: [], gestures: [], frames: [], lifecycle: [], errors: [], invalid: [], checkpoints: []};
  const originalError=console.error.bind(console);
  console.error=(...args)=>{traces.errors.push(args.map(value=>value instanceof Error ? value.stack : String(value)).join(' '));originalError(...args);};
  const report = value => window.webkit.messageHandlers.spikeReceipt.postMessage(JSON.stringify(value));
  let seed = 98120261016 >>> 0;
  Math.random = () => {
    seed = (seed + 0x6D2B79F5) | 0;
    let n = Math.imul(seed ^ seed >>> 15, 1 | seed);
    n = (n + Math.imul(n ^ n >>> 7, 61 | n)) ^ n;
    return ((n ^ n >>> 14) >>> 0) / 4294967296;
  };
  // No campusHost mutation channel is installed. This is never functional parity.
  addEventListener('error', event => traces.errors.push(event.message || 'Resource error: '+(event.target?.src || event.target?.href || event.target?.tagName || 'unknown')),true);
  addEventListener('unhandledrejection', event => traces.errors.push(String(event.reason)));
  addEventListener('campus:island:lifecycle', event => traces.lifecycle.push(event.detail));
  let started = false;
  let gl;
  const contextAttempts=[];
  const drawState={drawCalls:0,matrices:new Map()};
  window.spikeDrawState=()=>({drawCalls:drawState.drawCalls,matrices:[...drawState.matrices.values()]});
  function instrument(context) {
    if(!SPIKE_DIAGNOSTICS||context.__spikeInstrumented) return;
    context.__spikeInstrumented=true;
    for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']) {
      const original=context[name].bind(context);
      context[name]=(...args)=>{drawState.drawCalls++;return original(...args);};
    }
    const names=new Map();
    const originalLocation=context.getUniformLocation.bind(context);
    context.getUniformLocation=(program,name)=>{
      const location=originalLocation(program,name);
      if(location&&['viewMatrix','projectionMatrix'].includes(name)) names.set(location,name);
      return location;
    };
    const originalMatrix=context.uniformMatrix4fv.bind(context);
    context.uniformMatrix4fv=(location,transpose,value,...rest)=>{
      if(names.has(location)) drawState.matrices.set(location,{name:names.get(location),values:Array.from(value).slice(0,16)});
      return originalMatrix(location,transpose,value,...rest);
    };
  }
  const originalContext = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function(kind, ...rest) {
    try {
      const context=originalContext.call(this,kind,...rest);
      if (kind === 'webgl2' || kind === 'webgl') {
        contextAttempts.push({kind,attributes:rest,created:!!context});
        if (context) {gl=context;instrument(context);}
      }
      return context;
    } catch(error) {
      contextAttempts.push({kind,error:String(error)});
      throw error;
    }
  };
  function invalid(reason) { if (started) traces.invalid.push({at: performance.now(), reason}); }
  addEventListener('blur', () => invalid('focus loss'));
  document.addEventListener('visibilitychange', () => invalid('visibility change: ' + document.visibilityState));
  const pose = seconds => {
    const t = Math.min(60, Math.max(0, seconds));
    if (t <= 10) return [40*t, 0, 1];
    if (t <= 20) return [400-80*(t-10), 0, 1];
    if (t <= 30) return [-400+40*(t-20), 30*(t-20), 1];
    if (t <= 40) return [0, 300, 1+.05*(t-30)];
    if (t <= 50) return [0, 300, 1.5-.075*(t-40)];
    return [0, 300-30*(t-50), .75+.025*(t-50)];
  };
  function liveFixture() {
    const canvas=document.querySelector('canvas');
    // The producer imperatively appends its canvas to a React-owned host div.
    let element=canvas;
    let fiber;
    for(let n=0;element&&n<20;n++,element=element.parentElement) {
      const key=Object.keys(element).find(key=>key.startsWith('__reactFiber$'));
      if(key) {fiber=element[key];break;}
    }
    for(let n=0;fiber&&n<100;n++,fiber=fiber.return) {
      const snapshot=fiber.memoizedProps?.snapshot;
      if(snapshot?.projects&&snapshot?.agents&&snapshot?.seashore) {
        const tasks=[...(snapshot.imaginarium||[]),...(snapshot.seashore||[]),...(snapshot.in_progress||[]),...(snapshot.alarms||[])];
        return {source:'mounted canvas React ancestor snapshot',projects:snapshot.projects.length,
          agents:snapshot.agents.length,tasks:tasks.length,unique_projects:new Set(snapshot.projects.map(x=>x.id)).size,
          unique_agents:new Set(snapshot.agents.map(x=>x.id)).size,unique_tasks:new Set(tasks.map(x=>x.id)).size};
      }
    }
    return null;
  }
  function identity() {
    const debug=gl?.getExtension('WEBGL_debug_renderer_info');
    const parameter = key => {try {return gl?.getParameter(key) ?? null;} catch(error) {return String(error);}};
    return {renderer:debug ? parameter(debug.UNMASKED_RENDERER_WEBGL) : null,
      unmasked_vendor:debug ? parameter(debug.UNMASKED_VENDOR_WEBGL) : null,
      masked_renderer:gl ? parameter(gl.RENDERER) : null,
      vendor:gl ? parameter(gl.VENDOR) : null,version:gl ? parameter(gl.VERSION) : null,
      debug_extension:!!debug,extensions:gl?.getSupportedExtensions() ?? null,
      context_lost:gl?.isContextLost() ?? null,context_attempts:contextAttempts,
      canvas_count:document.querySelectorAll('canvas').length,live_fixture:liveFixture(),
      synthetic_page_text:document.body?.innerText.slice(0,4000),
      resources:performance.getEntriesByType('resource').map(entry=>({name:entry.name,duration:entry.duration,transferSize:entry.transferSize})),
      scripts:[...document.scripts].map(script=>({src:script.src,type:script.type})),
      viewport:[innerWidth,innerHeight],scale:devicePixelRatio,
      visibility:document.visibilityState,focus:document.hasFocus(),
      island_state:window.campusIsland?.state() ?? null,
      lifecycle:window.campusIsland?.lifecycleState() ?? null};
  }
  function inspect() {
    const facts=identity();
    if (!facts.canvas_count || !gl) throw Error('Actual WebGL context missing');
    if (!/llvmpipe/i.test(facts.renderer || '') && !(SPIKE_NATIVE_LLVMPIPE_PROVEN && facts.renderer === 'Apple GPU' && facts.unmasked_vendor === 'Apple Inc.')) throw Error('Native software renderer evidence or reviewed masked API identity missing');
    if (!facts.live_fixture || facts.live_fixture.projects!==12 || facts.live_fixture.agents!==48 || facts.live_fixture.tasks!==180 || facts.live_fixture.unique_projects!==12 || facts.live_fixture.unique_agents!==48 || facts.live_fixture.unique_tasks!==180) throw Error('Mounted scene fixture counts do not match freeze');
    if (innerWidth !== 1440 || innerHeight !== 900 || devicePixelRatio !== 1) throw Error('Viewport/scale mismatch');
    if (document.visibilityState !== 'visible' || !document.hasFocus()) throw Error('Foreground required');
    if (!window.campusIsland?.state().live) throw Error('No mounted Island');
    if (window.campusIsland.setReducedMotion(false) !== 'applied') throw Error('Normal motion not applied');
    if (window.campusIsland.setVisible(true) !== 'applied') throw Error('Visibility not applied');
    if (SPIKE_EXPECTED_RENDERER && facts.renderer !== SPIKE_EXPECTED_RENDERER) throw Error('Actual WebGL renderer changed after freeze');
    return identity();
  }
  window.spikePreflight = () => {
    try {report({kind:'preflight',...inspect(),errors:traces.errors});}
    catch(error) {report({kind:'preflight_failure',...identity(),errors:[...traces.errors,String(error)]});}
  };
  window.spikeStart = (motionProof = false) => {
    let facts;
    try {facts=inspect();}
    catch(error) {report({kind:'preflight_failure',...identity(),errors:[...traces.errors,String(error)]});return;}
    const renderer=facts.renderer;
    const canvas=document.querySelector('canvas');
    // Only the synthetic ID bypasses capture: dispatchEvent has no OS pointer to capture.
    const pointerID = 982;
    const capture = canvas.setPointerCapture.bind(canvas);
    const release = canvas.releasePointerCapture.bind(canvas);
    canvas.setPointerCapture = id => { if (id !== pointerID) capture(id); };
    canvas.releasePointerCapture = id => { if (id !== pointerID) release(id); };
    const pointer = (type, x, y, down) => {
      traces.gestures.push({at:performance.now(),type,x,y});
      canvas.dispatchEvent(new PointerEvent(type, {
        pointerId: pointerID, pointerType: 'mouse', isPrimary: true, button: 0,
        buttons: down ? 1 : 0, clientX: 720+x, clientY: 450+y, bubbles: true
      }));
    };
    let previous = [0, 0, 1];
    let dragging=false;
    const endDrag = () => {
      if (dragging) pointer('pointercancel',previous[0],previous[1],false);
      dragging=false;
    };
    const apply = (seconds,phase) => {
      const current=pose(seconds);
      const panChanged=current[0]!==previous[0] || current[1]!==previous[1];
      const zoomChanged=current[2]!==previous[2];
      // Primary pan is one continuous gesture. OrbitControls accepts wheel only in
      // NONE state: cancel/reopen during simultaneous final pan+zoom, never click.
      if (zoomChanged) {
        endDrag();
        const deltaY = -Math.log(current[2]/previous[2]) / (-Math.log(.95)*.015);
        canvas.dispatchEvent(new WheelEvent('wheel', {deltaY, deltaMode: 0, clientX:720, clientY:450, bubbles:true, cancelable:true}));
      }
      if (panChanged) {
        if (!dragging) {pointer('pointerdown',previous[0],previous[1],true);dragging=true;}
        pointer('pointermove',current[0],current[1],true);
      } else if (dragging) endDrag();
      traces.inputs.push({at:performance.now(),phase,seconds,requested:current});
      previous=current;
    };
    const reset = () => {
      endDrag();
      // Public lifecycle clears pending control damping, then canonical overview.
      const hidden=window.campusIsland.setVisible(false);
      const visible=window.campusIsland.setVisible(true);
      const focus=window.campusIsland.focus(null,{instant:true});
      if(hidden!=='applied'||visible!=='applied'||focus!=='focused') throw Error('Camera reset was not acknowledged');
      previous=[0,0,1];
      return {at:performance.now(),hidden,visible,focus,state:window.campusIsland.state()};
    };
    const initialReset=reset();
    started=true;
    const start=performance.now();
    let measurementStart;
    let measurementReset;
    let lastFrame;
    let checkpoint=-1;
    const timer=setInterval(()=>{
      const now=performance.now();
      if(measurementStart===undefined) {
        if(now-start<30000) {apply((now-start)/500,'warmup');return;}
        apply(60,'warmup');
        measurementReset=reset();
        measurementStart=performance.now();
      }
      const seconds=(performance.now()-measurementStart)/1000;
      apply(seconds,'measurement');
      const index=Math.min(6,Math.floor(seconds/10));
      if(motionProof&&index>checkpoint) {
        checkpoint=index;
        const item={index,at:performance.now(),seconds,requested:pose(seconds),state:window.campusIsland.state(),draws:window.spikeDrawState()};
        traces.checkpoints.push(item);
        report({kind:'motion_checkpoint',...item});
      }
    },16);
    const frame=now=>{
      if(measurementStart!==undefined&&now>=measurementStart) {
        if(!motionProof) {
          if(!traces.frames.length&&lastFrame!==undefined) traces.frames.push(lastFrame);
          traces.frames.push(now);
        }
      }
      lastFrame=now;
      if(measurementStart!==undefined&&now-measurementStart>=60000) {
        apply(60,'measurement');
        endDrag();
        clearInterval(timer);
        report({kind:motionProof?'motion_proof':'measurement',renderer,
          viewport:[innerWidth,innerHeight],scale:devicePixelRatio,initialReset,measurementReset,
          warmup_ms:measurementStart-start,duration_ms:now-measurementStart,
          measurement_start_ms:measurementStart,measurement_end_ms:measurementStart+60000,...traces});
        return;
      }
      requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  };
})();
