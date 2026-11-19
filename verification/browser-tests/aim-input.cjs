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
    await page.goto(pathToFileURL(path.resolve(__dirname, '../../game/Thai-Waters-play.html')).href);
    await page.waitForFunction(() => window.document.documentElement.dataset.device && !document.querySelector('#act').disabled);
    if (await page.locator('#product').isVisible()) await page.locator('#viewMode').click();
    async function castAt(kind, seed) {
      const target = await page.evaluate(([kind,seed]) => {
        g.initialize(seed); placeId=0; timeMode=currentSlot=0; g.place(0,0);
        return [g.zoneX(kind),g.zoneY(kind)];
      }, [kind,seed]);
      const bounds = await page.locator('#scene').boundingBox();
      await page.mouse.click(bounds.x + target[0]*bounds.width, bounds.y + target[1]*bounds.height);
      await page.waitForFunction(() => g.state()===7 || g.state()===8);
      assert.equal(await page.evaluate(() => g.contact()), kind);
    }
    await castAt(1,1);
    await page.waitForFunction(() => g.releaseProgress()===1);
    await page.locator('#act').click();
    await page.waitForFunction(() => g.state()===2);
    await castAt(2,1);
    await page.locator('#act').click();
    await page.waitForFunction(() => g.releaseProgress()>0);
    await page.locator('#act').click();
    await page.waitForFunction(() => g.state()===2);
    await castAt(3,9);
    const ledger = () => page.evaluate(() => [g.catches(),g.pts(),crewScore]);
    const before = await ledger();
    for (let i=0; i<12 && await page.evaluate(() => g.state()===8); i++) {
      await page.locator('#act').click();
      await page.evaluate(() => new Promise(requestAnimationFrame));
    }
    await page.waitForFunction(() => g.state()===9);
    assert.equal(await page.evaluate(() => g.junkId()),0);
    assert.deepEqual(await ledger(),before);
    console.log('PASS screen-targeted casts to branch, rock and debris, both on-screen release controls, recovered sandal, zero catch and event credit.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
