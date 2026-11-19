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
  console.log('PASS real WASM detents: CW/CCW, wrapped samples, pause, magnet dropout, click PCM, independent mute and silent synthetic winding.');
})().catch(e=>{console.error(e);process.exitCode=1;});
