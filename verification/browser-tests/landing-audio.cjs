const {chromium,devices}=require('playwright-core');
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
  const page=await browser.newPage({...devices['iPhone 13'],viewport:{width:844,height:390}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{
   // Silence music and the reel to isolate the live gameplay cue at the destination.
   localStorage.setItem('willow-v1-audio',JSON.stringify([3,0,0,2,0]));
   Object.defineProperty(navigator,'vibrate',{configurable:true,value:()=>true});
   window.landingProbe={heard:[],buffers:[]};
   const original=AudioNode.prototype.connect;
   AudioNode.prototype.connect=function(destination,...args){
    if(this instanceof AudioBufferSourceNode && destination===this.context.destination){
     const tap=window.landingProbe;
     if(!tap.analyser){
      tap.analyser=this.context.createAnalyser();tap.analyser.fftSize=512;
      const pcm=new Float32Array(tap.analyser.fftSize);
      setInterval(()=>{
       if(g?.state()!==5)return;
       tap.analyser.getFloatTimeDomainData(pcm);
       if(pcm.some(x=>Math.abs(x)>.02))tap.heard.push(g.age());
      },8);
     }
     original.call(this,tap.analyser);
     if(g?.state()===5 && this.buffer.getChannelData(0).some(x=>Math.abs(x)>.02))
      tap.buffers.push({age:g.age(),filed:g.filed()});
    }
    return original.call(this,destination,...args);
   };
  });
  const html=process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html');
  await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await page.goto(pathToFileURL(path.resolve(html)).href);
  await page.waitForFunction(()=>!!g && !$('act').disabled);
  await page.evaluate(()=>{
   // Select an uncommon fish, then start the same cast again with the real controls.
   const target=atlas.fish.findIndex((f,id)=>f.tier===1 && g.availableAt(id,placeId,currentSlot));
   if(target<0)throw Error('No eligible uncommon species at the fixture location');
   const bait=g.recommendedBait(target);
   for(let seed=1;seed<10000;++seed){
    g.initialize(seed);g.place(placeId,currentSlot);g.setBait(bait);g.advance(16,1,0,0);
    if(g.species()===target && !g.featureAt(g.aimX(),g.aimY())){
     g.initialize(seed);g.place(placeId,currentSlot);g.setBait(bait);return;
    }
   }
   throw Error('No suitable encounter');
  });
  await page.locator('#act').tap();
  await page.waitForFunction(()=>g.state()===3);
  await page.locator('#act').tap();
  await page.waitForFunction(()=>g.state()===4);
  let winding=false;
  for(let polls=0;polls<450;++polls){
   const [phase,run]=await page.evaluate(()=>[g.state(),g.surging()]);
   if(phase!==4)break;
   if(winding===!!run){
    if(run)await page.keyboard.up('r');else await page.keyboard.down('r');
    winding=!winding;
   }
   await page.waitForTimeout(70);
  }
  await page.keyboard.up('r');
  assert.equal(await page.evaluate(()=>g.state()),5);
  await page.waitForFunction(()=>g.age()>1800);
  const capture=await page.evaluate(()=>({
   buffers:landingProbe.buffers,heard:landingProbe.heard,metrics:$('metrics').textContent,
   count:g.caught(g.species()),reward:g.landingReward(),audio:audio.state
  }));
  assert.match(capture.metrics,/Uncommon/i);assert.equal(capture.count,0);assert.equal(capture.reward,3);
  assert.equal(capture.audio,'running');
  assert(capture.buffers.length>8 && capture.buffers.every(b=>b.age<1250 && !b.filed));
  assert(capture.heard.length>0 && capture.heard.every(t=>t<1450));
  assert(capture.heard[0]<450,'Fanfare begins as the catch card opens');
  await page.reload();
  await page.waitForFunction(()=>g?.state()===5);
  await page.locator('#dial').tap();
  await page.waitForFunction(()=>audio?.state==='running' && g.age()>1400);
  assert.deepEqual(await page.evaluate(()=>landingProbe.heard),[],'Restored card stays quiet');
  await page.locator('#catchContinue').tap();
  // A second filing request is harmless even if two controls dispatch in one frame.
  await page.evaluate(()=>fileSpecimen());
  await page.waitForFunction(()=>g.state()===0);
  assert.equal(await page.evaluate(()=>g.caught(g.species())),1);
  assert.deepEqual(await page.evaluate(()=>landingProbe.buffers),[],'Filing does not replay the celebration');
  const peakAfterResume=await page.evaluate(async()=>{
   await audio.suspend();
   g.initialize(1);g.visit(0,0);g.config(3,0,1,2);
   g.advance(16,1,0,0);g.advance(650,0,0,0);g.advance(6000,0,0,0);g.advance(16,0,1,0);
   g.config(3,0,0,2);
   for(let i=0;i<2400&&g.state()===4;i++)g.advance(16,0,0,g.surging()?0:.02);
   if(g.state()!==5||!g.fileCatch())throw Error('Suspended catch fixture failed');
   const ptr=g.samples();
   return new Int16Array(g.memory.buffer,ptr,512).some(sample=>sample!==0);
  });
  assert.equal(peakAfterResume,false,'An unconsumed cue expires when a catch is filed during audio interruption');
  assert.deepEqual(errors,[]);
  console.log('PASS trusted cast/lift/reel, live landing PCM before filing, silent held/restored card and double filing; first audible sample by '+capture.heard[0]+' ms.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
