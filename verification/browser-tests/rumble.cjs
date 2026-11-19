const {chromium}=require('playwright-core');
const {pathToFileURL}=require('node:url');
const path=require('node:path');
const assert=require('node:assert/strict');

(async()=>{
  const browser=await chromium.launch({
    executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless:true
  });
  try{
    const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:390,height:844}});
    await page.addInitScript(()=>{
      window.pulses=[];
      Object.defineProperty(navigator,'vibrate',{configurable:true,value:pattern=>{pulses.push(pattern);return true;}});
    });
    await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await page.goto(pathToFileURL(path.resolve(process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html'))).href);
    await page.waitForFunction(()=>!document.querySelector('#act').disabled);
    async function openMix(){
      await page.locator('#openMenu').tap();
      await page.locator('[data-to=sound]').tap();
    }
    await openMix();
    const sample=type=>page.locator('[data-pulse="'+type+'"]').tap();
    await page.selectOption('#rumbleLevel','Off');await sample(4);assert.deepEqual(await page.evaluate(()=>pulses),[],'Off suppresses physical previews');
    await page.locator('#testPhoneMotor').tap();
    assert.equal(await page.locator('#rumbleLevel').inputValue(),'Medium');
    assert.deepEqual(await page.evaluate(()=>pulses.at(-1)),[46,45,46]);
    await page.evaluate(()=>pulses.length=0);
    for(const id of [4,5,6])await sample(id);
    const heard=await page.evaluate(()=>pulses);
    assert.deepEqual(heard,[[20,340,20,340,20],[195],[32,34,27,31,22]]);
    await page.locator('#back').tap();assert.equal(await page.evaluate(()=>pulses.at(-1)),0);
    await page.reload();await page.waitForFunction(()=>!document.querySelector('#act').disabled);
    await openMix();assert.equal(await page.locator('#rumbleLevel').inputValue(),'Medium');
    await page.locator('#resume').tap();
    await page.evaluate(()=>{
      // Cast an actual ray at night and advance to its first bottom hold.
      for(let seed=1;seed<10000;seed++){
        g.initialize(seed);g.visit(3,3);g.setBait(g.recommendedBait(41));g.advance(16,1,0,0);
        if(g.species()===41)break;
      }
      if(g.species()!==41)throw Error('fixture could not draw ray');
      g.advance(700,0,0,0);g.advance(6000,0,0,0);g.advance(10,0,1,0);
    });
    await page.waitForFunction(()=>pulses.some(p=>Array.isArray(p)&&p[0]===195));
    await openMix();assert.equal(await page.evaluate(()=>pulses.at(-1)),0);
    await page.evaluate(()=>{Object.defineProperty(navigator,'vibrate',{value:undefined});});
    await sample(6);assert.match(await page.locator('#rumbleStatus').textContent(),/visual preview/);
    console.log('PASS phone haptic patterns, enabled level persistence, silent Off, menu cancellation, visual fallback and live hooked ray.');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
