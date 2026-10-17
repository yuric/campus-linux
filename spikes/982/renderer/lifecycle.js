/* Untimed diagnostic only; never loaded during performance measurement. */
window.spikeLifecycleProof=async()=>{
  const report=value=>window.webkit.messageHandlers.spikeReceipt.postMessage(JSON.stringify(value));
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const records=[];
  const observe=async(label,visible,reducedMotion)=>{
    const visibilityReply=window.campusIsland.setVisible(visible);
    const motionReply=window.campusIsland.setReducedMotion(reducedMotion);
    await sleep(300);
    const before=window.spikeDrawState();
    await sleep(2500);
    const after=window.spikeDrawState();
    const state=window.campusIsland.lifecycleState();
    records.push({label,visibilityReply,motionReply,state,draw_delta:after.drawCalls-before.drawCalls,
      before_matrices:before.matrices,after_matrices:after.matrices});
    report({kind:'motion_checkpoint',label,state,draw_delta:after.drawCalls-before.drawCalls});
  };
  await observe('normal-visible',true,false);
  await observe('reduced-motion-visible',true,true);
  await observe('hidden-paused',false,true);
  await observe('visible-resumed',true,true);
  await observe('normal-restored',true,false);
  const checks={
    acknowledgements:records.every(record=>record.visibilityReply==='applied'&&record.motionReply==='applied'&&record.state.applied),
    hidden_draw_stopped:records[2].draw_delta===0,
    normal_draws:records[0].draw_delta>0,
    resumed_draws:records[3].draw_delta>0,
    reduced_motion_ack:records[1].state.reducedMotion===true,
    normal_restored:records[4].state.reducedMotion===false
  };
  report({kind:'lifecycle_proof',records,checks,errors:[],limitations:['No reload persistence or elapsed-animation replay proof','Draw-loop evidence is not complete animation/visual parity']});
};
