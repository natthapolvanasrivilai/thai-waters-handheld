const {requireBootHome}=require('./boot-home-check.cjs');
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');

// Exercise the real focusable menu controls without waiting for WebGL frame
// stability, which is unrelated to this HID keyboard regression.
async function setPairedRod(page,enable,wantChecked){
 const indices=()=>enable.evaluate(el=>{
  const sheet=el.closest('.menu-sheet');
  const panel=sheet?.parentElement;
  if(!panel||panel.hidden)return [-1,-1];
  const sheets=[...panel.querySelectorAll(':scope > .menu-sheet')];
  return [sheets.indexOf(sheet),sheets.findIndex(s=>!s.hidden)];
 });
 let [target,active]=await indices();
 assert(target>=0&&active>=0,'Sensors menu has a real active sheet and Paired rod target');
 while(active!==target){
  const step=Math.sign(target-active);
  const arrow=page.locator(step<0?'#sheetPrev':'#sheetNext');
  assert(await arrow.isVisible()&&await arrow.isEnabled(),'The visible player navigation arrow is enabled');
  await arrow.press('Enter');
  const actual=await indices();
  assert.deepEqual(actual,[target,active+step],'Native arrow activation advances exactly one sheet');
  active=actual[1];
 }
 assert(await enable.isVisible()&&await enable.isEnabled(),'The Paired rod checkbox is accessible');
 assert.equal(await enable.isChecked(),!wantChecked,'The checkbox starts in the opposite state');
 await enable.press('Space');
 assert.equal(await enable.isChecked(),wantChecked,'Native checkbox activation updates its checked state');
}

// Use native button activation without waiting for stable pointer geometry.
async function pressButton(button){
 await button.waitFor({state:'visible'});
 assert(await button.isVisible()&&await button.isEnabled(),'The menu button is visible and enabled');
 await button.press('Enter');
}

