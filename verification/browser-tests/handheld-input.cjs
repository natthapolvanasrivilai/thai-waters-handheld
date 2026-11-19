const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');

async function verify(browser,mobile){
 const page=await browser.newPage({viewport:mobile?{width:390,height:844}:{width:1180,height:780},isMobile:mobile,hasTouch:mobile});
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 try{
  await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  const target=process.env.PLAYTEST_URL||pathToFileURL(process.env.PLAYTEST_HTML||path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
  await page.goto(target);await page.waitForFunction(()=>g&&typeof g.handheldRodHigh==='function');
  const press=code=>page.keyboard.press(code);
  await press('v');await press('c');await press('9');
  assert.equal(await page.evaluate(()=>g.state()),0,'No game events before opt-in');
  await page.locator('#openMenu').click();await page.locator('[data-to=sensors]').click();
  const enable=page.locator('#handheldEnable'),status=page.locator('#handheldStatus');
  await enable.check();assert.match(await status.textContent(),/Waiting/);
  await press('o');assert.equal(await page.evaluate(()=>dialAngle),0,'No rewind or turns before heartbeat');
  await press('v');assert.match(await status.textContent(),/Receiving/);
  await press('c');await press('h');await press('9');await press('o');
  assert.deepEqual(await page.evaluate(()=>[g.state(),g.rodUp(),dialAngle]),[0,0,0],'Motion bench consumes packets without playing');
  await page.locator('#back').click();await page.locator('[data-to=spots]').click();
  await page.locator('#searchSpot').focus();await press('v');await press('c');await press('h');await press('o');await press('9');
  assert.equal(await page.locator('#searchSpot').inputValue(),'','Controller packets cannot type into the location search');
  await page.keyboard.type('xyz');assert.equal(await page.locator('#searchSpot').inputValue(),'xyz');
  await page.locator('#resume').click();await press('v');await press('9');
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
  // A reproducible rock encounter exercises the signed reverse input in the actual game engine.
  await page.evaluate(()=>{g.initialize(5);g.place(0,0);g.setAim(g.zoneX(2),g.zoneY(2));});
  await press('v');await press('c');
  await page.waitForFunction(()=>g.state()===7&&g.contact()===2,null,{timeout:8000});
  await press('9');await press('p');await page.waitForTimeout(90);
  assert.equal(await page.evaluate(()=>g.state()),7,'Rock stays snagged when the rod is raised');
  await press('1');await press('p');
  await page.waitForFunction(()=>g.state()===2,null,{timeout:2500});
  // Hook only on the explicit lift packet; a high angle alone never hooks a fish.
  await page.evaluate(()=>{g.initialize(36);g.place(0,0);g.setAim(.88,.85);});
  await press('v');await press('c');
  await page.waitForFunction(()=>g.state()===3,null,{timeout:18000,polling:25});
  await press('v');await press('9');assert.equal(await page.evaluate(()=>g.state()),3);
  await press('h');await page.waitForFunction(()=>g.state()===4);
  await page.waitForFunction(()=>!handheldInput.ownsRod()&&!g.rodUp()&&rodAngle===0,null,{timeout:5500});
  assert.match(await status.textContent(),/Waiting/);
  await press('9');assert.equal(await page.evaluate(()=>g.rodUp()),0,'Stale reports require a new heartbeat');
  await press('v');await press('9');await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  assert.deepEqual(await page.evaluate(()=>[handheldInput.ownsRod(),g.rodUp(),rodAngle]),[false,0,0]);
  await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
  await press('v');await press('9');assert.equal(await page.evaluate(()=>g.rodUp()),1);
  await page.locator('#openMenu').click();assert.equal(await page.evaluate(()=>g.rodUp()),0);
  await page.locator('[data-language=th]').click();await page.locator('[data-to=sensors]').click();
  assert.match(await status.textContent(),/[ก-๙]/);await enable.uncheck();
  assert.match(await status.textContent(),/ปิด/);await page.locator('#resume').click();
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
