const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const {showControl}=require('./menu-controls.cjs');
const crypto=require('node:crypto');
const key='thai-atlas-v2',wanted=path.resolve(process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html'));
const file=pathToFileURL(wanted).href;
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH,headless:true});
 const requests=[],errors=[];
 const open=async()=>{
  const c=await browser.newContext({offline:true,acceptDownloads:true,isMobile:true,hasTouch:true,viewport:{width:844,height:390}});
  const p=await c.newPage();p.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(new URL(r.url()).protocol);});p.on('pageerror',e=>errors.push(e.message));
  await p.goto(file);await p.waitForFunction(()=>g&&!$('act').disabled);
  assert.equal(new URL(p.url()).protocol,'file:');assert.equal(p.url(),file);return p;
 };
 const career=async p=>{
  await p.locator('#openMenu').tap();await p.locator('[data-to=rod]').tap();
  const careerOpen=await showControl(p,'#careerOpen');
  await careerOpen.tap();
  await (await showControl(p,'#careerExport')).waitFor();
 };
 try{
  const src=await open(),backupPage=await open();
  console.log('TW_LANE file '+crypto.createHash('sha256').update(await fs.readFile(wanted)).digest('hex'));
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
  assert.equal(await backupPage.evaluate(()=>g.state()),0);
  await career(backupPage);
  const fileInput=await showControl(backupPage,'#careerFile');
  await fileInput.setInputFiles({name:'backup.json',mimeType:'application/json',buffer:bytes});
  const replace=backupPage.locator('#careerRestore');await replace.waitFor();
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),null,'choosing cannot write');
  await Promise.all([backupPage.waitForEvent('domcontentloaded'),replace.tap()]);
  await backupPage.waitForFunction(()=>g?.state()===5&&!$('act').disabled);
  const loaded=await backupPage.evaluate(()=>{const b=careerSnapshot();return [b.book[40],b.pending,b.pendingCapture,b.finish];});
  assert.deepEqual(loaded,[expected.book,expected.pending,expected.pendingCapture,expected.finish]);
  assert.equal(await backupPage.evaluate(()=>g.caught(41)),0);
  await backupPage.locator('#catchContinue').tap();
  await backupPage.waitForFunction(()=>g.state()===0&&g.caught(41)===1);
  const before=await backupPage.evaluate(k=>localStorage.getItem(k),key);
  assert.equal(JSON.parse(before).book[41][0],1,'pending catch was filed exactly once');
  const firstEpoch=await backupPage.evaluate(()=>performance.timeOrigin);
  assert.equal(await backupPage.evaluate(()=>history.state?.pocketReelCareerKnown),true);
  await backupPage.addInitScript(()=>{
   window.__fileCareerStart={known:history.state?.pocketReelCareerKnown===true,ready:document.readyState,epoch:performance.timeOrigin};
  });
  await backupPage.evaluate(k=>localStorage.removeItem(k),key);
  await backupPage.reload();await backupPage.waitForFunction(()=>g&&!$('act').disabled);
  const start=await backupPage.evaluate(()=>window.__fileCareerStart);
  assert.notEqual(start.epoch,firstEpoch);assert.equal(start.ready,'loading');assert.equal(start.known,true,'same file entry retains marker at document-start');
  await career(backupPage);
  assert(await backupPage.locator('#careerExport').isDisabled(),'blank recovery is not downloadable as the original');
  assert(await backupPage.locator('#careerFile').isDisabled(),'recovery does not accept in-place replacement');
  assert.match(await backupPage.locator('#careerPrivacy').textContent(),/localhost/);
  await backupPage.evaluate(()=>{finish=2;save();});
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),null);
  await backupPage.evaluate(([k,v])=>{localStorage.setItem(k,v);finish=0;save();},[key,before]);
  assert.equal(await backupPage.evaluate(k=>localStorage.getItem(k),key),before,'never overwrite a binding that returns during recovery');
  assert.deepEqual(requests,[]);assert.deepEqual(errors,[]);
  console.log('PASS direct file actual export/import download, pending ID/mass, exactly once, known-missing recovery, zero network.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