async function verify(browser,mobile){
 const page=await browser.newPage({viewport:mobile?{width:390,height:844}:{width:1180,height:780},isMobile:mobile,hasTouch:mobile});
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 try{
  // Only pin wall time for the world seed; performance.now and heartbeat timers stay real.
  await page.clock.setFixedTime(new Date('2026-01-12T23:00:00Z'));
  await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  const target=process.env.PLAYTEST_URL||pathToFileURL(process.env.PLAYTEST_HTML||path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
  await page.goto(target);
  const play=await requireBootHome(page);
  const press=code=>page.keyboard.press(code);
  for(const key of ['v','c','9','o'])await press(key);
  assert.deepEqual(await page.evaluate(()=>[g.state(),g.rodUp(),dialAngle]),[0,0,0],
   'Controller packets cannot cast, lift or wind while Home gates play');
  assert(await play.isVisible());assert(await page.locator('#act').isDisabled());
  await pressButton(play);
  await page.waitForFunction(()=>g&&typeof g.handheldRodHigh==='function'&&!$('act').disabled);
  await press('v');await press('c');await press('9');
  assert.equal(await page.evaluate(()=>g.state()),0,'No game events before opt-in');
  await pressButton(page.locator('#openMenu'));await pressButton(page.locator('[data-section=home] [data-to=sensors]'));
  const enable=page.locator('#handheldEnable'),status=page.locator('#handheldStatus');
  await setPairedRod(page,enable,true);assert.match(await status.textContent(),/Waiting/);
  await press('o');assert.equal(await page.evaluate(()=>dialAngle),0,'No rewind or turns before heartbeat');
  await press('v');assert.match(await status.textContent(),/Receiving/);
  await press('c');await press('h');await press('9');await press('o');
  assert.deepEqual(await page.evaluate(()=>[g.state(),g.rodUp(),dialAngle]),[0,0,0],'Motion bench consumes packets without playing');
  await pressButton(page.locator('#back'));await pressButton(page.locator('[data-section=home] [data-to=spots]'));
  await page.locator('#searchSpot').focus();await press('v');await press('c');await press('h');await press('o');await press('9');
  assert.equal(await page.locator('#searchSpot').inputValue(),'','Controller packets cannot type into the location search');
  await page.keyboard.type('xyz');assert.equal(await page.locator('#searchSpot').inputValue(),'xyz');
  await pressButton(page.locator('#resume'));await press('v');await press('9');
  assert.deepEqual(await page.evaluate(()=>[g.rodUp(),rodAngle,g.state()]),[1,28,0],'High posture is sustained without a synthetic cast');
  await press('5');assert.equal(await page.evaluate(()=>g.rodUp()),1,'Middle pitch retains prior high state');
  await press('1');assert.equal(await page.evaluate(()=>g.rodUp()),0);
  await press('Shift+o');assert.equal(await page.evaluate(()=>dialAngle),0,'Shift-modified key is not a controller report');
  await page.keyboard.down('j');await page.keyboard.down('j');await page.keyboard.up('j');
  assert.equal(await page.evaluate(()=>dialAngle),15,'Repeat does not duplicate a detent');
  await press('k');
  for(const key of ['j','u','i','o'])await press(key);
  assert.equal(await page.evaluate(()=>dialAngle),225);
  for(const key of ['k','n','m','p'])await press(key);
  assert.equal(await page.evaluate(()=>dialAngle),0,'Four signed detent packet sizes round-trip');
  // Park only the game rAF for the two transient gameplay fixtures. Real HID
  // events, performance.now and heartbeat expiry timers still run normally.
  await page.evaluate(()=>new Promise(resolve=>{
   const schedule=window.requestAnimationFrame;
   window.resumeHidFixture=()=>{
    window.requestAnimationFrame=schedule;
    prev=performance.now();schedule.call(window,frame);
    delete window.resumeHidFixture;
   };
   window.requestAnimationFrame=cb=>{
    if(cb===frame){resolve();return 0;}
    return schedule.call(window,cb);
   };
  }));
  const tick=()=>page.evaluate(()=>{frame(prev+16);return g.state();});
  try{
   // A reproducible rock encounter exercises signed payout in the real engine.
   assert.deepEqual(await page.evaluate(()=>{
    g.initialize(5);g.place(0,0);g.conditions(1,1,20466);g.setAim(g.zoneX(2),g.zoneY(2));
    return [currentSlot,g.featureAt(g.aimX(),g.aimY()),turns];
   }),[0,2,0],'Dawn fixture targets a rock with no preceding reel reports');
   await press('v');await press('c');
   assert.equal(await tick(),1,'HID cast starts engine flight');
   assert.deepEqual(await page.evaluate(()=>{
    g.advance(g.flightMs(),0,0,0);
    return [g.state(),g.contact()];
   }),[7,2],'The handheld cast lands on the selected rock');
   for(const high of [true,false]){
    const before=await page.evaluate(()=>dialAngle);
    await press('v');await press(high?'9':'1');
    assert.equal(await page.evaluate(()=>g.rodUp()),Number(high),'HID pitch reaches the engine before payout');
    await press('v');await press('p');
    const [angle,payout]=await page.evaluate(()=>[dialAngle,turns]);
    assert.equal(angle-before,-120,'One real reverse packet moves eight detents');
    assert(payout<=-.2999,'The AS5600 emulation queued enough actual reverse turns');
    const expected=high?[7,2,0,0]:[2,0,0,0];
    assert.deepEqual(await page.evaluate(()=>{
     frame(prev+16);
     return [g.state(),g.contact(),g.releaseProgress(),turns];
    }),expected,high?'Raised rod stays snagged and does not retain payout':'Low rod releases the rock on actual payout');
   }
   // Hook only on the explicit lift packet; the high posture never hooks alone.
   await page.evaluate(()=>{g.initialize(36);g.place(0,0);g.conditions(1,1,20466);g.setAim(.88,.85);});
   await press('v');await press('c');
   assert.equal(await tick(),1,'HID cast starts engine flight');
   assert.equal(await page.evaluate(()=>{
    for(let elapsed=0;elapsed<18000&&[1,2].includes(g.state());elapsed+=40)g.advance(40,0,0,0);
    return g.state();
   }),3,'Fixture reaches a bite before testing the input');
   await press('v');await press('9');
   assert.deepEqual(await page.evaluate(()=>{frame(prev+16);return [g.state(),g.rodUp()];}),[3,1],
    'High HID posture alone does not hook the fish');
   await press('v');await press('h');
   assert.equal(await tick(),4,'Explicit HID lift hooks the fish');
  }finally{await page.evaluate(()=>window.resumeHidFixture());}
  await page.waitForFunction(()=>!handheldInput.ownsRod()&&!g.rodUp()&&rodAngle===0,null,{timeout:5500,polling:100});
  assert.match(await status.textContent(),/Waiting/);
  await press('9');assert.equal(await page.evaluate(()=>g.rodUp()),0,'Stale reports require a new heartbeat');
  await press('v');await press('9');await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  assert.deepEqual(await page.evaluate(()=>[handheldInput.ownsRod(),g.rodUp(),rodAngle]),[false,0,0]);
  await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
  await press('v');await press('9');assert.equal(await page.evaluate(()=>g.rodUp()),1);
  await pressButton(page.locator('#openMenu'));assert.equal(await page.evaluate(()=>g.rodUp()),0);
  await pressButton(page.locator('#languageRow [data-language=th]'));await pressButton(page.locator('[data-section=home] [data-to=sensors]'));
  assert.match(await status.textContent(),/[ก-๙]/);await setPairedRod(page,enable,false);
  assert.match(await status.textContent(),/ปิด/);await pressButton(page.locator('#resume'));
  await press('v');await press('9');assert.equal(await page.evaluate(()=>g.rodUp()),0);
  assert.deepEqual(errors,[]);console.log('PASS '+(mobile?'mobile':'desktop')+' HID input, exact signed detents, physical cast/hook, rock payout, pitch hysteresis, neutral, menu safety and Thai labels');
 }finally{await page.close();}
}
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{await verify(browser,false);await verify(browser,true);}finally{await browser.close();}
 if(process.env.TEST_WEBKIT){
  const safari=await webkit.launch({headless:true});
  try{await verify(safari,true);}finally{await safari.close();}
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
