const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core'),assert=require('node:assert/strict');
(async()=>{
 const dir=path.resolve(process.argv[2]||'outputs'),preview=process.argv.includes('--preview');
 const file=path.join(dir,'Riffle-Rev-F-engineering-review.html');
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const p=await browser.newPage({viewport:{width:1260,height:820}}),errors=[];
 p.on('pageerror',e=>errors.push(String(e)));
 await p.goto(pathToFileURL(file).href);await p.evaluate(()=>document.fonts.ready);await p.getByRole('heading',{name:'Engineering release decision'}).waitFor();
 await p.getByRole('heading',{name:'Table of contents'}).waitFor();
 await p.locator('.toc a[href="#software"]').click();await p.locator('#swFind').fill('salvage');assert.equal(await p.locator('#swRows details').count(),1);await p.locator('#swRows summary').click();
 await p.locator('[data-tab=demo]').click();await p.locator('#loadDemo').click();const game=p.frameLocator('#gameFrame');await game.locator('#act:enabled').waitFor({state:'attached',timeout:45000});
 await game.locator('#scene').waitFor({state:'attached'});let demo=p.frames().find(f=>f.parentFrame()&&f.url()==='about:srcdoc');await demo.evaluate(()=>{tap()});await demo.waitForFunction(()=>g.state()!==0);
 await p.locator('[data-tab=overview]').click();
 if(process.env.HANDBOOK_PREVIEW)await p.screenshot({path:process.env.HANDBOOK_PREVIEW});
 await p.locator('[data-tab=circuits]').click();await p.selectOption('#casePick',{label:(await p.locator('#casePick option').allTextContents()).find(t=>t.startsWith('rail_derated_slow'))});
 assert.match(await p.locator('#caseDetail').innerText(),/2\.8356/);assert(await p.locator('#wave polyline').getAttribute('points'));
 await p.locator('#draw').fill('300');assert.equal(await p.locator('#runtime').textContent(),'3.4 h');
 await p.locator('[data-tab=validation]').click();await p.selectOption('#gate','DVT');await p.locator('#searchTest').fill('OTA');assert((await p.locator('#testRows details').count())>0);await p.locator('#testRows summary').first().click();
 await p.locator('[data-tab=business]').click();assert.match(await p.locator('#scenario').innerText(),/98.93/);await p.selectOption('#lot','1000');assert.match(await p.locator('#scenario').innerText(),/91.49/);await p.locator('#findPart').fill('DRV2605');assert((await p.locator('#bomGrid tbody tr').count())>0);
 await p.locator('[data-tab=factory]').click();await p.locator('#stationPick').selectOption('4');assert((await p.locator('#stationSpec').innerText()).includes('Record'));
 await p.locator('[data-tab=circuits]').click();await p.locator('#brakeCorner').selectOption('1');assert.match(await p.locator('#brakeMetrics').innerText(),/1.1805 A/);
 await p.goBack();await p.locator('#stationPick').waitFor({state:'visible'});
 await p.locator('[data-tab=assembly]').click();const frame=p.frameLocator('#viewer');await frame.locator('canvas').first().waitFor({state:'attached',timeout:45000});await p.waitForTimeout(600);
 assert.equal(errors.length,0,errors.join('; '));await p.locator('[data-tab=overview]').click();
 await p.setViewportSize({width:390,height:844});assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));await p.locator('[data-tab=circuits]').click();await p.locator('#casePick').selectOption('0');
 await p.setViewportSize({width:1200,height:800});await p.emulateMedia({media:'print'});
 await p.pdf({path:path.join(dir,'Riffle-Rev-F-production-review.pdf'),printBackground:true,preferCSSPageSize:true,displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="margin:0 13mm;font:9px Arial;color:#55685a;width:100%;display:flex;justify-content:space-between"><span>RIFFLE POCKET  /  REV F ENGINEERING REVIEW</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'});
 console.log('PASS playable embedded cast, software filters, station selection, browser history, separate brake simulations, mobile layout, circuit traces, runtime, BOM and cost controls, validation filters, real 3D canvas, zero page exceptions, PDF export.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
