const assert = require('node:assert/strict');
const path = require('node:path');
const {chromium, webkit} = require('playwright-core');

(async () => {
  const browser = process.env.TEST_WEBKIT === '1'
    ? await webkit.launch()
    : await chromium.launch({executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  try {
    const page = await browser.newPage({isMobile:true, hasTouch:true, viewport:{width:390,height:844}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    // The hosted event instructions run only on this origin. Supply the release
    // locally so this startup regression runs without a network or owner login.
    const url = 'https://thai-waters-pocket-angler.shoung0690.chatgpt.site/';
    await page.route(url, route => route.fulfill({path:path.resolve(__dirname,'../../game/Thai-Waters-play.html'),contentType:'text/html'}));
    await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await page.goto(url);
    await page.waitForFunction(() => !document.getElementById('act').disabled);
    await page.locator('#act').tap();
    await page.waitForFunction(() => g.state() !== 0);
    await page.locator('#openMenu').tap();
    await page.locator('[data-to=crew]').tap();
    await require('./menu-controls.cjs').showControl(page,'#crewHelp');
    assert.match(await page.locator('#crewHelp').first().innerText(), /private playtest/);
    assert.deepEqual(errors, []);
    console.log('PASS hosted-origin mobile startup, cast and shared-event menu.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
