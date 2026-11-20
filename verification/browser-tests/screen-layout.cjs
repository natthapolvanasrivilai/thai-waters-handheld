const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const {chromium} = require('playwright-core');

const entry = process.env.PLAYTEST_URL || pathToFileURL(path.resolve(
  process.env.PLAYTEST_HTML || path.join(__dirname, '..', '..', 'game', 'Thai-Waters-play.html'))).href;

async function verify(browser, width, height, touch, {testDevice = false, noWebGL = false} = {}) {
  const page = await browser.newPage({viewport: {width,height}, isMobile: touch, hasTouch: touch});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    await page.addInitScript(({noWebGL}) => {
      localStorage.setItem('thai-waters-language', 'th');
      if (noWebGL) {
        const getContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...options) {
          return /^webgl/.test(type) ? null : getContext.call(this,type,...options);
        };
      }
    }, {noWebGL});
    await page.goto(entry);
    await page.waitForFunction(() => window.document.documentElement.dataset.device === 'deferred');
    assert.equal(await page.locator('html').getAttribute('data-view'),'screen');
    assert.equal(await page.locator('#product canvas').count(),0,'3D has not started before opt-in');
    await page.waitForFunction(() => g && typeof g.state === 'function');
    const contained = async id => {
      const b = await page.locator(id).boundingBox();
      assert.ok(b && b.width > 0 && b.height > 0, id+' is visible');
      assert.ok(b.x>=-1 && b.y>=-1 && b.x+b.width<=width+1 && b.y+b.height<=height+1,
        id+' fits within the viewport: '+JSON.stringify(b));
      return b;
    };
    const b=await contained('#flatStage');
    assert.ok(Math.abs(b.width/b.height-1.5)<0.02,'LCD fits at its native aspect ratio');
    await contained('#dial'); await contained('#viewMode'); await contained('#simPower');
    if (touch) {
      const shell=await contained('main');
      assert.ok(Math.abs(shell.height-height)<=1,'phone fills the CSS viewport in either orientation');
      assert.equal(await page.evaluate(()=>!!document.fullscreenElement),false,'no automatic native fullscreen');
      const target=await contained('#mobileFullscreen');
      assert.ok(target.height>=44 && target.width>=44,'fullscreen touch target is at least 44 CSS pixels');
      await contained('#motionShortcut');
      await page.locator('#motionShortcut').click();
      assert.equal(await page.locator('#menu').getAttribute('data-page'),'sensors','motion setup is one tap away');
      await contained('#enableMotion');
      await page.locator('#resume').click();
    }
    await page.locator('#openMenu').click();
    assert.equal(await page.locator('#menu').getAttribute('open'),'');
    assert.match(await page.locator('#menuTitle').textContent(),/[ก-๙]/);
    await contained('#menu');
    await page.locator('[data-to=spots]').click();
    await page.locator('#back').click();
    await page.locator('#resume').click();
    assert.equal(await page.locator('#menu').getAttribute('open'),null);
    if (testDevice || noWebGL) {
      const state=await page.evaluate(() => g.state());
      await page.locator('#viewMode').click();
      await page.waitForFunction(expected=>document.documentElement.dataset.device===expected,
        noWebGL?'fallback':'ready');
      if (!noWebGL) {
        assert.equal(await page.locator('html').getAttribute('data-view'),'device');
        await contained('#viewMode');await contained('#foldButton');await contained('#gripButton');
        await page.locator('#viewMode').click();
      }
      assert.equal(await page.locator('html').getAttribute('data-view'),'screen');
      await contained('#flatStage');
      assert.equal(await page.evaluate(() => g.state()),state,'View change preserves game state');
    }
    assert.deepEqual(errors,[]);
    console.log('PASS',width+'×'+height,touch?'touch':'mouse',noWebGL?'WebGL fallback':testDevice?'3D round trip':'Thai flat menu');
  } finally {await page.close();}
}

(async()=>{
  const browser=await chromium.launch({
    executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless:true,
    args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']
  });
  try {
    await verify(browser,1099,713,false,{testDevice:true});
    await verify(browser,390,844,true);
    await verify(browser,844,390,true,{testDevice:true});
    await verify(browser,1099,713,false,{noWebGL:true});
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
