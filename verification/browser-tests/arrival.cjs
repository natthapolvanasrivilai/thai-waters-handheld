const {showControl,chooseNamed}=require('./menu-controls.cjs');
const {captureReloadStartup,readCheckpoint,reloadFailureText}=require('./reload-trace.cjs');
const assert = require('node:assert/strict');
const path = require('node:path');
const {openPersistenceEntry}=require('./persistence-entry.cjs');
const {chromium} = require('playwright-core');

(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 let entry;
 try {
  entry=await openPersistenceEntry(path.resolve(__dirname,'../../game/Thai-Waters-play.html'));
  const {url}=entry;
  for(const reduced of [false,true]){
   const page=await browser.newPage({viewport:reduced?{width:390,height:844}:{width:960,height:760},hasTouch:reduced,isMobile:reduced,reducedMotion:reduced?'reduce':'no-preference'});
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(captureReloadStartup);
  await page.goto(url);await page.waitForFunction(()=>!document.getElementById('act').disabled);
   if(await page.locator('#product').isVisible())await page.locator('#viewMode').click();
   assert.match(await page.title(),/Thai Waters/);
   assert.equal(await page.locator('#arrivalSkip').isVisible(),false,'Boot must start directly at the saved water');
   async function travel(name,period,beforeSubmit){
    await page.locator('#openMenu').click();await page.locator('[data-to=spots]').click();
    if(name){await showControl(page,'#places');await page.getByRole('button',{name:/Fishing location ·/}).click();await chooseNamed(page,name);}
    if(period){await showControl(page,'#period');await page.getByRole('button',{name:/Pond time ·/}).click();await page.getByRole('option',{name:period,exact:true}).click();}
    await showControl(page,'#fishHere');if(beforeSubmit)await beforeSubmit();await page.locator('#fishHere').click();
   }
   const shapes=await page.evaluate(()=>{
    const art=(site,age)=>{
      const n=sceneryEngine.sampleArrival(site,atlas.locations[site].pool,age);
      const data=new Int16Array(sceneryEngine.memory.buffer,sceneryEngine.arrivalShapes(),n*8);
      return {n,hash:data.reduce((h,v)=>Math.imul(h^v,16777619),2166136261)};
    };
    return atlas.locations.map(l=>{
      const a=art(l.id,630),b=art(l.id,1960),c=art(l.id,630);
      return {valid:a.n>0&&a.n<384&&a.hash===c.hash&&a.hash!==b.hash,
              family:sceneryEngine.arrivalLanding(l.id,l.pool)};
    });
   });
   const pixels=await page.evaluate(()=>{
     const sample=(place,ms)=>{
       const ptr=sceneryEngine.arrivalPixels(place,atlas.locations[place].pool,ms);
       return new Uint8Array(sceneryEngine.memory.buffer,ptr,240*160).slice();
     };
     let varied=true,valid=true,bankReveal=true;
     for(const spot of [16,4,3,2]){
       const pre=sample(spot,900),post=sample(spot,1600);
       valid&&=pre.every(c=>c<64||c===255)&&pre.includes(255);
       varied&&=new Set(pre).size>=8&&pre.some((c,i)=>c!==post[i]);
       const occupied=layer=>layer.reduce((n,c)=>n+(c!==255),0);
       const raising=occupied(sample(spot,3330)),last=occupied(sample(spot,3759));
       bankReveal&&=raising>0&&last<raising&&occupied(sample(spot,3760))===0;
     }
     // Read the real composited canvas. Source pixels below the captions must
     // fill their entire 2x2 LCD block with exactly their tinted palette color.
     const loc=placeId,age=1150,layer=sample(loc,age);
     ctx.save();paintArrival(age,0);ctx.restore();
     const canvasPixels=new Uint32Array(ctx.getImageData(0,0,480,320).data.buffer);
     let checked=0,matched=true;
     for(let y=36;y<142;y++)for(let x=0;x<240;x++){
       const k=layer[y*240+x];if(k===255)continue;
       let j=y*960+2*x;checked++;
       for(const delta of [0,1,480,481])matched&&=canvasPixels[j+delta]===arrivalPalette[k];
     }
     return {varied,valid,bankReveal,matched,checked};
   });
   assert(pixels.valid&&pixels.varied&&pixels.bankReveal&&pixels.matched&&pixels.checked>50,JSON.stringify(pixels));
   const routes=await page.evaluate(()=>['Kwan Phayao','Salween River','Mekong at Nong Khai','Cheow Lan Lake'].map(name=>{
     const l=atlas.locations.find(r=>r.name===name);return sceneryEngine.arrivalLanding(l.id,l.pool);
   }));
   assert.deepEqual(routes,[0,1,2,3],'water-specific approaches');
   assert(shapes.every(s=>s.valid));assert.equal(new Set(shapes.map(s=>s.family)).size,4);
   const probeTrip=(kind,capture=false)=>page.evaluate(({kind,capture})=>{
    window.arrivalProbe=new Promise((resolve,reject)=>{
     const lcd=$('lcdUI'),submit=$('fishHere'),skip=$('arrivalSkip');
     const state=()=>[g.state(),g.age(),held,action,turns,menu.open];
     const key=type=>$('act').dispatchEvent(new KeyboardEvent(type,
       {key:'r',code:'KeyR',bubbles:true,cancelable:true}));
     let observer,timeout,keydown=false;
     function finish(error,result){
      clearTimeout(timeout);observer?.disconnect();submit.removeEventListener('click',afterSubmit);
      if(keydown)key('keyup');
      if(error)reject(error);else resolve(result);
     }
     function afterSubmit(){
      try{
       // Capture the live feature after its actual submit handler in the same task.
       const start=arrivalSince,before=state();
       const visible=!skip.hidden&&skip.getClientRects().length>0&&getComputedStyle(skip).visibility==='visible';
       if(kind==='time'){finish(null,{started:start!==null,visible,phase:before[0]});return;}
       if(start===null||!visible)throw new Error('Destination did not show an active Skip control');
       const info={before,reduced:arrivalReduced,family:sceneryEngine.arrivalLanding(placeId,locationId)};
       if(kind==='skip'){
        if(capture){paintArrival(1850,0);info.capture=canvas.toDataURL('image/png');}
        skip.click();
        finish(null,{...info,after:state(),active:arrivalSince!==null,hidden:skip.hidden});
        return;
       }
       observer=new MutationObserver(()=>{
        if(arrivalSince!==null)return;
        finish(null,{...info,end:state(),hidden:skip.hidden,duration:performance.now()-start});
       });
       observer.observe(lcd,{attributes:true,attributeFilter:['data-arriving']});
       if(kind==='desktop'){
        keydown=true;key('keydown');info.after=state();
       }else{
        // Arrival is a translucent overlay; compare renders on the same base.
        const base=ctx.getImageData(0,0,canvas.width,canvas.height);
        paintArrival(0,0);const first=canvas.toDataURL();
        ctx.putImageData(base,0,0);
        paintArrival(500,0);info.static=first===canvas.toDataURL();
        ctx.putImageData(base,0,0);
       }
      }catch(e){finish(e);}
     }
     timeout=setTimeout(()=>finish(new Error('Timed out observing arrival '+kind)),60000);
     submit.addEventListener('click',afterSubmit,{once:true});
    });
    window.arrivalProbe.catch(()=>{});
   },{kind,capture});
   const checkTrip=()=>page.evaluate(()=>window.arrivalProbe);
   const neutral=[0,0,false,false,0,false];
   await travel('Chao Phraya River','Dusk',()=>probeTrip(reduced?'reduced':'desktop'));
   const natural=await checkTrip();
   assert.deepEqual(natural.before,neutral,'Arrival starts with neutral fishing inputs');
   assert.deepEqual(natural.end,neutral,'Fishing stays neutral until travel ends naturally');
   assert.equal(natural.hidden,true,'Natural completion hides Skip');
   assert.equal(natural.reduced,reduced,'Arrival uses the browser motion preference');
   if(reduced){
    assert(natural.static,'Reduced-motion arrival should be completely static');
    assert(natural.duration>=530&&natural.duration<1600,'Short reduced-motion card, measured '+natural.duration);
   }else{
    assert.deepEqual(natural.after,neutral,'Travel must quarantine the dispatched reel key');
    assert(natural.duration>=4180&&natural.duration<5300,'4.2 second arrival, measured '+natural.duration);
   }
   await travel(null,'Night',()=>probeTrip('time'));
   assert.deepEqual(await checkTrip(),{started:false,visible:false,phase:0},'Time-only selection does not start travel');
   await travel('Kwan Phayao','Day',()=>probeTrip('skip',!reduced&&Boolean(process.env.ARRIVAL_CAPTURE)));
   const kwan=await checkTrip();
   assert.deepEqual(kwan.before,neutral);
   assert.deepEqual(kwan.after,neutral,'Skip is consumed before the next tap');
   assert(!kwan.active&&kwan.hidden,'Skip finishes live travel');
   if(kwan.capture)require('node:fs').writeFileSync(process.env.ARRIVAL_CAPTURE,
    Buffer.from(kwan.capture.split(',')[1],'base64'));
   await page.evaluate(()=>{
    window.castProbe=new Promise((resolve,reject)=>{
     const timeout=setTimeout(()=>reject(new Error('No fishing transition after Act')),12000);
     $('act').addEventListener('click',()=>{
      const observe=()=>{
       const phase=g.state();
       if(phase===0)requestAnimationFrame(observe);
       else{clearTimeout(timeout);resolve(phase);}
      };
      observe();
     },{once:true});
    });
    window.castProbe.catch(()=>{});
   });
   await page.locator('#act').click();
   const placeName='Kwan Phayao';
   const {observed:castPhase,trace:beforeRestore,startup:beforeStartup}=await page.evaluate(readCheckpoint,{placeName,observe:'cast'});
   assert([1,2].includes(castPhase),'The tap after Skip starts fishing');
   try{
    await page.reload();await page.waitForFunction(()=>!document.getElementById('act').disabled);
    assert.equal(await page.locator('#arrivalSkip').isVisible(),false);
    assert.equal(await page.locator('#spot').textContent(),'Kwan Phayao');
   }catch(error){console.error(await reloadFailureText(page,{stage:reduced?'arrival-mobile':'arrival-desktop',before:beforeRestore,beforeStartup,expected:{placeName},pageErrors:errors.length}));throw error;}
   await travel('Krabi coastal waters','Dawn',()=>probeTrip('skip'));
   const krabi=await checkTrip();
   assert.equal(krabi.family,3,'Krabi uses the longtail-boat approach');
   assert.deepEqual(krabi.after,neutral,'Skip leaves the coastal trip ready to fish');
   assert(!krabi.active&&krabi.hidden,'Skip finishes the coastal trip');
   assert.deepEqual(errors,[]);
   await page.close();
  }
  console.log('PASS desktop and phone destination travel, first-person walking, hiking, driving and boating, natural 4.2 s completion, reduced motion, skip, controls, time-only changes and saved spot restore.');
 }finally{try{await browser.close();}finally{await entry?.close();}}
})().catch(e=>{console.error(e);process.exitCode=1;});
