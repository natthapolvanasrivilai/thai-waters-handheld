const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');
(async()=>{
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH});
 try{
  const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390},acceptDownloads:true});
  const key='thai-atlas-v2',target=process.env.PLAYTEST_URL||pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(target);await page.waitForFunction(()=>g&&!$('act').disabled);
  await page.evaluate(key=>{
   const b=careerSnapshot();b.schema=3;b.book[40]=[2,18];
   b.history=[{id:40,cm:18,grams:47}];localStorage.setItem(key,JSON.stringify(b));
  },key);
  await page.reload();await page.waitForFunction(()=>g?.caught(40)===2);
  assert.equal(await page.evaluate(()=>g.best(40)),18);
  const career=async()=>{
   await page.locator('#openMenu').tap();await page.locator('[data-to=career]').tap();
   await page.locator('#careerExport').waitFor();
  };
  await career();const saved=page.waitForEvent('download');await page.locator('#careerExport').tap();
  const file=await saved;assert.match(file.suggestedFilename(),/^Pocket-Reel-career-\d{4}-\d\d-\d\d\.json$/);
  const backup=await fs.readFile(await file.path());
  const wrap=JSON.parse(backup);assert.equal(wrap.version,1);assert.deepEqual(wrap.career.book[40],[2,18]);
  const before=await page.evaluate(k=>localStorage.getItem(k),key);
  const input=page.locator('#careerFile');
  await input.setInputFiles({name:'broken.json',mimeType:'application/json',buffer:Buffer.from('{}')});
  await page.waitForFunction(()=>$('careerStatus').textContent.length>0);
  assert(await page.locator('#careerRestore').isHidden());
  await input.setInputFiles({name:'backup.json',mimeType:'application/json',buffer:backup});
  await page.locator('#careerRestore').waitFor();
  assert.equal(await page.evaluate(k=>localStorage.getItem(k),key),before);
  await Promise.all([page.waitForEvent('domcontentloaded'),page.locator('#careerRestore').tap()]);
  await page.waitForFunction(()=>g?.caught(40)===2);
  assert.equal(await page.evaluate(()=>g.best(40)),18);
  assert.equal(JSON.parse(await page.evaluate(k=>localStorage.getItem(k),key)).schema,4);
  await page.locator('#act').tap();await page.waitForFunction(()=>g.state()===1||g.state()===2);
  assert.deepEqual(errors,[]);console.log('PASS real browser offline backup UI, schema-3 migration, PB restore and immediate cast.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
