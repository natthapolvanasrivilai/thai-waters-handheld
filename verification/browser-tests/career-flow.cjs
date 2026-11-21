const {requireBootHome}=require('./boot-home-check.cjs');
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const {openPersistenceEntry}=require('./persistence-entry.cjs');
const {chromium,webkit}=require('playwright-core');
(async()=>{
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH});
 let entry;
 try{
  entry=await openPersistenceEntry(path.resolve(__dirname,'../../game/Thai-Waters-play.html'),process.env.PLAYTEST_URL);
  const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390},acceptDownloads:true});
  const key='thai-atlas-v2',target=entry.url;
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(target);
  const play=await requireBootHome(page);assert.equal(await page.evaluate(()=>g.state()),0);
  await play.tap();await page.waitForFunction(()=>g&&!$('act').disabled);
  const legacyBytes=await page.evaluate(key=>{
   const b=careerSnapshot();b.schema=3;b.book[40]=[2,18];
   b.history=[{id:40,cm:18,grams:47}];const raw=JSON.stringify(b);localStorage.setItem(key,raw);return raw;
  },key);
  await page.reload();
  const resumeLegacy=await requireBootHome(page);
  assert.deepEqual(await page.evaluate(()=>[g.caught(40),g.best(40),g.state()]),[2,18,0]);
  assert.equal(await page.evaluate(k=>localStorage.getItem(k),key),legacyBytes);
  await resumeLegacy.tap();await page.waitForFunction(()=>g?.caught(40)===2);
  assert.equal(await page.evaluate(()=>g.best(40)),18);
  const career=async()=>{
   await page.locator('#openMenu').tap();await page.locator('[data-section=home] [data-to=rod]').tap();
   while(await page.locator('#sheetNext').isEnabled())await page.locator('#sheetNext').tap();
   await page.locator('[data-section=home] [data-to=career]').tap();
   await page.locator('#careerExport').waitFor();
  };
  await career();const saved=page.waitForEvent('download');await page.locator('#careerExport').tap();
  const file=await saved;assert.match(file.suggestedFilename(),/^Pocket-Reel-career-\d{4}-\d\d-\d\d\.json$/);
  const backup=await fs.readFile(await file.path());
  const wrap=JSON.parse(backup);assert.equal(wrap.version,1);assert.deepEqual(wrap.career.book[40],[2,18]);
  const before=await page.evaluate(k=>localStorage.getItem(k),key);
  await page.locator('#sheetNext').tap();
  const input=page.locator('#careerFile');
  await input.setInputFiles({name:'broken.json',mimeType:'application/json',buffer:Buffer.from('{}')});
  await page.waitForFunction(()=>$('careerStatus').textContent.length>0);
  assert(await page.locator('#careerRestore').isHidden());
  await input.setInputFiles({name:'backup.json',mimeType:'application/json',buffer:backup});
  await page.locator('#careerRestore').waitFor();
  assert.equal(await page.evaluate(k=>localStorage.getItem(k),key),before);
  await Promise.all([page.waitForEvent('domcontentloaded'),page.locator('#careerRestore').tap()]);
  const resumeBackup=await requireBootHome(page);
  assert.deepEqual(await page.evaluate(k=>{
   const s=JSON.parse(localStorage.getItem(k));
   return {native:[g.caught(40),g.best(40),g.state()],schema:s.schema,history:s.history,pending:s.pending,appliedHistory:catchHistory};
  },key),{native:[2,18,0],schema:4,history:[{id:40,cm:18,grams:47}],pending:null,appliedHistory:[{id:40,cm:18,grams:47}]});
  await resumeBackup.tap();
  await page.waitForFunction(()=>g?.caught(40)===2);
  assert.equal(await page.evaluate(()=>g.best(40)),18);
  assert.equal(JSON.parse(await page.evaluate(k=>localStorage.getItem(k),key)).schema,4);
  await page.locator('#act').tap();await page.waitForFunction(()=>g.state()===1||g.state()===2);
  assert.deepEqual(errors,[]);console.log('PASS real browser offline backup UI, schema-3 migration, PB restore and immediate cast.');
 }finally{try{await browser.close();}finally{await entry?.close();}}
})().catch(e=>{console.error(e);process.exitCode=1;});
