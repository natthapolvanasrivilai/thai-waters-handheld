const {showControl}=require('./menu-controls.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {webkit,chromium}=require('playwright-core');
(async()=>{
 const target=process.env.PLAYTEST_URL||pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
 const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390}});
 if(process.env.PRIVATE_SITE_CHECK){const secret=fs.readFileSync(0,'utf8').trim(),origin=new URL(target).origin;await page.route('**/*',async route=>{
  if(new URL(route.request().url()).origin!==origin)return route.continue();
  const res=await page.context().request.fetch(route.request(),{headers:{...route.request().headers(),'OAI-Sites-Authorization':'Bearer '+secret},maxRedirects:0});await route.fulfill({response:res});
 });}
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(target);await page.waitForFunction(()=>g&&!$('act').disabled);
 await page.evaluate(async()=>{await Promise.all(['Syy UDT','Syy UDS','Syy Flowey'].map(f=>document.fonts.load('16px "'+f+'"','ปูน้ำจืด')));});
 const shot=async name=>{if(process.env.GALLERY_PREVIEW)await page.locator('#flatStage').screenshot({path:path.join(process.env.GALLERY_PREVIEW,name+'.png')});};
 const routes=await page.evaluate(()=>[0,1,4].map(pool=>{chooseSpot(atlas.locations.findIndex(p=>p.pool===pool),1);stopArrival();return getComputedStyle($('spot')).fontFamily;}));assert.equal(new Set(routes).size,3);
 await page.evaluate(()=>{chooseSpot(1,2,2);stopArrival();g.setBait(13);g.restoreCatch(40,18);pendingCapture=captureLanding();save();draw();});
 const captured=await page.evaluate(()=>pendingCapture);
 await page.reload();await page.waitForFunction(()=>g?.state()===5&&!$('catchContinue').hidden);
 const pos=await page.evaluate(()=>{const ui=$('lcdUI'),before=ui.style.transform;ui.style.transform='none';const gap=ui.getBoundingClientRect().right-$('lcdPower').getBoundingClientRect().right;ui.style.transform=before;return gap;});assert(pos>=0&&pos<10);
 await shot('Thai-Waters-catch-screen');
 await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.waitForFunction(()=>g?.state()===5);assert.equal(await page.evaluate(()=>catchPromptOpacity(900)),1);await page.emulateMedia({reducedMotion:'no-preference'});await page.reload();await page.waitForFunction(()=>g?.state()===5);assert(await page.evaluate(()=>catchPromptOpacity(900)<0.5));
 await page.locator('#catchContinue').tap();await page.waitForFunction(()=>g.state()===0);
 await page.reload();await page.waitForFunction(()=>g&&!$('act').disabled);
 assert.deepEqual(await page.evaluate(()=>catchHistory),[captured]);
 await page.locator('#openMenu').tap();await page.locator('[data-to=book]').tap();await page.waitForFunction(()=>$('records').children.length===8);
 assert.equal(await page.locator('#menu').evaluate(m=>m.offsetWidth),480);assert.equal(await page.locator('#menu').evaluate(m=>m.offsetHeight),320);
 const touch=process.env.TEST_WEBKIT?null:await page.context().newCDPSession(page);
 async function swipe(selector,dx,dy=0){
  const box=await page.locator(selector).boundingBox();assert(box,selector);
  const x=Math.round(box.x+box.width/2),y=Math.round(box.y+Math.min(50,box.height/2));
  if(touch){
   await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
   for(let i=1;i<=5;i++)await touch.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+Math.round(dx*i/5),y:y+Math.round(dy*i/5)}]});
   await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  }else{
   await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+dx,y+dy,{steps:5});await page.mouse.up();
  }
 }
 await swipe('#records',-82);await page.waitForFunction(()=>bookOffset===1&&bookSpecies===null);
 await swipe('#records',82);await page.waitForFunction(()=>bookOffset===0&&bookSpecies===null);
 await swipe('#records',82);assert.equal(await page.evaluate(()=>bookOffset),0); // no wrap; no tile activation
 await swipe('#records',7,54);assert.deepEqual(await page.evaluate(()=>[bookOffset,bookSpecies]),[0,null]);
 const unknown=page.locator('#species-0');
 assert.equal(await unknown.locator('b').count(),0);assert.equal((await unknown.innerText()).trim(),'');
 await unknown.tap();assert(!await page.locator('#bookDetail').innerText().then(s=>s.includes('Climbing perch')||s.includes('ปลาหมอไทย')));
 await swipe('#bookDetail',-82);await page.waitForFunction(()=>bookSpecies===1);
 await swipe('#bookDetail',82);await page.waitForFunction(()=>bookSpecies===0);
 await page.locator('#back').tap();
 assert(await unknown.locator('canvas').evaluate(c=>{const b=c.getContext('2d').getImageData(0,0,c.width,c.height).data,colors=new Set();for(let i=0;i<b.length;i+=4)if(b[i+3]===255)colors.add(b.slice(i,i+3).join(','));return colors.size===1;}));
 for(let i=0;i<Math.floor(40/8);i++)await page.locator('#bookNext').tap();
 assert(await page.locator('#species-40 b').isVisible());assert.equal(await page.locator('#species-41 b').count(),0);
 await shot('Thai-Waters-collection');await page.locator('#bookSearch').fill('prawn');await page.locator('#species-40').tap();
 const row=page.locator('.catch-log');assert.equal(await row.count(),1);assert.equal(await row.locator('svg').count(),8);assert.match(await row.innerText(),/18/);
 await shot('Thai-Waters-catch-history');await page.locator('#back').tap();assert(await page.locator('#species-40').isVisible());
 await page.locator('#back').tap();await page.locator('[data-to=sensors]').tap();await showControl(page,'#handheldEnable');await page.locator('#handheldEnable').check();await page.keyboard.press('v');await page.locator('#resume').tap();await page.keyboard.press('c');await page.waitForFunction(()=>g.state()===1||g.state()===2);
 assert.deepEqual(errors,[]);console.log('PASS three Thai location typefaces, 480×320 gallery, confirmed catch across reload, eight history fields, full-width HUD, reduced-motion prompt, and controller cast.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
