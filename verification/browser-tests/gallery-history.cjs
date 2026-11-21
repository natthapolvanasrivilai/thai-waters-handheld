const {requireBootHome}=require('./boot-home-check.cjs');
const {showControl}=require('./menu-controls.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {openPersistenceEntry}=require('./persistence-entry.cjs');
const {webkit,chromium}=require('playwright-core');

// Keep the deterministic local fixture out of authenticated external playtests.
async function assertRayongLanding(browser,target){
 const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390},reducedMotion:'reduce',serviceWorkers:'block'});
 try{
  await page.route('**/*',route=>{
   const url=route.request().url();
   return url===target||url.startsWith('data:')||url.startsWith('blob:')?route.continue():route.abort();
  });
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const tap=s=>page.locator(s).tap(), ready=()=>page.waitForFunction(()=>g?.state()===0&&!$('act').disabled,undefined,{timeout:10000});
  await page.goto(target);await (await requireBootHome(page)).tap();await ready();
  assert.equal(await page.locator('html').getAttribute('lang'),'th');
  assert.deepEqual(await page.evaluate(()=>{const x=atlas.fish[1433];return [x.art,x.key,x.name,x.scientificName,x.thaiNameKind,x.thaiSearchAliases,x.measure];}),[1433,5215810,'ปลากระเบนทอง','Taeniura lymma','species',['ปลากระเบนหางพัดจุดฟ้า'],'ความกว้างลำตัว']);
  assert.equal(await page.evaluate(()=>{$('bookSearch').value='ปลากระเบนหางพัดจุดฟ้า';const found=bookMatches().includes(1433);$('bookSearch').value='';return found;}),false);
  // Seed the normal Rayong cast, bite and bottom-holding fight; do not restore
  // a catch or write a receipt. The real frame performs the landing transition.
  const trace=await page.evaluate(()=>{
   chooseSpot(98,1,1);stopArrival();g.initialize(25);g.place(98,1);g.conditions(1,11,20779);g.setTechnique(0);if(!g.setBait(17))throw Error('bait');g.setAim(.5,.67);
   g.advance(16,1,0,0);const encounter=[g.state(),g.species(),g.lengthCm()];g.advance(900,0,0,0);
   for(let i=0;i<1000&&g.state()===2;i++)g.advance(16,0,0,0);
   if(g.state()!==3)throw Error('no seeded bite');g.advance(16,0,1,0);const style=g.fightStyle();let planted=0;
   for(let i=0;i<472;i++){if(g.state()!==4)throw Error('fight ended early');const bottom=!!g.holdingBottom();if(bottom)planted+=16;g.advance(16,0,bottom?1:0,g.fightBeat()===1||bottom?0:.014);}
   if(g.state()!==4||g.holdingBottom()||g.fightBeat()===1)throw Error('final seed step changed');
   const request=window.requestAnimationFrame;try{window.requestAnimationFrame=()=>0;turns=.014;frame(prev+16);}finally{window.requestAnimationFrame=request;}
   return {encounter,style,planted,state:g.state(),capture:pendingCapture};
  });
  assert.deepEqual(trace.encounter,[1,1433,27]);assert.equal(trace.style,2);assert.equal(trace.planted,960);assert.equal(trace.state,5);
  const cap=trace.capture;assert.equal(cap.id,1433);assert.equal(cap.cm,27);assert.equal(cap.place,98);assert.match(cap.uid,/^[a-f0-9]{32}$/i);
  assert.equal(cap.bait,17);assert(Number.isSafeInteger(cap.grams)&&cap.grams>=0);
  const measurement=await page.evaluate(()=>readEngineText(g.measurement(g.species(),g.lengthCm())));
  assert.equal(measurement,'Disc width');
  await page.locator('#catchContinue').waitFor({state:'visible'});assert.equal(await page.locator('#message').textContent(),'ปลากระเบนทอง');
  const saved=()=>page.evaluate(()=>{const s=JSON.parse(localStorage.getItem('thai-atlas-v2'));return {stored:s?.book?.[1433],pending:s?.pendingCapture,history:s?.history,active:g.caught(1433),place:placeId};});
  assert.deepEqual(await saved(),{stored:[0,0],pending:cap,history:[],active:0,place:98});
  await page.evaluate(()=>{$('catchContinue').addEventListener('click',e=>document.body.dataset.rayongTrusted=String(e.isTrusted),{once:true});});
  await tap('#catchContinue');assert.equal(await page.locator('body').getAttribute('data-rayong-trusted'),'true');await ready();assert.deepEqual(await saved(),{stored:[1,27],pending:null,history:[cap],active:1,place:98});
  const verifyCollection=async()=>{
   await tap('#openMenu');await tap('[data-section=home] [data-to=book]');
   for(const q of ['ปลากระเบนทอง','ปลากระเบนหางพัดจุดฟ้า','Taeniura lymma']){
    await tap('#bookFind');await page.locator('#bookSearch').fill(q);await tap('#bookFindDone');await page.locator('#species-1433').waitFor({state:'visible'});
    assert.deepEqual(await page.evaluate(()=>bookMatches()),[1433],q);
   }
   await tap('#species-1433');assert.equal(await page.locator('#bookDetail h2').textContent(),'ปลากระเบนทอง');assert.match(await page.locator('#bookDetail').textContent(),/Taeniura lymma/u);
  };
  await verifyCollection();await page.reload();const resume=await requireBootHome(page);
  assert.deepEqual(await saved(),{stored:[1,27],pending:null,history:[cap],active:1,place:98});
  await resume.tap();await ready();await verifyCollection();assert.deepEqual(errors,[]);
  console.log('PASS seeded Rayong disc-width landing, one trusted Continue, and exact catch UID across Thai Collection and reload');
 }finally{await page.close();}
}

