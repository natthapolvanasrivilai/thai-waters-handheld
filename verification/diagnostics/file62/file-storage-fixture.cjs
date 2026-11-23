'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const count=Number(process.env.FIXTURE_CYCLES??3);
assert(Number.isInteger(count)&&count>=1&&count<=12,'FIXTURE_CYCLES must be 1–12');
const profiles={
 desktop:{hasTouch:false,isMobile:false,narrow:false},
 mobile:{hasTouch:true,isMobile:true,narrow:true},
 'touch-only':{hasTouch:true,isMobile:false,narrow:true},
 'mobile-only':{hasTouch:false,isMobile:true,narrow:true},
};
const order=(process.env.FIXTURE_LANES??'desktop,mobile').split(',');
assert(order.length&&new Set(order).size===order.length&&order.every(l=>Object.hasOwn(profiles,l)),
 'FIXTURE_LANES must list unique desktop,mobile,touch-only,mobile-only profiles');
(async()=>{
 const temp=await fs.mkdtemp(path.join(os.tmpdir(),'pocket-reel-fixture-'));
 let browser;
 const results=[];
 try{
  await fs.mkdir(path.join(temp,'prefixed'));
  for(const rel of ['probe.html','prefixed/probe.html']){
   await fs.copyFile(path.join(__dirname,'file-storage-fixture.html'),path.join(temp,rel));
  }
  const canonical=pathToFileURL(path.join(temp,'probe.html')).href;
  const prefixed=pathToFileURL(path.join(temp,'prefixed','probe.html')).href;
  browser=await chromium.launch({executablePath:process.env.BROWSER_PATH,headless:true});
  console.log('Synthetic file control · Chromium '+browser.version());
  for(const lane of order) for(let cycle=0;cycle<count;cycle++){
   const {hasTouch:touch,isMobile,narrow}=profiles[lane];
   const context=await browser.newContext({offline:true,viewport:narrow?{width:390,height:844}:{width:480,height:600},hasTouch:touch,isMobile});
   try{
    const page=await context.newPage();
    page.setDefaultTimeout(6000);
    page.setDefaultNavigationTimeout(12000);
    const problems=[];
    const network=[];
    page.on('pageerror',e=>problems.push(e.name));
    page.on('request',request=>{if(/^https?:/.test(request.url()))network.push(true);});
    await page.addInitScript(urls=>{
     if(!urls.includes(location.href))return;
     try{
      window.fixtureInit={language:localStorage.getItem('pocket-reel-fixture-language'),
       career:localStorage.getItem('pocket-reel-fixture-career'),error:null};
     }catch(e){window.fixtureInit={error:e.name};}
    },[canonical,prefixed]);
    const cdp=touch?await context.newCDPSession(page):null;
    async function press(id){
     const locator=page.locator('#'+id);
     if(!touch){await locator.press('Enter');return;}
     const box=await locator.boundingBox();
     assert(box,'touch target missing');
     const point={x:box.x+box.width/2,y:box.y+box.height/2};
     await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});
     await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    }
    await page.goto(canonical);
    const fresh=await page.evaluate(()=>fixtureAtScript);
    assert.deepEqual([fresh.language,fresh.career,fresh.error,fresh.known],[null,null,null,false],
     'fresh ephemeral context contaminated or storage unavailable');
    await press('seed');
    await press('move');
    const original=await page.evaluate(()=>({storage:readFixture(),record}));
    assert.deepEqual(original.record.map(x=>[x.button,x.trusted,x.type]),
     [['seed',true,touch?'pointerup':'click'],['move',true,touch?'pointerup':'click']]);
    assert.deepEqual([original.storage.language,original.storage.career,original.storage.known],
     ['synthetic-TH','synthetic-travel',true],'fixture writes did not happen');
    const reload=await page.reload();
    const now=await page.evaluate(()=>({init:window.fixtureInit,first:fixtureAtScript,later:readFixture()}));
    const healthy=value=>value?.error===null&&value?.language==='synthetic-TH'&&value?.career==='synthetic-travel';
    assert.equal(page.url(),canonical);
    assert(!reload||reload.url()===canonical);
    assert.equal(now.first.protocol,'file:');
    assert.equal(now.first.ready,'loading');
    assert.notEqual(now.first.epoch,original.storage.epoch);
    assert(now.first.known,'reload did not preserve history marker');
    const sameFilePassed=[now.init,now.first,now.later].every(healthy);
    await Promise.all([page.waitForURL(prefixed), page.locator('#relative').click()]);
    const sibling=await page.evaluate(()=>({init:window.fixtureInit,first:fixtureAtScript}));
    await page.goBack();
    assert.equal(page.url(),canonical);
    const back=await page.evaluate(()=>readFixture());
    const summary=x=>({language:x?.language==null?'missing':'present',
     career:x?.career==null?'missing':'present',error:x?.error??null});
    const row={cycle,lane,touch,isMobile,sameFilePassed,reload:[now.init,now.first,now.later].map(summary),
     relativeSibling:[sibling.init,sibling.first].map(summary),returned:summary(back),problems,network:network.length};
    results.push(row);
    console.log(JSON.stringify(row));
   }finally{await context.close();}
  }
  assert(results.every(x=>x.sameFilePassed&&x.problems.length===0&&x.network===0),
    'file:// control failed; see synthetic traces (no production result overridden)');
 }finally{
  try{if(browser)await browser.close();}finally{await fs.rm(temp,{recursive:true,force:true});}
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
