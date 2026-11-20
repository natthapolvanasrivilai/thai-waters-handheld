const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const game = path.resolve(__dirname, '../../game');
const places = JSON.parse(fs.readFileSync(path.join(game,'locations.json')));
const bytes = fs.readFileSync(path.join(game, 'assets/landscape.wasm'));
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
const repeat = 524288;

async function check() {
  const {instance:{exports:e}} = await WebAssembly.instantiate(bytes);
  let base, palette, maxSpans=0;
  function load(id,p) {
    const address=e.paintPlace(id,p);
    base=new Uint8Array(e.memory.buffer,address,240*160);
    palette=new Uint32Array(e.memory.buffer,e.placePalette(),64);
  }
  function spans(ms,utcDayPlusOne=0) {
    const n=e.sampleAmbient(ms,utcDayPlusOne);
    assert.ok(n>0 && n<=256,'bounded span buffer');
    maxSpans=Math.max(n,maxSpans);
    return Buffer.from(new Uint8Array(e.memory.buffer,e.ambientSpans(),n*4));
  }
  function rgb(ops) {
    const raster=Buffer.from(base);
    for(let i=0;i<ops.length;i+=4){
      const [x,y,n,ink]=ops.subarray(i,i+4);
      for(let dx=0;dx<n;dx++)raster[(x+dx)*160+159-y]=ink;
    }
    const frame=Buffer.alloc(240*160*3);
    for(let y=0;y<160;y++)for(let x=0;x<240;x++)
      frame.writeUIntBE(palette[raster[x*160+159-y]],(y*240+x)*3,3);
    return frame;
  }
  let samples=0;
  for(const {id,name} of places)for(let p=0;p<4;p++){
    load(id,p);
    const clean=hash(base),distinct=new Set();
    for(let i=0;i<67;i++){
      const ms=(i*7168+id*257)>>>0,ops=spans(ms);
      for(let j=0;j<ops.length;j+=4){
        const [x,y,n,ink]=ops.subarray(j,j+4);
        assert.ok(x<240&&y<160&&n>0&&x+n<=240&&ink<57,name);
      }
      if(i<4)distinct.add(hash(rgb(ops)));
      if(i===29){
        spans(ms+repeat); // Voyages are deliberately not tied to the short weather repeat.
        assert.deepEqual(spans(ms),ops,'resampling after pause/fast-forward');
      }
      samples++;
    }
    assert.equal(distinct.size,4,name+' visibly animates in period '+p);
    assert.equal(hash(base),clean,'actors must leave a reusable clean background');
    const last=spans(0xffffffc0);spans(0);
    assert.deepEqual(spans(0xffffffc0),last,'sampling across rollover preserves deterministic frame');
  }
  // The raft is identifiable by its terracotta roof strokes. It crosses
  // once in a fixed route, leaves the lake, and waits out of view.
  function roofX(ops){
    const x=[];
    for(let i=0;i<ops.length;i+=4)if(ops[i+3]===42)x.push(ops[i]+ops[i+2]/2);
    return x.length?Math.round(x.reduce((a,b)=>a+b,0)/x.length):null;
  }
  load(0,1);
  assert.ok(!base.includes(42),'Mae Ngat base has no baked raft roof');
  const travel=Array.from({length:256},(_,i)=>roofX(spans(i*1024)));
  assert.ok(travel.some(x=>x===null)&&travel.some(x=>x!==null&&x<15)&&travel.some(x=>x>225));
  let forward=false,back=false;
  for(let i=1;i<travel.length;i++)if(travel[i]!==null&&travel[i-1]!==null){
    const dx=travel[i]-travel[i-1];forward||=dx>=2;back||=dx<=-2;
    assert.ok(Math.abs(dx)<12,'a continuous trip has no teleport');
  }
  assert.notEqual(forward,back,'a continuous passage is one-way');
  assert.ok(travel.filter(x=>x!==null).length<travel.length/4,'long quiet section between passes');
  function litPasses(id,period){
    load(id,period);let visible=0;
    for(let ms=0;ms<32*repeat;ms+=4096)if(roofX(spans(ms))!==null)visible++;
    return visible;
  }
  assert.ok(litPasses(0,1)>3*litPasses(0,3),'most raft trips rest overnight');
  assert.ok(litPasses(1,3)>120,'Chao Phraya still has occasional night ferry service');
  load(1,3);spans(282624);
  const ferryMix=e.ambientBoatMix();
  assert.ok((ferryMix&255)>0&&ferryMix>>8,'visible ferry has motor and wake');
  const ptr=e.ambientBoatPcm(ferryMix,2);
  assert.ok(new Int16Array(e.memory.buffer,ptr,256).some(n=>n!==0),'ferry has audible ambience');
  e.ambientBoatPcm(ferryMix,0);
  assert.ok(new Int16Array(e.memory.buffer,ptr,256).every(n=>n===0),'effects mute also mutes world boats');
  load(0,3);
  const duskBoundary=13*3600000; // 20:00 ICT.
  assert.ok(roofX(spans(44800,duskBoundary+1))!==null,'aft of a dusk departure remains visible after 20:00 ICT');
  assert.equal(roofX(spans(44800,duskBoundary+180000+1)),null,'night service applies to later departures');
  load(2,3);
  for(let ms=0;ms<repeat;ms+=4096){
    const o=spans(ms);for(let i=3;i<o.length;i+=4)assert.notEqual(o[i],46,'paper boats settle at night');
  }
  // On the bridge scene, the train/bridge is the sole terracotta structure.
  // Its pixels cannot be sampled by reflections or birds during a day cycle.
  load(81,1);
  assert.ok(base.includes(42),'anchored bridge/rail detail should survive');
  for(let ms=0;ms<repeat;ms+=1024){
    const o=spans(ms);
    for(let i=0;i<o.length;i+=4)for(let x=o[i];x<o[i]+o[i+2];x++){
      assert.ok(![40,41,42].includes(base[x*160+159-o[i+1]]),'anchored structure moved');
    }
  }
  console.log(samples+' sampled animations across 468 scenes; peak '+maxSpans+' / 256 spans; raft crossings, schedules, anchored structures and wrap verified.');
  const output=process.argv[2],captures=[
    [0,1,'raft-left',40,'084ef3783c5f3e6cb6c6617dcf2de81f6e891188088cb1a06930219b5646d20a'],
    [0,1,'raft-center',120,'543554db01ac172ad4a11e859998813021cfb8e3017e4913a20f9493e1236ccb'],
    [0,1,'raft-right',200,'fb3ec3287ad15e1c5bcc44b02a2e502bea01bbf0fa7b2e69aea2254db90d3584'],
    [1,3,'ferry-night',120,'a807971a49ba44d2ed3240c8aa4f55e3d2b96e9aced85036756bda2438e2f95b'],
    [2,0,'karst-dawn',null,'b7b32e87ed8450040f423410367ced85a8a5e4c75e317831323f5b38dbe700e4'],
    [100,2,'coast-dusk',null,'6f30d32206ae56d73d42dc3185f4fe6de145b0830586474ab148c2e3c78f551e']
  ];
  if(output)fs.mkdirSync(output,{recursive:true});
  for(const [id,p,label,target,expected] of captures){
    load(id,p);let ms=12000;
    if(target!==null){
      for(let t=0;t<repeat;t+=256){let x=roofX(spans(t));if(x!==null&&Math.abs(x-target)<=1){ms=t;break;}}
    }
    const frame=rgb(spans(ms));assert.equal(hash(frame),expected,label+' pixel regression');
    if(output){
      fs.writeFileSync(path.join(output,label+'.ppm'),Buffer.concat([Buffer.from('P6\n240 160\n255\n'),frame]));
      console.log(label,ms+' ms');
    }
  }
  const native=process.argv[3];
  if(native){
    const {execFileSync}=require('node:child_process');
    const panelDigests=execFileSync(path.resolve(native),{encoding:'utf8'}).trim().split(/\s+/);
    let k=0;
    for(const {id} of places)for(let p=0;p<4;p++){
      load(id,p);
      for(const ms of [11000,0xfffffe00]){
        const pixels=Buffer.from(base),o=spans(ms);
        for(let i=0;i<o.length;i+=4)for(let dx=0;dx<o[i+2];dx++)pixels[(o[i]+dx)*160+159-o[i+1]]=o[i+3];
        let digest=2166136261;
        for(const ink of pixels)digest=Math.imul(digest^ink,16777619)>>>0;
        assert.equal(digest.toString(16).padStart(8,'0'),panelDigests[k++],places[id].name+' native LCD mask and span parity');
      }
    }
    assert.equal(k,panelDigests.length);
    console.log(k+' web/host-native LCD frames match at every logical pixel after palette conversion.');
  }
}
check().catch(e=>{console.error(e);process.exitCode=1;});
