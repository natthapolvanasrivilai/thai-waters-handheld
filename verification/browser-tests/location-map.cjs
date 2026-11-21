'use strict';
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const {requireBootHome}=require('./boot-home-check.cjs');
const wanted=path.resolve(process.argv[2]||path.resolve(__dirname,'../../game/Thai-Waters-play.html'));
const url=pathToFileURL(wanted).href;
const orderedIds=require('../../game/locations.json').map(l=>String(l.id));
assert.equal(orderedIds.length,117);
const picked='16', unmapped='1';
assert.equal(orderedIds[1],unmapped);


(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH,headless:true});
 try{
  for(const touch of [false,true]){
   const c=await browser.newContext({offline:true,viewport:touch?{width:390,height:844}:{width:480,height:600},hasTouch:touch,isMobile:touch});
   const p=await c.newPage(),errors=[],outside=[];
   p.setDefaultTimeout(6000);
   p.setDefaultNavigationTimeout(12000);
   p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^https?:/.test(r.url()))outside.push(r.url());});
   const press=async s=>touch?p.locator(s).tap():p.locator(s).press('Enter');
   await p.addInitScript(fileUrl=>{
    if(location.href!==fileUrl||localStorage.getItem('thai-atlas-v2')!==null)return;
    localStorage.setItem('thai-atlas-v2',JSON.stringify({
     schema:4,book:[],site:0,place:0,bait:0,time:4,weather:0,finish:0,rig:0,rank:[0,0,0],
     history:[],pending:null,pendingCapture:null
    }));
   },url);
   await p.goto(url);
   await requireBootHome(p);
   assert.equal(p.url(),url);
   const name=touch?'mobile touch':'desktop keyboard';
   console.log('Map run · '+name);
   const touchSession=touch?await c.newCDPSession(p):null;
   await p.evaluate(()=>{
    window.mapTravelTrace=[];
    for(const type of ['pointerdown','pointerup','pointercancel','touchend','click']){
     window.addEventListener(type,e=>{
      const id=e.target.closest?.('button')?.id;
      if(id!=='mapTravel'&&id!=='fishHere')return;
      const row={type,id,pointer:e.pointerType??null,trusted:e.isTrusted};
      mapTravelTrace.push(row);
      queueMicrotask(()=>{row.prevented=e.defaultPrevented;});
     },{capture:true});
    }
   });
   async function touchCenter(selector){
    const button=p.locator(selector);
    await button.scrollIntoViewIfNeeded();
    const b=await button.boundingBox();assert(b,name+' '+selector);
    const x=Math.round(b.x+b.width/2),y=Math.round(b.y+b.height/2);
    assert.equal(await p.evaluate(({x,y})=>document.elementFromPoint(x,y)?.closest('button')?.id,{x,y}),selector.slice(1),
     'Physical button center must be hittable: '+selector);
    return {x,y};
   }
   async function activateTravel(selector,id){
    const button=p.locator(selector),key=selector.slice(1);
    assert(await button.isVisible()&&await button.isEnabled(),name+' '+key+' must be visible and enabled');
    const gate=await p.evaluate(()=>({allowed:spotTravelAllowed(),temporary:sessionOnly,menu:menu.open,page:menuPage}));
    assert.deepEqual(gate,{allowed:true,temporary:false,menu:true,page:'spots'});
    const trace=()=>p.evaluate(()=>mapTravelTrace);
    await p.evaluate(()=>{mapTravelTrace.length=0;});
    if(touchSession){
     const point=await touchCenter(selector);
     await touchSession.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});
     // Same real contact interval as gallery-history, rather than a zero-duration tap.
     await new Promise(resolve=>setTimeout(resolve,65));
     await touchSession.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    }else await button.press('Enter');
    const mapTouch=Boolean(touchSession&&key==='mapTravel'),eventType=mapTouch?'pointerup':'click';
    await p.waitForFunction(({key,eventType})=>mapTravelTrace.some(e=>e.type===eventType&&e.trusted&&e.id===key),
     {key,eventType},{timeout:2500}).catch(()=>{});
    const events=await trace();
    const context=()=>name+' '+selector+' events='+JSON.stringify(events)+' errors='+JSON.stringify(errors);
    const trusted=kind=>events.filter(e=>e.type===kind&&e.trusted&&e.id===key);
    if(mapTouch){
     assert.deepEqual(trusted('pointerdown').map(e=>e.pointer),['touch'],context());
     assert.deepEqual(trusted('pointerup').map(e=>e.pointer),['touch'],context());
     assert.equal(trusted('click').length,0,'map touch needs no downstream compatibility click: '+context());
    }else assert.equal(trusted('click').length,1,context());
    // chooseSpot updates synchronously in the click handler. A longer arrival wait
    // would obscure the difference between missing input and an application error.
    assert.equal(await p.evaluate(()=>placeId),id,context());
    assert(!await p.evaluate(()=>menu.open),context());
   }
   const credits=JSON.parse(await p.locator('#mapSources').textContent());
   const msea=credits.mapSources['msea-res-s1'];
   assert.equal(msea.creator.length,3);
   assert.equal(msea.licenseUrl,'https://creativecommons.org/licenses/by/4.0/');
   assert.equal(msea.identifier,'https://doi.org/10.5194/essd-17-2693-2025');
   assert.match(msea.changes,/rounded/);
   assert.equal(credits.featureSources.length,9);
   const chooseKwanByKeyboard=async()=>{
    const trigger=p.locator('#mapWaterbody + button'),overlay=p.locator('#lcdPicker');
    await trigger.press('ArrowDown');
    await overlay.waitFor();
    assert.equal(await overlay.getAttribute('data-field'),'mapWaterbody');
    assert.equal(await trigger.getAttribute('aria-expanded'),'true');
    const index=await p.locator('#mapWaterbody').evaluate(s=>[...s.options].findIndex(o=>o.value==='16'));
    assert(index>0&&index<6,'Kwan Phayao appears on the first picker page');
    const focused=p.locator('#lcdPicker [role=option]:focus');
    await p.keyboard.press('Home');
    for(let i=0;i<index;i++)await p.keyboard.press('ArrowDown');
    assert.equal(await focused.getAttribute('data-index'),String(index));
    assert.match(await focused.textContent(),/^Kwan Phayao$/i);
    await p.keyboard.press('Enter');
    assert(await overlay.isHidden());
    assert.equal(await trigger.getAttribute('aria-expanded'),'false');
   };
   const assertList=async()=>assert.deepEqual(await p.locator('#places option').evaluateAll(xs=>xs.map(x=>x.value)),orderedIds);

   for(const lang of ['th','en']){
    await press('[data-language="'+lang+'"]');
    await press('[data-section=boot-home] [data-to=spots]');
    assert(await p.locator('#waterbodyMap').isVisible());
    assert(await p.locator('#mapTravel').isDisabled(),'boot preview never travels');
    await assertList();
    assert.equal(await p.locator('#mapWaterbody option').count(),10);
    assert(await p.locator('#mapAccessNote').isVisible());
    assert.match(await p.locator('#mapAccessNote').innerText(),lang==='th'?/ไม่ใช่จุดเข้าตกปลา/:/not a fishing-access point/);
    const r=await p.locator('#menu').boundingBox();
    for(const s of ['#waterbodyMap','#mapAccessNote','#mapReset','#mapToList','#mapWaterbody + button']){
     const b=await p.locator(s).boundingBox();assert(b&&b.x>=r.x-1&&b.y>=r.y-1&&b.x+b.width<=r.x+r.width+1&&b.y+b.height<=r.y+r.height+1,s);
    }
    await press('#mapToList');
    assert(await p.locator('#locationMapOpen').isVisible());
    for(const query of lang==='th'?['Kwan Phayao','กว๊านพะเยา']:['Kwan Phayao']){
     await p.locator('#searchSpot').fill(query);
     assert.equal(await p.locator('#places').inputValue(),picked);
    }
    await p.locator('#searchSpot').fill('');
    await assertList();
    await press('#back');
   }
   await press('#bootResume');await press('#openMenu');await press('[data-section=home] [data-to=spots]');
   assert(await p.locator('#locationMapOpen').isVisible(),'in-game entry preserves list-first navigation');
   await press('#locationMapOpen');
   assert(!(await p.locator('#mapWaterbody option').evaluateAll(xs=>xs.map(x=>x.value))).includes(unmapped));
   const snapshot=()=>p.evaluate(()=>({
    live:placeId,pending:pendingSpot,engine:g.state(),raw:localStorage.getItem('thai-atlas-v2')
   }));
   const beforeState=await snapshot();
   assert.equal(beforeState.live,0);
   assert.equal(JSON.parse(beforeState.raw).place,0);
   const before=await p.locator('#spot').textContent(), prior=await p.locator('#places').inputValue();
   const b=await p.locator('#waterbodyMap').boundingBox();
   const x=b.x+b.width*(115+(99.875-101.1)*10.2)/230,y=b.y+b.height*(93+(13.1-19.171)*10.6)/186;
   if(touch)await p.touchscreen.tap(x,y);else await p.mouse.click(x,y);
   assert.equal(await p.locator('#mapWaterbody').inputValue(),picked);
   if(touch){
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+40,y:y+20}]});
    assert.equal(await p.locator('#waterbodyMap').getAttribute('data-dragging'),'', 'touch move reached map pan');
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
   }else{
    await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x+40,y+20,{steps:5});
    assert.equal(await p.locator('#waterbodyMap').getAttribute('data-dragging'),'', 'mouse move reached map pan');
    await p.mouse.up();
    await p.locator('#waterbodyMap').press('Home');
    await chooseKwanByKeyboard();
   }
   assert.equal(await p.locator('#mapWaterbody').inputValue(),picked);
   assert.equal(await p.locator('#places').inputValue(),prior);
   assert.equal(await p.locator('#spot').textContent(),before);
   assert(await p.locator('#arrivalSkip').isHidden());
   assert.deepEqual(await snapshot(),beforeState,'selection/pan must not change live, pending, engine or saved bytes');
   assert.equal(await p.locator('#mapWaterbody').inputValue(),picked);
   if(touchSession){
    const point=await touchCenter('#mapTravel');
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]});
    assert.deepEqual(await snapshot(),beforeState,'cancelled touch on Travel cannot relocate or save');
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:point.x+22,y:point.y}]});
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[point]});
    await touchSession.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    assert.deepEqual(await snapshot(),beforeState,'drag out and back on Travel cannot relocate or save');
   }
   await activateTravel('#mapTravel',16);
   await p.locator('#arrivalSkip').waitFor();
   assert.match(await p.locator('#spot').textContent(),/Kwan Phayao/i);
   const after=await snapshot();
   assert.equal(after.live,16);
   assert.equal(JSON.parse(after.raw).place,16,'confirmed travel updates the existing stable saved ID');
   // Reuse the normal list (no map pin) to prove list-only travel still works.
   if(await p.locator('#arrivalSkip').isVisible())await press('#arrivalSkip');
   await press('#openMenu');
   await press('[data-section=home] [data-to=spots]');
   await assertList();
   await p.locator('#searchSpot').fill('Chao Phraya River');
   assert.equal(await p.locator('#places').inputValue(),unmapped);
   await activateTravel('#fishHere',1);
   assert.equal(JSON.parse((await snapshot()).raw).place,1);
   await p.locator('#arrivalSkip').waitFor();
   if(await p.locator('#arrivalSkip').isVisible())await press('#arrivalSkip');

   if(!touch){
    // Same exact native catch restore used by the existing file-career tests.
    // The menu is opened before the catch so fixture does not bypass hidden UI controls.
    await press('#openMenu');
    await press('[data-section=home] [data-to=spots]');
    await p.evaluate(()=>{g.restoreCatch(41,atlas.fish[41].low);pendingCapture=captureLanding();save();});
    const pending=await snapshot();
    assert.equal(pending.engine,5);
    assert.equal(JSON.parse(pending.raw).pending[0],41);
    await press('#locationMapOpen');
    await chooseKwanByKeyboard();
    assert.equal(await p.locator('#mapWaterbody').inputValue(),picked);
    assert(await p.locator('#mapTravel').isDisabled(),'unfiled native catch forbids travel even from an open map');
    await p.locator('#mapTravel').evaluate(b=>b.click());
    assert.deepEqual(await snapshot(),pending,'disabled map cannot discard or relocate an active catch');
   }
   const final=await snapshot();
   await p.reload();
   await requireBootHome(p);
   assert.equal(await p.evaluate(()=>placeId),1,name+' retains selected ID after real reload');
   assert.equal(await p.evaluate(()=>localStorage.getItem('thai-atlas-v2')),final.raw,
    name+' restores the exact saved file without rewriting it');
   assert.deepEqual(errors,[]);assert.deepEqual(outside,[]);
   if(touchSession)await touchSession.detach();
   await c.close();
  }
  console.log('TW_LANE file '+crypto.createHash('sha256').update(fs.readFileSync(wanted)).digest('hex'));
  console.log('PASS bilingual map, attribution, exact list order, mouse/touch, save isolation, active catch, explicit and list-only travel');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
