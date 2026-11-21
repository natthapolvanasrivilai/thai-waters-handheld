const {requireBootHome}=require('./boot-home-check.cjs');
const assert=require('node:assert/strict'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');
(async()=>{
 const engine=process.env.TEST_WEBKIT?webkit:chromium,browser=await engine.launch(engine===webkit?{}:{executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{for(const width of [844,390,320]){
  const p=await browser.newPage({viewport:{width,height:width===844?390:800},isMobile:true,hasTouch:true});
  p.on('pageerror',e=>console.error(e.message));await p.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);
  await (await requireBootHome(p)).tap();
  await p.waitForFunction(()=>g&&!$('act').disabled);
  for(const lang of ['th','en']){
   await p.locator('#openMenu').tap();await p.locator('[data-language='+lang+']').tap();
   async function fits(){
    const bad=await p.evaluate(()=>{
     const menu=$('menu'),picker=$('lcdPicker'),frame=picker.hidden?menu:picker,r=frame.getBoundingClientRect();
     const nodes=[...frame.querySelectorAll('button,input:not([type=checkbox]),label,p,h2,small,.book-info,.lcd-choice,.build,fieldset')].filter(el=>el.getClientRects().length&&(!el.closest('#lcdPicker')||!picker.hidden));
     return nodes.filter(el=>{const b=el.getBoundingClientRect();return b.width>0&&b.height>0&&(b.left<r.left-1.5||b.right>r.right+1.5||b.bottom>r.bottom+1.5||b.top<r.top-1.5)}).map(el=>(el.id||el.textContent).slice(0,55));
    });assert.deepEqual(bad,[],width+' '+lang+' '+await p.locator('#menuTitle').textContent()+' '+bad);
   }
   await fits();
   for(const route of ['spots','rod','sound','sensors','crew','book']){
    await p.locator('[data-section=home] [data-to='+route+']').tap();
    while(await p.locator('#sheetPrev').isVisible()&&await p.locator('#sheetPrev').isEnabled())await p.locator('#sheetPrev').tap();
    for(;;){await fits();
     if(route==='crew'&&await p.locator('#cupScope').isVisible()){
      await p.evaluate(()=>{cupBoard={goal:tournamentGoal(),leaders:Array.from({length:11},(_,i)=>({rank:i+1,angler:'Angler '+(i+1),cm:98-i}))};rankPage=0;drawCup();});
      const last=p.locator('#cupLeaders .history-nav button').last();await last.tap();await last.tap();
      assert(await last.isDisabled());assert((await p.locator('#cupLeaders').innerText()).includes('#11'));await fits();
     }
     if(route==='spots'&&await p.locator('#places + button').isVisible()){
      await p.locator('#places + button').tap();const next=p.locator('#lcdPicker .menubar button').last();
      while(await next.isEnabled()){await fits();await next.tap();}
      await fits();await p.locator('.choice-list button').last().tap();
     }
     if(!await p.locator('#sheetNext').isVisible()||!await p.locator('#sheetNext').isEnabled())break;
     await p.locator('#sheetNext').tap();
    }
    if(route==='rod'){
     await p.locator('#careerOpen').tap();await fits();
     assert.equal(await p.locator('#sheetNumber').textContent(),'1/2','Repeated Career entry resumes at the summary');
     await p.locator('#sheetNext').tap();await fits();
     await p.locator('#back').tap();await fits();
    }
    if(route==='book'){
     await p.evaluate(()=>{g.restoreEntry(40,12,25);catchHistory=Array.from({length:12},(_,i)=>({id:40,at:Date.UTC(2026,10,18-i),place:106,period:3,weather:2,bait:14,cm:25,grams:130}));showBookEntry(40);});
     await fits();
     const history=p.locator('#bookDetail .catch-scroll'),receipts=history.locator('tbody tr');
     assert.equal(await receipts.count(),12,'All twelve receipts are reachable in one table');
     const before=await history.evaluate(e=>({head:e.querySelector('thead').getBoundingClientRect().top,top:e.scrollTop,canScroll:e.scrollHeight>e.clientHeight}));
     assert.equal(before.top,0);assert(before.canScroll,'The table scrolls inside the full LCD without overflowing it');
     await history.press('End');
     await p.waitForFunction(()=>{
      const e=document.querySelector('#bookDetail .catch-scroll');
      return e.scrollTop>0&&Math.abs(e.scrollTop+e.clientHeight-e.scrollHeight)<=1;
     });
     const after=await history.evaluate(e=>({head:e.querySelector('thead').getBoundingClientRect().top,
      last:e.querySelector('tbody tr:last-child').getBoundingClientRect().bottom,bottom:e.getBoundingClientRect().bottom}));
     assert(Math.abs(after.head-before.head)<1&&after.last<=after.bottom+1,'Last receipt is visible and the header stays pinned');
     await fits();
     await p.locator('#back').tap();await p.locator('#bookNext').tap();const id=await p.locator('.record').first().getAttribute('id');await p.locator('#'+id).tap();await fits();await p.locator('#back').tap();assert(await p.locator('#'+id).isVisible());}
    await p.locator('#back').tap();
   }
   await p.locator('#resume').tap();
  }
  await p.close();console.log(width+' px: paged menus, last water, scrollable catch history, journal return, Thai + English');
 }}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
