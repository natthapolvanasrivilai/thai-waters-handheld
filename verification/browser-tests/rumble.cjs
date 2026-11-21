const {requireBootHome}=require('./boot-home-check.cjs');
const {showControl}=require('./menu-controls.cjs');
const {chromium}=require('playwright-core');
const {openPersistenceEntry}=require('./persistence-entry.cjs');
const path=require('node:path');
const assert=require('node:assert/strict');

(async()=>{
  const browser=await chromium.launch({
    executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless:true
  });
  let entry;
  try{
    entry=await openPersistenceEntry(path.resolve(process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html')));
    const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:390,height:844}});
    await page.addInitScript(()=>{
      window.pulses=[];
      Object.defineProperty(navigator,'vibrate',{configurable:true,value:pattern=>{pulses.push(pattern);return true;}});
    });
    await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
    await page.goto(entry.url);
    const play=await requireBootHome(page);
    assert.equal(await page.evaluate(()=>g.state()),0);
    await play.tap();
    await page.waitForFunction(()=>!document.querySelector('#act').disabled);
    async function openMix(){
      await page.locator('#openMenu').tap();
      await page.locator('[data-section=home] [data-to=sound]').tap();
    }
    await openMix();
    const sample=async type=>{const el=await showControl(page,'[data-pulse="'+type+'"]');await el.tap();};
    await showControl(page,'#rumbleLevel');await page.selectOption('#rumbleLevel','Off');await sample(4);assert.deepEqual(await page.evaluate(()=>pulses),[],'Off suppresses physical previews');
    await showControl(page,'#testPhoneMotor');await page.locator('#testPhoneMotor').tap();
    assert.equal(await page.locator('#rumbleLevel').inputValue(),'Medium');
    assert.deepEqual(await page.evaluate(()=>pulses.at(-1)),[46,45,46]);
    await page.evaluate(()=>pulses.length=0);
    for(const id of [4,5,6])await sample(id);
    const heard=await page.evaluate(()=>pulses);
    assert.deepEqual(heard,[[20,340,20,340,20],[195],[32,34,27,31,22]]);
    await page.locator('#back').tap();assert.equal(await page.evaluate(()=>pulses.at(-1)),0);
    await page.reload();
    const resume=await requireBootHome(page);
    assert.deepEqual(await page.evaluate(()=>[
      g.state(),$('rumbleLevel').value,localStorage.getItem('thai-waters-rumble')
    ]),[0,'Medium','2'],'Rumble preference is restored while Home still locks play');
    await resume.tap();
    await page.waitForFunction(()=>!document.querySelector('#act').disabled);
    await openMix();assert.equal(await page.locator('#rumbleLevel').inputValue(),'Medium');
    await page.locator('#resume').tap();
    await page.evaluate(()=>{
      // Cast an actual ray at night and advance to its first bottom hold.
      for(let seed=1;seed<10000;seed++){
        g.initialize(seed);g.visit(3,3);g.setBait(g.recommendedBait(41));g.advance(16,1,0,0);
        if(g.species()===41)break;
      }
      if(g.species()!==41)throw Error('fixture could not draw ray');
      g.advance(g.flightMs(),0,0,0);g.advance(6000,0,0,0);g.advance(10,0,1,0);
    });
    await page.waitForFunction(()=>pulses.some(p=>Array.isArray(p)&&p[0]===195));
    await openMix();assert.equal(await page.evaluate(()=>pulses.at(-1)),0);
    await page.evaluate(()=>{Object.defineProperty(navigator,'vibrate',{value:undefined});});
    await sample(6);assert.match(await page.locator('#rumbleStatus').textContent(),/visual preview/);
    console.log('PASS phone haptic patterns, enabled level persistence, silent Off, menu cancellation, visual fallback and live hooked ray.');
  } finally {try{await browser.close();}finally{await entry?.close();}}
})().catch(error=>{console.error(error);process.exitCode=1;});
