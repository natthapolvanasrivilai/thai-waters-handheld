const {requireBootHome}=require('./boot-home-check.cjs');
const assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright-core');
const {openPersistenceEntry}=require('./persistence-entry.cjs');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 let entry;
 try{entry=await openPersistenceEntry(path.resolve(__dirname,'../../game/Thai-Waters-play.html'));
 const p=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390}});
 // This test asserts an English journal title; Thai names have their own default-locale integration test.
 await p.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
 await p.goto(entry.url);
 await (await requireBootHome(p)).tap();
 await p.waitForFunction(()=>g&&!$('act').disabled);
 const result=await p.evaluate(async()=>{
  const seen=new Map(),shapes=new Set(),dupes=[],missing=[];
  const c=document.createElement('canvas');c.width=96;c.height=50;const ctx=c.getContext('2d',{willReadFrequently:true});
  const digest=async data=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data))).join('.');
  for(let id=0;id<atlas.fish.length;id++){
   if(!g.hasPortrait(id)){missing.push(id);continue;}
   if((atlas.fish[id].art??id)!==id)throw Error('Shared art ID '+id);
   ctx.clearRect(0,0,96,50);drawSpecimen(ctx,id,0,0,96,50);
   const rgba=ctx.getImageData(0,0,96,50).data,mask=new Uint8Array(4800);for(let i=0;i<4800;i++)mask[i]=rgba[i*4+3]?1:0;
   if(mask.some((on,i)=>on&&(i<96||i>=4704||i%96===0||i%96===95)))throw Error('Missing transparent margin on '+id);
   const area=mask.reduce((a,b)=>a+b,0);if(area<60)throw Error('Empty image '+id);
   let left=96,right=0,top=50,bottom=0;for(let i=0;i<mask.length;i++)if(mask[i]){const x=i%96,y=Math.floor(i/96);left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);}
   if(area>(right-left+1)*(bottom-top+1)*.94)throw Error('Opaque rectangular backing on '+id);
   const h=await digest(rgba);if(seen.has(h))dupes.push([id,seen.get(h)]);seen.set(h,id);shapes.add(await digest(mask));
  }
  const ids=[1822,76,2314,77,1821,1756,82,85,1825,91,2167,390,60,2168,2490,2544];
  const plate=document.createElement('canvas');plate.width=720;plate.height=464;const ink=plate.getContext('2d');ink.imageSmoothingEnabled=false;ink.fillStyle='#203c34';ink.fillRect(0,0,plate.width,plate.height);
  ids.forEach((id,i)=>{const x=i%4*180,y=Math.floor(i/4)*116;drawSpecimen(ink,id,x+4,y+4,172,89);ink.fillStyle='#f0e7cf';ink.font='italic 12px Georgia';ink.fillText(atlas.fish[id].name,x+6,y+105,168);});
  return {catalogSize:atlas.fish.length,count:seen.size,shapes:shapes.size,dupes,missing,sheet:plate.toDataURL()};
 });assert.deepEqual(result.dupes,[]);assert.deepEqual(result.missing,[]);assert.equal(result.catalogSize,2545);assert.equal(result.count,result.catalogSize);const manifest=require('../../game/art-source/field/plates.json');assert.equal(result.count,60+manifest.reduce((a,p)=>a+p.ids.length,0));assert.equal(result.shapes,result.count);
 const labeo=await p.evaluate(()=>{
  const id=1822;
  if(atlas.fish[id].name!=='Labeo dyocheilus'||!g.hasPortrait(id))throw Error('Missing Brahmaputra labeo');
  const f=atlas.fish[id];chooseSpot(f.spot,Math.max(0,[0,1,2,3].find(t=>f.mask&(1<<t))??0));stopArrival();
  g.restoreCatch(id,Math.round((f.low+f.high)/2));
  if(g.state()!==5||g.species()!==id)throw Error('Catch species mismatch');
  const source=CanvasRenderingContext2D.prototype.drawImage,drawn=[];
  try{
   CanvasRenderingContext2D.prototype.drawImage=function(img,...args){
    if(this===ctx&&img instanceof HTMLCanvasElement&&img.width===96&&img.height===50)drawn.push(img.toDataURL());
    return source.call(this,img,...args);
   };
   landedCatch(0);
  }finally{CanvasRenderingContext2D.prototype.drawImage=source;}
  if(drawn.length!==1||drawn[0]!==portraitCache.get(id).toDataURL())throw Error('Catch screen used a different sprite');
  pendingCapture=captureLanding();save();draw();return drawn[0];
 });
 if(process.env.LABEO_PREVIEW)await p.locator('#flatStage').screenshot({path:process.env.LABEO_PREVIEW});
 await p.locator('#catchContinue').click();await p.waitForFunction(()=>g.caught(1822)===1);
 await p.reload();
 const resume=await requireBootHome(p);
 assert.deepEqual(await p.evaluate(()=>[g.state(),g.caught(1822)]),[0,1]);
 await resume.tap();
 await p.waitForFunction(()=>g&&!$('act').disabled);
 const journal=await p.evaluate(()=>{
  showBookEntry(1822);
  const entry=document.querySelector('.book-profile');
  const thumb=entry.querySelector('canvas'),ref=document.createElement('canvas');
  ref.width=thumb.width;ref.height=thumb.height;const ink=ref.getContext('2d');ink.imageSmoothingEnabled=false;
  drawSpecimen(ink,1822,0,0,ref.width,ref.height);
  return {name:entry.querySelector('h2').textContent,pixels:thumb.toDataURL()===ref.toDataURL(),source:portraitCache.get(1822).toDataURL()};
 });
 assert.equal(journal.name,'Labeo dyocheilus');assert.equal(journal.pixels,true);assert.equal(journal.source,labeo);
 console.log('PASS restored Labeo dyocheilus catch, same full-color source on reveal and saved journal after reload.');
 // Opt-in branch, two DPRs and unchanged active localization.
 for(const dpr of [1,2]){
  const pilot=await browser.newPage({isMobile:true,hasTouch:true,deviceScaleFactor:dpr,viewport:{width:844,height:390}});
  await pilot.addInitScript(()=>localStorage.setItem('thai-waters-language','th'));
  await pilot.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href+'?fishArt=hq');
  await (await requireBootHome(pilot)).tap();
  await pilot.waitForFunction(()=>g&&!$('act').disabled);
  const state=await pilot.evaluate(async()=>{
   const ids=[1822,2158,2160,2190,2192],id=1822,unknown=1821;
   const ready=await Promise.all(ids.map(i=>loadDetailArt(i)?.done));
   menu.show();section('book');showBookEntry(id);
   const unseen=document.querySelector('#bookDetail .fish-thumb').dataset.fishArt;
   g.restoreEntry(id,1,Math.round((atlas.fish[id].low+atlas.fish[id].high)/2));
   showBookEntry(id);
   const tile=document.querySelector('#bookDetail .fish-thumb');
   // Compare against the same rendered canvas before its intrinsic bitmap is replaced.
   // A fixed viewport-pixel ceiling is sensitive to the mobile menu's responsive sizing.
   const legacyLayout=[tile.offsetWidth,tile.offsetHeight],legacyBitmap=[tile.width,tile.height];
   await loadDetailArt(id).done;await Promise.resolve();
   const layout=[tile.offsetWidth,tile.offsetHeight],name=document.querySelector('#bookDetail h2').textContent;
   const scientific=originalAtlas.fish[id].name;
   const labels=[...document.querySelectorAll('#bookDetail small')].map(n=>n.textContent);
   g.restoreCatch(id,Math.round((atlas.fish[id].low+atlas.fish[id].high)/2));
   if(g.state()!==5||g.species()!==id)throw Error('Not the requested catch');
   const hit=[],original=CanvasRenderingContext2D.prototype.drawImage;
   try{
    CanvasRenderingContext2D.prototype.drawImage=function(img,...args){if(this===ctx&&img===loadDetailArt(id).img)hit.push(args);return original.call(this,img,...args);};
    landedCatch(0);
   }finally{CanvasRenderingContext2D.prototype.drawImage=original;}
   const unmatched=originalAtlas.fish[id].name;originalAtlas.fish[id].name='test wrong species';
   let rejected;try{rejected=loadDetailArt(id)===null;}finally{originalAtlas.fish[id].name=unmatched;}
   return {ready,unseen:unseen||null,hq:tile.dataset.fishArt,px:[tile.width,tile.height],layout,legacyLayout,legacyBitmap,name,expected:atlas.fish[id].name,labels,scientific,hit,unknown:loadDetailArt(unknown)===null,rejected,dpr:devicePixelRatio};
  });
  assert.equal(state.dpr,dpr);assert.deepEqual(state.ready,[true,true,true,true,true]);
  assert.equal(state.unseen,null);assert.equal(state.hq,'hq');assert.deepEqual(state.px,[288,150]);
  assert.deepEqual(state.legacyBitmap,[144,75]);
  assert(state.legacyLayout.every(n=>n>0),'Legacy profile is visibly laid out');
  assert.deepEqual(state.layout,state.legacyLayout,'HQ bitmap must not change the original profile layout');
  assert.equal(state.name,state.expected);assert(state.name===state.scientific||state.labels.includes(state.scientific));
  assert.equal(state.hit.length,1,'Catch paints the matching source-resolution image');
  assert.equal(state.unknown,true);assert.equal(state.rejected,true);
  await pilot.close();
 }
 if(process.env.ART_PREVIEW)fs.writeFileSync(process.env.ART_PREVIEW,Buffer.from(result.sheet.split(',')[1],'base64'));
 console.log(result.count+' unique full-color portraits, '+result.shapes+' distinct alpha silhouettes; '+result.missing.length+' awaiting an illustration');
 }finally{try{await browser.close();}finally{await entry?.close();}}
})().catch(e=>{console.error(e);process.exitCode=1});
