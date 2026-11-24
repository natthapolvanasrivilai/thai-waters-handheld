'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {createRequire}=require('node:module');
const localRequire=createRequire(path.resolve('verification/browser-tests/package.json'));
const {chromium}=localRequire('playwright-core');
const expected={node:'v22.16.0',playwright:'1.62.1',chromium:'151.0.7922.34'};
assert.equal(process.version,expected.node);
const pwVersion=localRequire('playwright-core/package.json').version;assert.equal(pwVersion,expected.playwright);
(async()=>{
const dir=await fs.mkdtemp(path.join(os.tmpdir(),'file62-synthetic-'));
let browser;
try {
  const fixture=path.join(dir,'synthetic.html');
  await fs.writeFile(fixture,'<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width"><button id=seed>Seed synthetic sample</button><script>document.querySelector("#seed").onclick=()=>{localStorage.setItem("fixture-known","synthetic-value");localStorage.setItem("fixture-career","synthetic-value")}</script>');
  const url=pathToFileURL(fixture).href;
  browser=await chromium.launch({executablePath:chromium.executablePath(),headless:true});assert.equal(browser.version(),expected.chromium);
  const lanes=[];
  for(const mode of ['desktop','mobile']){
    const ctx=await browser.newContext({offline:true,hasTouch:mode==='mobile',isMobile:mode==='mobile',viewport:mode==='mobile'?{width:390,height:844}:{width:480,height:600}});
    const page=await ctx.newPage(), cdp=await ctx.newCDPSession(page);
    const binding=[], cdpConsole=[], playwright=[], unexpected=[];
    const prefix='file62_probe:';
    const append=(list,s)=>{if(typeof s!=='string'||!s.startsWith(prefix))return; const p=JSON.parse(s.slice(prefix.length));
      assert.deepEqual(Object.keys(p).sort(),['career','epoch','known','persisted','phase','readable']);
      assert.match(p.epoch,/^\d{10,16}(?:\.\d{1,8})?$/);
      assert.ok(['init','pagehide'].includes(p.phase));
      assert.ok(['known','career','readable'].every(k=>typeof p[k]==='boolean'));
      assert.equal(p.phase==='init',p.persisted===null);
      if(p.phase==='pagehide')assert.equal(typeof p.persisted,'boolean');
      list.push(p)};
    cdp.on('Runtime.bindingCalled',e=>{if(e.name==='__file62Witness')append(binding,e.payload)});
    cdp.on('Runtime.consoleAPICalled',e=>{if(e.type==='debug')append(cdpConsole,e.args[0]?.value)});
    page.on('console',e=>{if(e.type()==='debug')append(playwright,e.text())});
    page.on('request',r=>{if(/^https?:/i.test(r.url()))unexpected.push(r.url());});
    await cdp.send('Runtime.enable');
    await cdp.send('Runtime.addBinding',{name:'__file62Witness'});
    await page.addInitScript(exact=>{
      if(window!==top||location.href!==exact)return;
      const epoch=String(performance.timeOrigin);
      const witness=(phase,persisted)=>{
        let known=false,career=false,readable=false;
        try{known=localStorage.getItem('fixture-known')!==null;career=localStorage.getItem('fixture-career')!==null;readable=true;}catch{}
        const text='file62_probe:'+JSON.stringify({phase,epoch,known,career,persisted,readable});
        if(typeof window.__file62Witness==='function') window.__file62Witness(text);
        console.debug(text);
      };
      witness('init',null);
      addEventListener('pagehide',e=>witness('pagehide',e.persisted),{once:true});
    },url);
    await page.goto(url);
    await (mode==='mobile'?page.locator('#seed').tap():page.locator('#seed').press('Enter'));
    const before=await page.evaluate(()=>[localStorage.getItem('fixture-known')!==null,localStorage.getItem('fixture-career')!==null]);
    assert.deepEqual(before,[true,true]);
    await page.reload();
    const after=await page.evaluate(()=>[localStorage.getItem('fixture-known')!==null,localStorage.getItem('fixture-career')!==null]);
    assert.deepEqual(after,[true,true]);assert.equal(page.url(),url);assert.deepEqual(unexpected,[]);
    for(const channel of [binding,cdpConsole,playwright]){
      const init=channel.filter(x=>x.phase==='init');
      assert.equal(init.length,2);assert.ok(init.every(p=>p.readable));assert.notEqual(init[0].epoch,init[1].epoch);
      assert.deepEqual(init.map(x=>[x.known,x.career]),[[false,false],[true,true]]);
      const hidden=channel.filter(x=>x.phase==='pagehide');
      assert.ok(hidden.length<=1);
      if(hidden.length){assert.ok(hidden[0].readable);assert.ok(channel.indexOf(hidden[0])>channel.indexOf(init[0])&&channel.indexOf(hidden[0])<channel.indexOf(init[1]));assert.equal(hidden[0].epoch,init[0].epoch);assert.deepEqual([hidden[0].known,hidden[0].career],[true,true]);}
    }
    lanes.push({mode,binding:binding.slice(),cdpConsole:cdpConsole.slice(),playwright:playwright.slice(),before,after});
    await ctx.close();
  }
  console.log(JSON.stringify({version:browser.version(),node:process.version,playwright:pwVersion,lanes},null,2));
}finally{await browser?.close();await fs.rm(dir,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
