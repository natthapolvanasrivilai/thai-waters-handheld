const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const {showControl}=require('./menu-controls.cjs');
const {requireBootHome}=require('./boot-home-check.cjs');
const crypto=require('node:crypto');
const key='thai-atlas-v2',wanted=path.resolve(process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html'));
const file=pathToFileURL(wanted).href;
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH,headless:true});
 const requests=[],errors=[];
 const open=async (viewport={width:844,height:390})=>{
  const c=await browser.newContext({offline:true,acceptDownloads:true,isMobile:true,hasTouch:true,viewport});
  const p=await c.newPage();p.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(new URL(r.url()).protocol);});p.on('pageerror',e=>errors.push(e.message));
  await p.goto(file);
  const play=await requireBootHome(p);
  if(viewport.width<=390){
   const r=await play.boundingBox();assert(r&&r.width>=44&&r.height>=44,'Visible phone Resume has a 44 CSS px touch target');
   assert.equal(await p.locator('html').getAttribute('lang'),'th');
  }
  await play.tap();await p.waitForFunction(()=>g&&!$('act').disabled);
  assert.equal(new URL(p.url()).protocol,'file:');assert.equal(p.url(),file);return p;
 };
 // Exercise the real packed WASM PCM adapter on a separate synthetic profile.
 // The exact timestamped virtual-encoder fixture avoids frame/touch jitter;
 // the rest of this file still exercises real file input and Recovery controls.
 const rodPcm=(p,next=null)=>p.evaluate(next=>{
  if(typeof g.setRodFinish!=='function')throw Error('Packed WASM lacks the rod-voice export');
  g.config(3,0,1,0);g.reelVolume(2);
  const read=()=>Array.from(new Int16Array(g.memory.buffer,g.samples(),512));
  const queue=()=>{
   g.resetDetents();g.dialReset();g.dialSample(2048,0);
   let cue=0;
   for(let i=1;i<=4;i++){
    g.dialSample(2048+90*i,30*i);
    cue=g.rumbleEvent(1000+30*i,1);
   }
   if(cue!==9)throw Error('Expected a real detent before reading PCM');
  };
  if(next!==null){
   queue();
   const field=document.getElementById('finish');
   field.selectedIndex=next;field.dispatchEvent(new Event('change',{bubbles:true}));
   return read();
  }
  // Each voice cycles eight takes; order depends on preceding clicks.
  const takes=[];
  for(let i=0;i<8;i++){queue();const pcm=read();if(!pcm.some(Boolean))throw Error('Detent produced no PCM');takes.push(pcm.join(','));}
  return takes.sort();
 },next);
 const rodMenu=async p=>{
  await p.locator('#openMenu').tap();await p.locator('[data-section=home] [data-to=rod]').tap();
  const field=await showControl(p,'#finish');await field.waitFor();
  return field;
 };
 const rodVoices=async()=>{
  const p=await open();
  try{
   const river=await rodPcm(p);
   assert.equal(new Set(river).size,8,'Default River reed emits all eight real PCM takes');
   const field=await rodMenu(p);
   assert.equal(await field.evaluate(el=>el.selectedIndex),0);
   await field.selectOption({index:0});
   const riverSave=await p.evaluate(k=>JSON.parse(localStorage.getItem(k)),key);
   assert(riverSave);assert.equal(riverSave.schema,4);assert.equal(riverSave.finish,0);
   // One synchronous DOM event inside the PCM fixture ensures the frame
   // loop cannot consume the queued A click before the switch clears it.
   assert((await rodPcm(p,1)).every(x=>x===0),'Switch drops pending old-voice PCM');
   const copper=await rodPcm(p);
   assert.equal(new Set(copper).size,8,'Copper emits all eight real PCM takes');
   assert.notDeepEqual(copper,river,'Copper and River reed route to different voices');
   const saved=await p.evaluate(k=>localStorage.getItem(k),key);
   const {finish:oldFinish,...riverFields}=riverSave;
   const {finish:newFinish,...copperFields}=JSON.parse(saved);
   assert.equal(newFinish,1);assert.deepEqual(copperFields,riverFields,'Equip changes only the existing finish field');
   await p.reload();
   const resume=await requireBootHome(p);await resume.tap();
   await p.waitForFunction(()=>g&&!$('act').disabled);
   assert.equal(new URL(p.url()).protocol,'file:');
   assert.equal(await p.evaluate(k=>localStorage.getItem(k),key),saved,'Resume leaves saved bytes untouched');
   assert.equal(await p.locator('#finish').evaluate(el=>el.selectedIndex),1);
   assert.deepEqual(await rodPcm(p),copper,'Real restore installs Copper audio before first use');
   await (await rodMenu(p)).selectOption({index:0});
   assert.deepEqual(await rodPcm(p),river,'Selecting River reed switches back to exact A voice');
  }finally{await p.context().close();}
 };
 const career=async p=>{
  await p.locator('#openMenu').tap();await p.locator('[data-section=home] [data-to=rod]').tap();
  const careerOpen=await showControl(p,'#careerOpen');
  await careerOpen.tap();
  await (await showControl(p,'#careerExport')).waitFor();
 };
 try{
  const src=await open(),backupPage=await open();
  console.log('TW_LANE file '+crypto.createHash('sha256').update(await fs.readFile(wanted)).digest('hex'));
  await rodVoices();
  const phone=await open({width:320,height:700});await phone.context().close();
  assert.equal(await src.evaluate(()=>g.state()),0);
  assert(await src.locator('#openMenu').isVisible());
  await career(src); // Catch hides the Menu button; enter the genuine Career UI while idle.
  const expected=await src.evaluate(()=>{
   g.restoreCatch(40,atlas.fish[40].low);g.fileCatch();g.advance(800,0,0,0);
   finish=1;g.restoreCatch(41,atlas.fish[41].low);pendingCapture=captureLanding();pendingCapture.grams=95;save();
   const b=careerSnapshot();return {book:b.book[40],pending:b.pending,pendingCapture:b.pendingCapture,finish};
  });
  assert.equal(expected.pending[0],41);assert.equal(expected.pendingCapture.id,41);assert.equal(expected.pendingCapture.grams,95);
  assert(await src.evaluate(()=>g.state()===5&&!g.filed()&&menu.open&&menuPage==='career'));
  assert(await src.locator('#careerExport').isVisible(),'The genuine Career export stays visible with a pending fixture');
  const p=src.waitForEvent('download');await src.locator('#careerExport').tap();
  const dl=await p, bytes=await fs.readFile(await dl.path());
  assert.match(dl.suggestedFilename(),/^Pocket-Reel-career-\d{4}-\d\d-\d\d\.json$/);
  const wrap=JSON.parse(bytes);assert.equal(wrap.version,1);
  assert.deepEqual([wrap.career.book[40],wrap.career.pending,wrap.career.pendingCapture,wrap.career.finish],[expected.book,expected.pending,expected.pendingCapture,expected.finish]);

  // Retain the already-shipped guard's active-file Career controls as a
  // separate branch: lose the source's synthetic key while actually playing.
  await src.evaluate(k=>localStorage.removeItem(k),key);
  await src.locator('#resume').tap();
  await src.locator('#catchContinue').tap();
  await src.waitForFunction(()=>g.state()===0&&g.caught(41)===1);
  assert.equal(await src.evaluate(k=>localStorage.getItem(k),key),null);
  await career(src);
  assert(await src.locator('#careerFile').isDisabled(),'active file recovery does not accept in-place replacement');
  assert.match(await src.locator('#careerPrivacy').textContent(),/localhost/);
  assert.equal(await backupPage.evaluate(()=>g.state()),0);
  await career(backupPage);
  const fileInput=await showControl(backupPage,'#careerFile');
  await fileInput.setInputFiles({name:'backup.json',mimeType:'application/json',buffer:bytes});
  const replace=backupPage.locator('#careerRestore');await replace.waitFor();
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),null,'choosing cannot write');
  await Promise.all([backupPage.waitForEvent('domcontentloaded'),replace.tap()]);
  const resumeImported=await requireBootHome(backupPage);
  assert.equal(await backupPage.evaluate(()=>g.state()),5);
  const importedBytes=await backupPage.evaluate(k=>localStorage.getItem(k),key);
  const loaded=await backupPage.evaluate(()=>{const b=careerSnapshot();return [b.book[40],b.pending,b.pendingCapture,b.finish];});
  assert.deepEqual(loaded,[expected.book,expected.pending,expected.pendingCapture,expected.finish]);
  assert.equal(await backupPage.evaluate(()=>g.caught(41)),0);
  assert(await backupPage.locator('#catchContinue').isDisabled());
  await resumeImported.tap();await backupPage.waitForFunction(()=>g?.state()===5&&!$('act').disabled);
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),importedBytes,'Resume does not re-import or file the catch');
  await backupPage.locator('#catchContinue').tap();
  await backupPage.waitForFunction(()=>g.state()===0&&g.caught(41)===1);
  const before=await backupPage.evaluate(k=>localStorage.getItem(k),key);
  assert.equal(JSON.parse(before).book[41][0],1,'pending catch was filed exactly once');
  const filed=JSON.parse(before).history.filter(x=>x.uid===expected.pendingCapture.uid);
  assert.deepEqual(filed,[expected.pendingCapture]);
  const firstEpoch=await backupPage.evaluate(()=>performance.timeOrigin);
  assert.equal(await backupPage.evaluate(()=>history.state?.pocketReelCareerKnown),true);
  await backupPage.addInitScript(()=>{
   window.__fileCareerStart={known:history.state?.pocketReelCareerKnown===true,ready:document.readyState,epoch:performance.timeOrigin};
  });
  await backupPage.evaluate(k=>localStorage.removeItem(k),key);
  await backupPage.reload();
  await backupPage.locator('#startupRecovery').waitFor({state:'visible'});
  const start=await backupPage.evaluate(()=>window.__fileCareerStart);
  assert.notEqual(start.epoch,firstEpoch);assert.equal(start.ready,'loading');assert.equal(start.known,true,'same file entry retains marker at document-start');
  const blocked=()=>backupPage.evaluate(()=>g===null&&!powered&&!$('menu').open&&$('act').disabled);
  assert(await blocked(),'Known missing storage opens Recovery, not a fresh playable career');
  assert(await backupPage.locator('#careerExport').isHidden(),'blank recovery is not downloadable as the original');
  assert(await backupPage.locator('#careerRestore').isHidden(),'recovery does not accept in-place replacement');
  assert(await backupPage.locator('#startupRecoveryUseSession').isHidden());
  await backupPage.locator('#startupRetry').tap();
  await backupPage.waitForFunction(()=>startupPending===null&&!$('startupRecovery').hidden);
  assert(await blocked());assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),null);

  await backupPage.locator('#startupRecoveryFile').setInputFiles({name:'backup.json',mimeType:'application/json',buffer:bytes});
  const use=backupPage.locator('#startupRecoveryUseSession');await use.waitFor({state:'visible'});
  assert(await blocked());assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),null,'Recovery preview is read-only');
  await use.tap();
  const resumeTemporary=await requireBootHome(backupPage,{temporary:true});
  assert.equal(await backupPage.evaluate(()=>performance.timeOrigin),start.epoch,'Temporary restore never reloads');
  assert.deepEqual(await backupPage.evaluate(()=>[g.state(),g.filed(),g.caught(41),pendingCapture,pendingDay]),[5,0,0,expected.pendingCapture,0]);
  assert(await backupPage.locator('#sessionCareerNotice').isVisible());
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),null);

  // Make the exact original synthetic snapshot visible again. Actual Resume
  // and Continue must now file only the temporary copy, not the original.
  await backupPage.evaluate(([k,v])=>localStorage.setItem(k,v),[key,before]);
  await resumeTemporary.tap();
  await backupPage.locator('#catchContinue').waitFor({state:'visible'});
  assert.match(await backupPage.locator('#metrics').textContent(),/95 (?:g|กรัม)/);
  await backupPage.locator('#catchContinue').tap();
  await backupPage.waitForFunction(()=>g.state()===0&&g.caught(41)===1);
  assert.deepEqual(await backupPage.evaluate(u=>catchHistory.filter(x=>x.uid===u),expected.pendingCapture.uid),[expected.pendingCapture]);
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),before,'never overwrite a binding that returns during recovery');
  await career(backupPage);
  const temporary=backupPage.waitForEvent('download');await backupPage.locator('#careerExport').tap();
  const exported=await temporary;assert.match(exported.suggestedFilename(),/^Pocket-Reel-session-/);
  const tempCareer=JSON.parse(await fs.readFile(await exported.path())).career;
  assert.equal(tempCareer.book[41][0],1);assert.equal(tempCareer.pending,null);
  assert.deepEqual(tempCareer.history.filter(x=>x.uid===expected.pendingCapture.uid),[expected.pendingCapture]);
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),before);
  assert.deepEqual(requests,[]);assert.deepEqual(errors,[]);
  console.log('PASS direct file actual export/import download, pending ID/mass, exactly once, known-missing recovery, zero network.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