(async()=>{
 const html=path.resolve(__dirname,'../../game/Thai-Waters-play.html');
 const directPortrait=process.env.PLAYTEST_URL||pathToFileURL(html).href;
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 let entry;
 try{
 entry=await openPersistenceEntry(html,process.env.PLAYTEST_URL);
 const target=entry.url;
 const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390}});
 if(process.env.PRIVATE_SITE_CHECK){const secret=fs.readFileSync(0,'utf8').trim(),origin=new URL(target).origin;await page.route('**/*',async route=>{
  if(new URL(route.request().url()).origin!==origin)return route.continue();
  const res=await page.context().request.fetch(route.request(),{headers:{...route.request().headers(),'OAI-Sites-Authorization':'Bearer '+secret},maxRedirects:0});await route.fulfill({response:res});
 });}
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(target);
 await (await requireBootHome(page)).tap();
 await page.waitForFunction(()=>g&&!$('act').disabled);
 await page.evaluate(async()=>{await Promise.all(['Syy UDT','Syy UDS','Syy Flowey'].map(f=>document.fonts.load('16px "'+f+'"','ปูน้ำจืด')));});
 const shot=async name=>{if(process.env.GALLERY_PREVIEW)await page.locator('#flatStage').screenshot({path:path.join(process.env.GALLERY_PREVIEW,name+'.png')});};
 const routes=await page.evaluate(()=>[0,1,4].map(pool=>{chooseSpot(atlas.locations.findIndex(p=>p.pool===pool),1);stopArrival();return getComputedStyle($('spot')).fontFamily;}));assert.equal(new Set(routes).size,3);
 await page.evaluate(()=>{chooseSpot(1,2,2);stopArrival();g.setBait(13);g.restoreCatch(40,18);pendingCapture=captureLanding();save();draw();});
 const captured=await page.evaluate(()=>pendingCapture);
 const resumeHeld=async()=>{
  const resume=await requireBootHome(page);
  assert.deepEqual(await page.evaluate(()=>({phase:g.state(),filed:!!g.filed(),pending:pendingCapture})),
   {phase:5,filed:false,pending:captured},'No catch or exact capture metadata may be lost or filed at Home');
  await resume.tap();
 };
 await page.reload();await resumeHeld();await page.waitForFunction(()=>g?.state()===5&&!$('catchContinue').hidden);
 const pos=await page.evaluate(()=>{const ui=$('lcdUI'),before=ui.style.transform;ui.style.transform='none';const gap=ui.getBoundingClientRect().right-$('lcdPower').getBoundingClientRect().right;ui.style.transform=before;return gap;});assert(pos>=0&&pos<10);
 await shot('Thai-Waters-catch-screen');
 const portrait=await browser.newPage({isMobile:true,hasTouch:true,deviceScaleFactor:1,viewport:{width:320,height:700}});
 if(!process.env.PRIVATE_SITE_CHECK){
  await portrait.goto(directPortrait);
  await (await requireBootHome(portrait)).tap();
  await portrait.waitForFunction(()=>g&&!$('act').disabled);
  await portrait.evaluate(()=>{for(let i=0;i<8;i++)g.restoreEntry(i,1,atlas.fish[i].low);});
  await portrait.locator('#openMenu').tap();await portrait.locator('[data-section=home] [data-to=book]').tap();
  const fit=await portrait.evaluate(()=>{
   const rect=$('menu').getBoundingClientRect();
   const tiles=[...$('records').children],targets=[...tiles,$('bookFind'),$('bookNext'),$('fishCredits')];
   return {touch:parseInt(getComputedStyle($('lcdUI')).getPropertyValue('--touch')),count:tiles.length,
    noOverflow:$('records').scrollHeight<=$('records').clientHeight,
    fitted:targets.every(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.top>=rect.top-1&&r.bottom<=rect.bottom+1&&r.left>=rect.left-1&&r.right<=rect.right+1;}),
    labelFit:tiles.every(e=>[...e.querySelectorAll('b,small')].every(label=>{const b=label.getBoundingClientRect(),r=e.getBoundingClientRect();return b.height>0&&b.top>=r.top&&b.bottom<=r.bottom;}))};
  });
  if(process.env.COLLECTION_PREVIEW)await portrait.locator('#flatStage').screenshot({path:process.env.COLLECTION_PREVIEW});
  await portrait.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const native=Buffer.from(await portrait.locator('#scene').evaluate(c=>c.toDataURL('image/png').split(',')[1]),'base64');
  assert.equal(native.readUInt32BE(16),480);assert.equal(native.readUInt32BE(20),320);
  if(process.env.COLLECTION_PREVIEW)fs.writeFileSync(path.join(path.dirname(process.env.COLLECTION_PREVIEW),'collection-native-480x320.png'),native);
  assert.equal(fit.touch,74,'Small portrait activates the largest LCD touch targets');
  assert.deepEqual(fit,{touch:74,count:8,noOverflow:true,fitted:true,labelFit:true},'Eight readable touch cards and controls fit the narrow phone');
 }
 await portrait.close();
 await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await resumeHeld();await page.waitForFunction(()=>g?.state()===5);assert.equal(await page.evaluate(()=>catchPromptOpacity(900)),1);await page.emulateMedia({reducedMotion:'no-preference'});await page.reload();await resumeHeld();await page.waitForFunction(()=>g?.state()===5);assert(await page.evaluate(()=>catchPromptOpacity(900)<0.5));
 await page.locator('#catchContinue').tap();await page.waitForFunction(()=>g.state()===0);
 await page.reload();
 const resumeFiled=await requireBootHome(page);
 assert.deepEqual(await page.evaluate(()=>catchHistory),[captured],'Filed record must be restored before Resume');
 await resumeFiled.tap();
 await page.waitForFunction(()=>g&&!$('act').disabled);
 assert.deepEqual(await page.evaluate(()=>catchHistory),[captured]);
 await page.locator('#openMenu').tap();await page.locator('[data-section=home] [data-to=book]').tap();await page.waitForFunction(()=>$('records').children.length===8);
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
 // The trusted menu taps unlock the real mixer. Keep it running while observing only page cues.
 await page.waitForFunction(()=>audio?.state==='running',undefined,{timeout:5000});
 await page.evaluate(()=>{
  window.galleryPageCues=[];
  window.gallerySoundBefore={pluck,fx:$('fx').selectedIndex,cue:$('cue').selectedIndex};
  pluck=(freq,when,duration,gain)=>{
   if(freq===340&&duration===.068)galleryPageCues.push({freq,duration,gain});
   return gallerySoundBefore.pluck(freq,when,duration,gain);
  };
  $('fx').selectedIndex=2;
 });
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
 const sounds=await page.evaluate(()=>galleryPageCues.slice());
 assert.equal(sounds.length,2,'Only actual list flips sound; boundaries, pans, details and Back remain silent');
 assert.deepEqual(sounds,[{freq:340,duration:.068,gain:.062},{freq:340,duration:.068,gain:.062}],
  'Both actual swipes use the exact short SFX at Normal effects volume');
 await page.evaluate(()=>$('fx').selectedIndex=0);
 await swipe('#records',-82);await page.waitForFunction(()=>bookOffset===1&&bookSpecies===null);
 await swipe('#records',82);await page.waitForFunction(()=>bookOffset===0&&bookSpecies===null);
 assert.equal(await page.evaluate(()=>galleryPageCues.length),2,'Muted page changes must stay silent');
 await page.evaluate(()=>{$('fx').selectedIndex=1;$('cue').selectedIndex=1;});
 await page.evaluate(()=>{
  window.galleryPagerTrace=[];
  for(const kind of ['pointerdown','pointerup','pointercancel','lostpointercapture','touchend','click']){
   window.addEventListener(kind,e=>{
    const target=e.target.closest?.('button')?.id;
    if(!['bookPrev','bookNext'].includes(target)||galleryPagerTrace.length>=24)return;
    const row={kind,target,phase:e.pointerType||null,trust:e.isTrusted,page:bookOffset};
    galleryPagerTrace.push(row);
    queueMicrotask(()=>{row.prevented=e.defaultPrevented;row.next=bookOffset;});
   },true);
  }
 });
 async function expectPager(selector,target){
  await tapBookButton(selector);
  await page.waitForFunction(n=>bookOffset===n,target,{timeout:2500}).catch(()=>{});
  const trace=await page.evaluate(()=>({page:bookOffset,events:galleryPagerTrace.slice()}));
  assert.equal(trace.page,target,'Immediate native touch on '+selector+' must turn one page: '+JSON.stringify(trace));
 }
 await expectPager('#bookNext',1);await expectPager('#bookPrev',0);
 assert.deepEqual(await page.evaluate(()=>galleryPageCues.slice(2).map(n=>n.gain)),[.033,.033],
  'Both arrow taps use Low effects volume even in bite-only Light mode');
 await page.locator('#bookNext').click();await page.waitForFunction(()=>bookOffset===1);
 await page.locator('#bookPrev').press('Enter');await page.waitForFunction(()=>bookOffset===0);
 assert.deepEqual(await page.evaluate(()=>galleryPageCues.slice(4).map(n=>n.gain)),[.033,.033],
  'Ordinary mouse and keyboard actions still move one page and sound once');
 await page.evaluate(()=>{
  pluck=gallerySoundBefore.pluck;$('fx').selectedIndex=gallerySoundBefore.fx;$('cue').selectedIndex=gallerySoundBefore.cue;
 });


 assert(await unknown.locator('canvas').evaluate(c=>{const b=c.getContext('2d').getImageData(0,0,c.width,c.height).data,colors=new Set();for(let i=0;i<b.length;i+=4)if(b[i+3]===255)colors.add(b.slice(i,i+3).join(','));return colors.size===1;}));
 for(let i=0;i<Math.floor(40/8);i++){
  assert(await page.locator('#bookNext').isVisible(),'Next missing before page '+(i+2)+': '+JSON.stringify(await page.evaluate(()=>({menuPage,bookSpecies,bookOffset}))));
  await tapBookButton('#bookNext');
  await page.waitForFunction(i=>menuPage==='book'&&bookSpecies===null&&bookOffset===i,i+1,{timeout:1500}).catch(()=>{});
  assert.deepEqual(await page.evaluate(()=>[menuPage,bookSpecies,bookOffset]),['book',null,i+1],'Next tap did not advance page '+(i+2));
 }
 assert(await page.locator('#species-40 b').isVisible());assert.equal(await page.locator('#species-41 b').count(),0);
 await shot('Thai-Waters-collection');
 assert(await page.locator('#bookSearch').isHidden(),'Search does not occupy the fish grid');
 await page.locator('#bookFind').tap();await page.waitForFunction(()=>document.activeElement.id==='bookFindHeading');
 assert(await page.locator('#records').isHidden(),'Search sheet does not overlay fish controls');
 await page.locator('#bookSearch').fill('prawn');await page.locator('#bookFindDone').tap();
 assert(await page.locator('#bookFind').evaluate(el=>document.activeElement===el),'Done restores focus');
 assert(await page.locator('#species-40').isVisible());
 await page.locator('#bookFind').tap();assert.equal(await page.locator('#bookSearch').inputValue(),'prawn');
 await page.keyboard.press('Escape');assert(await page.locator('#species-40').isVisible(),'Escape returns to the still-filtered fish grid');
 await page.locator('#species-40').tap();
 assert.equal(await page.locator('.catch-table').count(),0,'Receipts are not crowded into the profile');
 const hero=await page.locator('.book-profile > .fish-thumb').evaluate(e=>e.offsetWidth*e.offsetHeight);
 assert(hero>=2*78*46,'Fish hero must be at least twice the former area');
 await page.locator('#bookHistory').tap();
 const row=page.locator('.catch-log'),table=page.locator('.catch-table');
 assert.equal(await row.count(),1);
 assert.equal(await table.locator('thead th[scope=col]').count(),8);
 assert(await table.locator('thead th').evaluateAll(xs=>xs.every(x=>getComputedStyle(x).whiteSpace==='nowrap')));
 assert.equal(await row.locator('td').count(),8);
 assert.deepEqual(await row.locator('td').allTextContents(),await page.evaluate(r=>catchHistoryValues(r),captured));
 // Exercise a mixed retained receipt, incomplete receipt and legacy aggregate.
 const partial={id:40,cm:18};
 await page.evaluate(({partial,captured})=>{
  g.restoreEntry(40,15,18);
  catchHistory=[...Array.from({length:12},()=>({...captured})),partial];
  renderBook();
 },{partial,captured});
 assert.equal(await row.count(),13);
 assert.equal(await row.first().locator('.catch-unknown').count(),7);
 assert.match(await page.locator('.catch-legacy').innerText(),/2/);
 assert.equal(await page.locator('.catch-scroll').getAttribute('tabindex'),'0');
 const scroll=page.locator('.catch-scroll');
 const box=await scroll.boundingBox();assert(box);
 const x=Math.round(box.x+box.width*.7),y=Math.round(box.y+box.height*.7);
 await page.mouse.move(x,y);await page.mouse.wheel(120,120);
 await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 assert.deepEqual(await scroll.evaluate(e=>[e.scrollLeft,e.scrollTop]),[0,0],'Wheel must not scroll catch history');
 await page.mouse.move(x-28,y-36);
 assert.deepEqual(await scroll.evaluate(e=>[e.scrollLeft,e.scrollTop]),[0,0],'Hovering without holding must not scroll');
 await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x-70,y-70,{steps:5});await page.mouse.up();
 await page.waitForFunction(()=>{const e=document.querySelector('.catch-scroll');return e.scrollLeft>0&&e.scrollTop>0;});
 assert.equal(await page.evaluate(()=>bookSpecies),40,'Mouse press-drag stays inside history');
 await scroll.press('Home');await scroll.evaluate(e=>e.scrollLeft=0);
 await page.waitForFunction(()=>document.querySelector('.catch-scroll').scrollTop===0);
 const before=await scroll.evaluate(e=>({top:e.scrollTop,head:e.querySelector('thead').getBoundingClientRect().top}));
 if(touch)await swipe('.catch-scroll',0,-78);
 else await scroll.evaluate(e=>e.scrollTop=65);
 await page.waitForFunction(()=>document.querySelector('.catch-scroll').scrollTop>0);
 const after=await scroll.evaluate(e=>({top:e.scrollTop,head:e.querySelector('thead').getBoundingClientRect().top}));
 assert(after.top>before.top&&Math.abs(before.head-after.head)<1,'Header remains pinned as receipts pan vertically');
 if(touch)await swipe('.catch-scroll',-85);
 else await scroll.evaluate(e=>e.scrollLeft=65);
 await page.waitForFunction(()=>document.querySelector('.catch-scroll').scrollLeft>0);
 assert.equal(await page.evaluate(()=>bookSpecies),40,'Swiping inside catch table never changes species');
 await shot('Thai-Waters-catch-history');await tapBookButton('#back');await page.waitForFunction(()=>bookDetailView==='profile'&&bookSpecies===40);
 assert(await page.locator('#bookHistory').isVisible());await tapBookButton('#back');await page.waitForFunction(()=>bookSpecies===null);
 assert(await page.locator('#species-40').isVisible());
 await page.locator('#back').tap();await page.locator('[data-section=home] [data-to=sensors]').tap();await showControl(page,'#handheldEnable');await page.locator('#handheldEnable').check();await page.keyboard.press('v');await page.locator('#resume').tap();await page.keyboard.press('c');await page.waitForFunction(()=>g.state()===1||g.state()===2);
 if(!process.env.PLAYTEST_URL&&!process.env.PRIVATE_SITE_CHECK)await assertRayongLanding(browser,target);
 assert.deepEqual(errors,[]);console.log('PASS three Thai location typefaces, 480×320 gallery, confirmed catch across reload, eight history fields and two-axis scroll, full-width HUD, reduced-motion prompt, and controller cast.');
 }finally{try{await browser.close();}finally{await entry?.close();}}
})().catch(e=>{console.error(e);process.exitCode=1;});
