const {showControl}=require('./menu-controls.cjs');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright-core');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  try {
    const page = await browser.newPage({viewport: {width: 960, height: 850}});
    await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await page.goto(pathToFileURL(process.env.GAME_HTML || path.resolve(__dirname, '../../game/Thai-Waters-play.html')).href);
    await page.waitForFunction(() => window.document.documentElement.dataset.device && !document.querySelector('#act').disabled);
    if (await page.locator('#product').isVisible()) await page.locator('#viewMode').click();
    const hidden=await page.evaluate(()=>{
      timeMode=currentSlot=0;elapsed=2000;aimUntil=0;
      const snapshot=seed=>{
        g.initialize(seed);g.place(0,0);g.conditions(1,1,20111);draw();
        return {hazard:g.featureAt(g.zoneX(1),g.zoneY(1)),pixels:canvas.toDataURL()};
      };
      const empty=snapshot(1),branch=snapshot(2);
      return empty.hazard===0 && branch.hazard===1 && empty.pixels===branch.pixels;
    });
    assert(hidden,'An occupied casting zone must look exactly like an empty zone before contact');
    async function castAt(kind, seed) {
      const target = await page.evaluate(([kind,seed]) => {
        g.initialize(seed); placeId=0; timeMode=currentSlot=0; g.place(0,0);
        applyWeather();g.conditions(1,1,20111);
        return [g.zoneX(kind),g.zoneY(kind)];
      }, [kind,seed]);
      const bounds = await page.locator('#scene').boundingBox();
      await page.mouse.click(bounds.x + target[0]*bounds.width, bounds.y + target[1]*bounds.height);
      await page.waitForFunction(() => g.state()===7 || g.state()===8);
      assert.equal(await page.evaluate(() => g.contact()), kind);
    }
    await castAt(1,2);
    await page.waitForFunction(() => g.releaseProgress()===1);
    await page.locator('#act').click();
    await page.waitForFunction(() => g.state()===2);
    await castAt(2,5);
    await page.locator('#act').click();
    await page.waitForFunction(() => g.releaseProgress()>0);
    await page.locator('#act').click();
    await page.waitForFunction(() => g.state()===2);
    await castAt(3,16);
    const ledger = () => page.evaluate(() => [g.catches(),g.pts(),crewScore]);
    const before = await ledger();
    for (let i=0; i<12 && await page.evaluate(() => g.state()===8); i++) {
      await page.locator('#act').click();
      await page.evaluate(() => new Promise(requestAnimationFrame));
    }
    await page.waitForFunction(() => g.state()===9);
    assert(await page.evaluate(() => $('message').textContent.includes(salvageItems[g.junkId()].name)));
    assert.deepEqual(await ledger(),before);
    await page.locator('#openMenu').click();
    await page.locator('[data-to="spots"]').click();
    await showControl(page,'#weatherChoice');await page.getByRole('button',{name:/Weather ·/}).click();
    await page.getByRole('option',{name:'Storm',exact:true}).click();
    await showControl(page,'#fishHere');await page.locator('#fishHere').click();
    assert.equal(await page.evaluate(()=>g.weather()),3);
    await page.reload();
    await page.waitForFunction(()=>typeof g?.weather==='function' && !$('act').disabled);
    assert.equal(await page.evaluate(()=>g.weather()),3);
    console.log('PASS concealed cast layouts, storm selection and weather preference restore.');
    console.log('PASS screen-targeted casts to branch, rock and debris, both on-screen release controls, localized recovery card, zero catch and event credit.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
