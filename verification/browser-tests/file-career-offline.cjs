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
 const career=async p=>{
  await p.locator('#openMenu').tap();await p.locator('[data-section=home] [data-to=rod]').tap();
  const careerOpen=await showControl(p,'#careerOpen');
  await careerOpen.tap();
  await (await showControl(p,'#careerExport')).waitFor();
 };
 try{
  const src=await open(),backupPage=await open();
  console.log('TW_LANE file '+crypto.createHash('sha256').update(await fs.readFile(wanted)).digest('hex'));
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
