const {showControl,chooseNamed}=require('./menu-controls.cjs');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright-core');

(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const url=pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
 try {
  for(const reduced of [false,true]){
   const page=await browser.newPage({viewport:reduced?{width:390,height:844}:{width:960,height:760},hasTouch:reduced,isMobile:reduced,reducedMotion:reduced?'reduce':'no-preference'});
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
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
     let varied=true,valid=true;
     for(const spot of [16,4,3,2]){
       const pre=sample(spot,900),post=sample(spot,1600);
       valid&&=pre.every(c=>c<64||c===255)&&pre.includes(255);
       varied&&=new Set(pre).size>=8&&pre.some((c,i)=>c!==post[i]);
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
     return {varied,valid,matched,checked};
   });
   assert(pixels.valid&&pixels.varied&&pixels.matched&&pixels.checked>50,JSON.stringify(pixels));
   const routes=await page.evaluate(()=>['Kwan Phayao','Salween River','Mekong at Nong Khai','Cheow Lan Lake'].map(name=>{
     const l=atlas.locations.find(r=>r.name===name);return sceneryEngine.arrivalLanding(l.id,l.pool);
   }));
   assert.deepEqual(routes,[0,1,2,3],'water-specific approaches');
   assert(shapes.every(s=>s.valid));assert.equal(new Set(shapes.map(s=>s.family)).size,4);
   const observeTravel=()=>page.evaluate(()=>{
    window.arrivalProbe=new Promise((resolve,reject)=>{
     const lcd=$('lcdUI'), snapshot=()=>[g.state(),g.age(),held,action,turns,menu.open];
     const key=(type)=>$('act').dispatchEvent(new KeyboardEvent(type,
       {key:'r',code:'KeyR',bubbles:true,cancelable:true}));
     let start=null,before,after;
     const timeout=setTimeout(()=>{observer.disconnect();reject(new Error(start===null?'Did not observe arrival start':'Did not observe arrival end'));},60000);
     const observer=new MutationObserver(()=>{
      if(start===null&&arrivalSince!==null){
       start=arrivalSince;before=snapshot();key('keydown');after=snapshot();
      }else if(start!==null&&arrivalSince===null){
       const end=snapshot(),duration=performance.now()-start;
       observer.disconnect();clearTimeout(timeout);key('keyup');
       resolve({before,after,end,duration});
      }
     });
     observer.observe(lcd,{attributes:true,attributeFilter:['data-arriving']});
    });
    // Keep an observation timeout from producing an unhandled page error
    // before the test attaches its awaiting evaluation.
    window.arrivalProbe.catch(()=>{});
   });
   await travel('Chao Phraya River','Dusk',reduced?undefined:observeTravel);
   if(!reduced){
    const {before,after,end,duration}=await page.evaluate(()=>window.arrivalProbe);
    const neutral=[0,0,false,false,0,false];
    assert.deepEqual(before,neutral,'Start the trip with neutral fishing inputs');
    assert.deepEqual(after,neutral,'Travel must quarantine the dispatched reel key');
    assert.deepEqual(end,neutral,'Fishing remains neutral until travel naturally ends');
    assert(duration>=4180&&duration<5300,'4.2 second arrival, measured '+duration);
   }else{
    await page.locator('#arrivalSkip').waitFor({state:'visible'});
    assert.equal(await page.evaluate(()=>g.state()),0);
    const same=await page.evaluate(async()=>{
      draw();const first=canvas.toDataURL();await new Promise(r=>setTimeout(r,90));draw();return first===canvas.toDataURL();
    });
    assert(same,'Reduced-motion arrival should be completely static');
    await page.waitForTimeout(540);assert.equal(await page.locator('#arrivalSkip').isVisible(),false,'Reduced motion ends after a short static card');
   }
   assert.equal(await page.evaluate(()=>g.state()),0);
   await travel(null,'Night');assert.equal(await page.locator('#arrivalSkip').isVisible(),false,'Time-only selection');
   await travel('Kwan Phayao','Day');await page.locator('#arrivalSkip').waitFor({state:'visible'});
   if(!reduced&&process.env.ARRIVAL_CAPTURE){
    await page.waitForTimeout(1850);await page.locator('#scene').screenshot({path:process.env.ARRIVAL_CAPTURE});
   }
   await page.locator('#arrivalSkip').click();await page.waitForTimeout(85);assert.equal(await page.evaluate(()=>g.state()),0,'Skip is consumed before the next tap');
   await page.locator('#act').click();await page.waitForFunction(()=>g.state()===1||g.state()===2);
   await page.reload();await page.waitForFunction(()=>!document.getElementById('act').disabled);
   assert.equal(await page.locator('#arrivalSkip').isVisible(),false);
   assert.equal(await page.locator('#spot').textContent(),'Kwan Phayao');
   await travel('Krabi coastal waters','Dawn');await page.locator('#arrivalSkip').waitFor({state:'visible'});
   assert.equal(await page.evaluate(()=>sceneryEngine.arrivalLanding(placeId,locationId)),3);
   await page.locator('#arrivalSkip').click();
   assert.deepEqual(errors,[]);
   await page.close();
  }
  console.log('PASS desktop and phone destination travel, first-person walking, hiking, driving and boating, natural 4.2 s completion, reduced motion, skip, controls, time-only changes and saved spot restore.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
