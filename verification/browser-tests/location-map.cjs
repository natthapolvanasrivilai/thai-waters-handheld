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
    if(location.href!==fileUrl)return;
    localStorage.setItem('thai-atlas-v2',JSON.stringify({
     schema:4,book:[],site:0,place:0,bait:0,time:4,weather:0,finish:0,rig:0,rank:[0,0,0],
     history:[],pending:null,pendingCapture:null
    }));
   },url);
   await p.goto(url);
   await requireBootHome(p);
   assert.equal(p.url(),url);
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
    const session=await c.newCDPSession(p);
    await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
    await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+40,y:y+20}]});
    assert.equal(await p.locator('#waterbodyMap').getAttribute('data-dragging'),'', 'touch move reached map pan');
    await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    await session.detach();
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
   await press('#mapTravel');
   await p.waitForFunction(()=>placeId===16);
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
   await press('#fishHere');
   await p.waitForFunction(()=>placeId===1);
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
   assert.deepEqual(errors,[]);assert.deepEqual(outside,[]);
   await c.close();
  }
  console.log('TW_LANE file '+crypto.createHash('sha256').update(fs.readFileSync(wanted)).digest('hex'));
  console.log('PASS bilingual map, attribution, exact list order, mouse/touch, save isolation, active catch, explicit and list-only travel');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
