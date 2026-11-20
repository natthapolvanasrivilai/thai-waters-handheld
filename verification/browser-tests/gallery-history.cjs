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
 async function tapBookButton(selector){
  const button=page.locator(selector);
  if(!touch){await button.tap();return;}
  await button.scrollIntoViewIfNeeded();
  const b=await button.boundingBox();assert(b,selector);
  const x=Math.round(b.x+b.width/2),y=Math.round(b.y+b.height/2);
  assert.equal(await page.evaluate(({x,y})=>document.elementFromPoint(x,y)?.closest('button')?.id,{x,y}),selector.slice(1),
   'Physical button center must be hittable: '+selector);
  await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
  // Give Chromium one ordinary contact interval rather than a zero-duration tap.
  await new Promise(resolve=>setTimeout(resolve,65));
  await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 }
 async function expectBackAfter(label){
  await page.evaluate(()=>{window.galleryBackTrace=[];});
  assert.deepEqual(await page.evaluate(()=>[menuPage,bookSpecies]),['book',0]);
  await tapBookButton('#back');
  await page.waitForFunction(()=>menuPage==='book'&&bookSpecies===null&&$('bookDetail').hidden,undefined,{timeout:2500}).catch(()=>{});
  const result=await page.evaluate(()=>({menuPage,bookSpecies,detailHidden:$('bookDetail').hidden,
   touchAction:getComputedStyle($('back')).touchAction,viewportScale:window.visualViewport?.scale,backTrace:galleryBackTrace}));
  assert(result.menuPage==='book'&&result.bookSpecies===null&&result.detailHidden,
   `Back must close only the detail (${label}): `+JSON.stringify(result));
 }
 await page.evaluate(()=>{
  window.galleryBackTrace=[];
  for(const t of ['touchstart','touchend','touchcancel','pointerdown','pointerup','pointercancel','mousedown','mouseup','click']){
   window.addEventListener(t,e=>{
    const point=e.changedTouches?.[0]??e;
    const x=point.clientX,y=point.clientY,target=e.target.closest?.('button,article,[data-section]')?.id||e.target.nodeName;
    const hit=Number.isFinite(x)&&Number.isFinite(y)?document.elementFromPoint(x,y)?.closest('button,article,[data-section]')?.id:null;
    if(target!=='back'&&hit!=='back')return;
    const record={t,target,hit,pointerType:e.pointerType,primary:e.isPrimary,trusted:e.isTrusted,x,y};
    galleryBackTrace.push(record);
    queueMicrotask(()=>{record.prevented=e.defaultPrevented;record.after=[menuPage,bookSpecies];});
   },{capture:true});
  }
 });
 await tapBookButton('#species-0');await page.waitForFunction(()=>bookSpecies===0);
 await expectBackAfter('before any swipe');
 await swipe('#records',-82);await page.waitForFunction(()=>bookOffset===1&&bookSpecies===null);
 await swipe('#records',82);await page.waitForFunction(()=>bookOffset===0&&bookSpecies===null);
 await swipe('#records',82);assert.equal(await page.evaluate(()=>bookOffset),0); // no wrap; no tile activation
 await swipe('#records',7,54);assert.deepEqual(await page.evaluate(()=>[bookOffset,bookSpecies]),[0,null]);
 const unknown=page.locator('#species-0');
 assert.equal(await unknown.locator('b').count(),0);assert.equal((await unknown.innerText()).trim(),'');
 await tapBookButton('#species-0');await page.waitForFunction(()=>bookSpecies===0);assert(!await page.locator('#bookDetail').innerText().then(s=>s.includes('Climbing perch')||s.includes('ปลาหมอไทย')));
 await swipe('#bookDetail',-82);await page.waitForFunction(()=>bookSpecies===1);
 await swipe('#bookDetail',82);await page.waitForFunction(()=>bookSpecies===0);
 await expectBackAfter('immediately after two detail swipes');
 assert(await unknown.locator('canvas').evaluate(c=>{const b=c.getContext('2d').getImageData(0,0,c.width,c.height).data,colors=new Set();for(let i=0;i<b.length;i+=4)if(b[i+3]===255)colors.add(b.slice(i,i+3).join(','));return colors.size===1;}));
 for(let i=0;i<Math.floor(40/8);i++){
  assert(await page.locator('#bookNext').isVisible(),'Next missing before page '+(i+2)+': '+JSON.stringify(await page.evaluate(()=>({menuPage,bookSpecies,bookOffset}))));
  await tapBookButton('#bookNext');
  await page.waitForFunction(i=>menuPage==='book'&&bookSpecies===null&&bookOffset===i,i+1,{timeout:1500}).catch(()=>{});
  assert.deepEqual(await page.evaluate(()=>[menuPage,bookSpecies,bookOffset]),['book',null,i+1],'Next tap did not advance page '+(i+2));
 }
 assert(await page.locator('#species-40 b').isVisible());assert.equal(await page.locator('#species-41 b').count(),0);
 await shot('Thai-Waters-collection');await page.locator('#bookSearch').fill('prawn');await page.locator('#species-40').tap();
 const row=page.locator('.catch-log');assert.equal(await row.count(),1);assert.equal(await row.locator('svg').count(),8);assert.match(await row.innerText(),/18/);
 await shot('Thai-Waters-catch-history');await page.locator('#back').tap();assert(await page.locator('#species-40').isVisible());
 await page.locator('#back').tap();await page.locator('[data-to=sensors]').tap();await showControl(page,'#handheldEnable');await page.locator('#handheldEnable').check();await page.keyboard.press('v');await page.locator('#resume').tap();await page.keyboard.press('c');await page.waitForFunction(()=>g.state()===1||g.state()===2);
 assert.deepEqual(errors,[]);console.log('PASS three Thai location typefaces, 480×320 gallery, confirmed catch across reload, eight history fields, full-width HUD, reduced-motion prompt, and controller cast.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
