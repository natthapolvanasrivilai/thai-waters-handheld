const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const p=await browser.newPage({viewport:{width:1280,height:800},deviceScaleFactor:1});
  const errors=[],net=[];p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^https?:/.test(r.url()))net.push(r.url())});
  await p.goto(pathToFileURL(path.resolve(process.argv[2])).href);
  await p.waitForFunction(()=>document.documentElement.dataset.ready==='true',null,{timeout:120000});
  assert.match(await p.title(),/Assembly inspection/);
  const entries=await p.locator('#list button').count();
  assert(entries>=75);assert.equal(await p.locator('#percent').innerText(),'56%');
  if(process.argv[3])await p.screenshot({path:process.argv[3]});
  await p.locator('[data-view=wiring]').click();assert.equal(await p.locator('#percent').innerText(),'0%');
  await p.locator('#find').fill('reel SDA');await p.locator('#list button').first().click();assert.equal(await p.locator('#selected').innerText(),'Reel SDA');
  await p.locator('#isolate').click();assert.match(await p.locator('#listed').innerText(),/1 shown/);await p.locator('#clear').click();
  await p.locator('#find').fill('');await p.locator('#group').selectOption('Haptics');await p.locator('#groupOnly').click();assert.match(await p.locator('#listed').innerText(),/4 shown/);
  await p.locator('#clear').click();await p.locator('#group').selectOption('All groups');
  await p.locator('[data-view=assembled]').click();await p.locator('#haptic').uncheck();await p.locator('#rod').uncheck();
  await p.locator('#cell').selectOption('alt');await p.locator('#scope summary').click();assert.match(await p.locator('#cellResult').innerText(),/118.397/);
  await p.locator('#section').check();await p.locator('#sectionRange').fill('-5');
  await p.locator('#explode').fill('100');assert.equal(await p.locator('#percent').innerText(),'100%');
  await p.locator('#next').click();assert.match(await p.locator('#stepTitle').innerText(),/Prepare the housing/);
  for(let i=0;i<6;i++)await p.locator('#next').click();assert.equal(await p.locator('#next').isDisabled(),true);
  await p.locator('[data-view=grip]').click();await p.locator('#rod').check();
  await p.locator('#rear').click();await p.locator('#fit').click();
  await p.locator('#section').uncheck();await p.locator('[data-view=assembled]').click();await p.locator('#front').click();
  const canvas=await p.locator('#stage canvas').boundingBox();
  await p.mouse.click(canvas.x+canvas.width*.5,canvas.y+canvas.height*.30);
  assert.notEqual(await p.locator('#selected').innerText(),'Assembled product');
  await p.locator('[data-view=exploded]').click();await p.setViewportSize({width:390,height:844});
  await p.waitForTimeout(250);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.deepEqual(net,[]);assert.deepEqual(errors,[]);
  console.log('PASS offline WebGL, '+entries+' pickable entries, click, HUD, filtering, isolation, options, alternate battery, section, explode, 7 assembly stages, camera, mobile width and no remote requests.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
