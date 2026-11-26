const {chromium}=require('playwright-core');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
(async()=>{
 const [file,evidence,preview]=process.argv.slice(2);
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1450,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve(file)).href);
  await page.locator('html[data-ready=true]').waitFor({timeout:90000});
  const read=()=>page.locator('#dist').textContent();
  assert.equal(await read(),'0.00 mm');
  const cross0=await page.locator('#polys').innerHTML();
  await page.locator('[data-at="260"]').click();
  assert.equal(await read(),'0.00 mm');
  assert.notEqual(await page.locator('#polys').innerHTML(),cross0);
  await page.locator('#closeup').click();
  await page.locator('[data-at="1000"]').click();
  assert.equal(await read(),'8.25 mm');
  await page.locator('#display').check();
  assert.match(await page.locator('#w4').textContent(),/Display boards seated/);
  await page.locator('#display').uncheck();
  await page.locator('#context').uncheck();await page.locator('#context').check();
  await page.locator('#fit').click();
  await page.screenshot({path:preview});
  await page.locator('[data-at="0"]').click();
  await page.locator('#play').click();await page.waitForTimeout(1000);
  assert.notEqual(await page.locator('html').getAttribute('data-motion'),'0');
  await page.locator('#play').click();
  await page.locator('#motion').focus();
  await page.keyboard.press('End');assert.equal(await read(),'8.25 mm');
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.locator('[data-at="0"]').click();assert.equal(await read(),'0.00 mm');
  assert.deepEqual(errors,[]);
  fs.writeFileSync(evidence,JSON.stringify({browser:browser.version(),tested:['seated','actuate without translation','withdraw','seated display overlay','board context','fit and close-up cameras','animation and pause','keyboard','390-pixel mobile layout'],browser_errors:errors},null,2)+'\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

