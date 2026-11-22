const {requireBootHome}=require('./boot-home-check.cjs');
const assert=require('node:assert/strict'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');
// Park a real mouse on one mode, then operate a different row by keyboard.
async function mixedInputFocus(browser){
 const p=await browser.newPage({viewport:{width:900,height:650},reducedMotion:'reduce'});
 try{
  await p.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);
  const start=p.locator('#bootStart');await start.waitFor({state:'visible'});await start.click();
  const rod=p.locator('#bootRoutes [data-to=rod]');
  // Right-click parks and focuses without activating the game's route.
  await rod.click({button:'right'});
  assert(await rod.evaluate(el=>el.matches(':hover')&&document.activeElement===el),'Trusted mouse is parked over Rods & Lures');
  await p.keyboard.press('Tab');
  const witness=await p.evaluate(()=>{
   const dock=$('arcadeDock'),parked=dock.querySelector('[data-to=rod]'),focused=dock.querySelector('[data-to=book]');
   const marked=b=>getComputedStyle(b.querySelector('.arcade-selector')).visibility==='visible';
   return {focus:document.activeElement===focused,focusVisible:focused.matches(':focus-visible'),hover:parked.matches(':hover'),
    marks:[...dock.querySelectorAll('button')].filter(marked).map(b=>b.dataset.to||b.id),
    focusedFill:getComputedStyle(focused).backgroundColor,parkedFill:getComputedStyle(parked).backgroundColor};
  });
  assert(witness.focus&&witness.focusVisible&&witness.hover,'Keyboard focus changes while the mouse remains parked');
  assert.deepEqual(witness.marks,['book'],'Only the keyboard-focused row is marked');
  assert.equal(witness.parkedFill,'rgba(0, 0, 0, 0)','Parked row has no highlight');
  assert.match(witness.focusedFill,/^rgba\(35, 103, 95, /,'Keyboard row remains visibly filled');
  await p.keyboard.press('Enter');
  assert.equal(await p.locator('#menu').getAttribute('data-page'),'book');
  assert(await p.locator('#records').isVisible(),'The visibly highlighted Fish Collection actually opens');
  assert(await p.locator('#act').isDisabled(),'Boot lock still prevents play');
 }finally{await p.close();}
}
(async()=>{
 const engine=process.env.TEST_WEBKIT?webkit:chromium,browser=await engine.launch(engine===webkit?{}:{executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
  await mixedInputFocus(browser);
  for(const width of [844,390,320]){
  const p=await browser.newPage({viewport:{width,height:width===844?390:800},isMobile:true,hasTouch:true});
  p.on('pageerror',e=>console.error(e.message));await p.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);
  await (await requireBootHome(p)).tap();
  await p.waitForFunction(()=>g&&!$('act').disabled);
  for(const lang of ['th','en']){
   await p.locator('#openMenu').tap();await p.locator('#languageRow [data-language='+lang+']').tap();
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
     await p.locator('#bookHistory').tap();await fits();
     const history=p.locator('#bookDetail .catch-scroll'),receipts=history.locator('tbody tr');
     assert.equal(await receipts.count(),12,'All twelve receipts are reachable in one table');
     const geometry=e=>{
      const frame=e.getBoundingClientRect(),header=e.querySelector('thead').getBoundingClientRect(),
        last=e.querySelector('tbody tr:last-child').getBoundingClientRect();
      return {headOffset:header.top-frame.top,headBottom:header.bottom,frameBottom:frame.bottom,
       scale:frame.height/e.offsetHeight,top:e.scrollTop,room:e.scrollHeight-e.clientHeight,
       lastTop:last.top,lastBottom:last.bottom,lastHeight:last.height};
     };
     const before=await history.evaluate(geometry);
     assert.equal(before.top,0);assert(before.room>0,'The table scrolls inside the full LCD without overflowing it');
     await history.press('End');
     await p.waitForFunction(()=>{
      const e=document.querySelector('#bookDetail .catch-scroll');
      return e.scrollTop>0&&Math.abs(e.scrollTop+e.clientHeight-e.scrollHeight)<=1;
     });
     const after=await history.evaluate(geometry),detail=JSON.stringify({width,lang,before,after});
     const rounding=1+after.scale; // scrollHeight/clientHeight are rounded native LCD pixels.
     assert(Math.abs(after.headOffset)<=rounding,'Header is pinned to its viewport: '+detail);
     assert(Math.abs(after.headOffset-before.headOffset)<=rounding,'Header stays pinned while scrolling: '+detail);
     const visible=Math.min(after.lastBottom,after.frameBottom)-Math.max(after.lastTop,after.headBottom);
     assert(visible>=after.lastHeight-rounding,'Last receipt is visible below the sticky heading: '+detail);
     await fits();
     await p.locator('#back').tap();assert(await p.locator('#bookHistory').isVisible());await p.locator('#back').tap();await p.locator('#bookNext').tap();const id=await p.locator('.record').first().getAttribute('id');await p.locator('#'+id).tap();await fits();await p.locator('#back').tap();assert(await p.locator('#'+id).isVisible());}
    await p.locator('#back').tap();
   }
   await p.locator('#resume').tap();
  }
  await p.close();console.log(width+' px: paged menus, last water, scrollable catch history, journal return, Thai + English');
 }}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
