const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium,webkit}=require('playwright-core');

(async()=>{
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({
  executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
 });
 const file=path.join(__dirname,'../../game/Thai-Waters-play.html');
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(file));});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:'+server.address().port);
  await page.waitForFunction(()=>typeof g!=='undefined'&&g&&!document.querySelector('#act').disabled);
  assert.equal(await page.locator('html').getAttribute('lang'),'th');
  assert.equal(await page.locator('#openMenu').textContent(),'เมนู');
  await page.evaluate(()=>document.fonts.load('600 16px "Atkinson Hyperlegible Next"','กุ้ง'));
  assert(await page.evaluate(()=>atlas.locations.length===117&&atlas.locations.every(p=>/[ก-๙]/.test(p.name)&&/[ก-๙]/.test(p.story))));
  assert(await page.evaluate(()=>atlas.fish.slice(0,60).every(f=>/[ก-๙]/.test(f.name)&&/[ก-๙]/.test(f.lore))));
  await page.locator('#openMenu').tap();await page.locator('[data-to=rod]').tap();
  await page.locator('#hookBait + button').tap();
  assert.equal(await page.locator('.bait-option canvas').count(),6);
  const fingerprints=await page.locator('.bait-option canvas').evaluateAll(list=>list.map(c=>c.toDataURL()));
  assert.equal(new Set(fingerprints).size,6);
  if(process.env.BAIT_PREVIEW)await page.waitForTimeout(450);
  if(process.env.BAIT_PREVIEW)await page.locator('#flatStage').screenshot({path:process.env.BAIT_PREVIEW});
  await page.locator('.bait-option').nth(1).tap();
  assert.equal(await page.locator('#hookBait').evaluate(s=>s.selectedIndex),1);
  assert.match(await page.locator('#baitNote').textContent(),/[ก-๙]/);
  await page.locator('#back').tap();await page.locator('[data-language=en]').tap();
  assert.equal(await page.locator('#menuTitle').textContent(),'Tackle box');
  await page.reload();await page.waitForFunction(()=>g&&!$('act').disabled);
  assert.equal(await page.locator('html').getAttribute('lang'),'en');
  await page.locator('#openMenu').tap();await page.locator('[data-language=th]').tap();await page.locator('#resume').tap();
  await page.evaluate(()=>{g.restoreCatch(1,12);pendingDay=0;save();draw();});
  await page.waitForFunction(()=>!$('catchContinue').hidden);
  assert.equal(await page.locator('#catchContinue').getAttribute('aria-label'),'แตะเพื่อไปต่อ');
  assert.equal(await page.locator('#act').isVisible(),false);
  await page.waitForTimeout(1200);
  assert.equal(await page.evaluate(()=>g.caught(1)),0);
  await page.reload();await page.waitForFunction(()=>g&&g.state()===5&&!$('catchContinue').hidden);
  if(process.env.CATCH_PREVIEW)await page.locator('#flatStage').screenshot({path:process.env.CATCH_PREVIEW});
  await page.locator('#catchContinue').tap({position:{x:24,y:50}});
  await page.waitForFunction(()=>g.caught(1)===1&&g.state()===0);
  assert.equal(await page.locator('#menu').evaluate(m=>m.open),false);
  await page.reload();await page.waitForFunction(()=>g&&!$('act').disabled);
  assert.equal(await page.evaluate(()=>g.caught(1)),1);
  assert.equal(await page.evaluate(()=>g.baitChoice()%6),1);
  assert.deepEqual(errors,[]);
  console.log('PASS Thai default, English switch and persistence, six distinct bait sprites, retained selection, held catch across reload, one-tap journal transfer and return to fishing.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
