const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const wasm=fs.readFileSync(path.resolve(__dirname,'../../game/assets/atlas.wasm'));
(async()=>{
  let g;
  const {instance}=await WebAssembly.instantiate(wasm,{env:{
    memset:(p,v,n)=>{new Uint8Array(g.memory.buffer,p,n).fill(v);return p;},
    sinf:Math.sin,atan2f:Math.atan2,acosf:Math.acos,lroundf:n=>Math.sign(n)*Math.round(Math.abs(n))
  }});
  g=instance.exports;g.initialize(123);g.config(3,0,1,0);g.reelVolume(2);
  let now=0,raw=4090;
  g.dialReset();g.dialSample(raw,now);
  function sample(step){
    now+=40;raw=(raw+step+4096)%4096;g.dialSample(raw,now);
    return g.rumbleEvent(now,1);
  }
  function hasAudio(){
    const address=g.samples();
    return new Int16Array(g.memory.buffer,address,512).some(n=>n!==0);
  }
  for(const direction of [1,-1]){
    let total=0;
    for(let i=0;i<96;i++){
      const step=Math.round((i+1)*4096/96)-Math.round(i*4096/96);
      const cue=sample(direction*step);
      assert.equal(hasAudio(),cue===9);
      if(cue===9)total++;
    }
    assert.equal(total,12);
  }
  for(let i=0;i<30;i++){g.advance(40,0,0,.02);assert.equal(sample(0),0);assert(!hasAudio());}
  for(let i=0;i<8;i++)sample(36);
  g.dialSample(-1,now+1);g.rumbleEvent(now+1,1);
  raw=200;g.dialSample(raw,now+2);assert.equal(sample(130),0);
  g.rumbleEvent(now,0);g.reelVolume(0);
  let mutedTicks=0;
  for(let i=0;i<12;i++){if(sample(130)===9)mutedTicks++;assert(!hasAudio());}
  assert(mutedTicks>0);
  // Browser virtual encoder starts at 0, rAF sound gate uses the page clock.
  g.initialize(123);g.config(3,0,1,0);g.reelVolume(2);g.dialReset();
  let elapsed=0,position=0,motor=0,audible=0;
  g.dialSample(position,0);assert.equal(g.rumbleEvent(10000,1),0);assert(!hasAudio());
  for(let packet=0;packet<500;packet++){
    elapsed+=8;position=(position+192)&4095;
    assert.equal(g.dialSample(position,elapsed),192/4096);
    if(g.rumbleEvent(10000+elapsed,1)===9)motor++;
    if(hasAudio())audible++;
  }
  assert.equal(motor,110,'32ms physical haptic gating remains unchanged');
  assert.equal(audible,141,'24ms audio budget is independent without waveform backlog');
  for(let t=32;t<=320;t+=32){assert.equal(g.rumbleEvent(10000+elapsed+t,1),0);assert(!hasAudio());}
  console.log('PASS real WASM detents: CW/CCW, wrapped samples, pause, magnet dropout, click PCM, independent mute and silent synthetic winding.');
})().catch(e=>{console.error(e);process.exitCode=1;});
