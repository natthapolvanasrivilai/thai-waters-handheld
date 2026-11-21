const {chromium}=require('playwright-core');
const {spawn}=require('node:child_process');
const {once}=require('node:events');
const {randomInt}=require('node:crypto');
const {resolve}=require('node:path');
const {setTimeout:delay}=require('node:timers/promises');
const assert=require('node:assert/strict');

async function openCup(page,touch){
 const click=selector=>touch?page.locator(selector).tap():page.locator(selector).click();
 await click('#openMenu');
 await click('[data-to=crew]');
 return click;
}
// Poll from Node so startup checks remain live while the test's animation clock is paused.
async function waitForTargetState(page,ready,label){
 for(let i=0;i<200;i++){
  if(await page.evaluate(ready))return;
  await delay(50);
 }
 throw Error('Timed out waiting for '+label);
}
async function checkTarget(page,url,touch,language){
 const reports=[],goal={day:20778,spot:96,species:45,minimum:28,maximum:42};
 await page.clock.install({time:new Date('2026-11-21T04:00:00Z')});
 await page.addInitScript(kind=>{localStorage.setItem('thai-waters-language',kind);},language);
 await page.route('**/event/cup', async route=>{
  reports.push(route.request().postDataJSON().action);
  await route.fulfill({json:{goal,joined:false,best:0,rank:0,leaders:[]}});
 });
 const errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 const ready=()=>!$('act').disabled;
 await page.goto(url);await waitForTargetState(page,ready,'game init');
 const click=await openCup(page,touch);
 await waitForTargetState(page,()=>cupBoard?.goal?.species===45,'fixed cup board');
 await page.evaluate(()=>document.fonts.ready);
 const label=language==='th'?/ขั้นต่ำที่เข้าเกณฑ์: 28 ซม. · ความยาวทั้งหมด/:/Qualifying minimum: 28 cm · Total length/;
 assert.equal(await page.locator('#cupGoal').innerText(),language==='th'?'ปลาอีคุด':'Goldlined seabream');
 assert.match(await page.locator('#cupTargetSize').innerText(),label);
 assert.match(await page.locator('#cupLocation').innerText(),language==='th'?/ชายฝั่งตราด/:/Trat coastal waters/);
 assert.match(await page.locator('#cupLoadout').innerText(),language==='th'?/หมึกหั่นเส้น · หน้าดิน/:/Vertical jig · Squid strip · Bottom/);
 assert.equal(await page.locator('#cupRulerMark').evaluate(node=>node.style.left),'70%');
 assert.deepEqual(await page.locator('#cupRulerLabels span').allTextContents(),['0','10','20','30',language==='th'?'40 ซม.':'40 cm']);
 const art=await page.locator('#cupPortrait').evaluate(canvas=>{
  const brush=canvas.getContext('2d'),drawn=brush.getImageData(0,0,canvas.width,canvas.height).data;
  const ref=document.createElement('canvas');ref.width=canvas.width;ref.height=canvas.height;
  const ctx=ref.getContext('2d');ctx.imageSmoothingEnabled=false;
  drawSpecimen(ctx,45,0,0,ref.width,ref.height);
  const source=ctx.getImageData(0,0,ref.width,ref.height).data;
  return {id:canvas.dataset.species,visible:drawn.some((value,i)=>i%4===3&&value>0),same:drawn.every((value,i)=>value===source[i])};
 });
 assert.deepEqual(art,{id:'45',visible:true,same:true});
 const ruler=await page.evaluate(()=>{
  const lcd=$('lcdUI'),prior=lcd.style.transform,native=document.createElement('canvas');
  native.width=480;native.height=320;
  const brush=native.getContext('2d');let rect,origin,mark;
  try{
   lcd.style.transform='none';origin=lcd.getBoundingClientRect();
   rect=$('cupRulerTicks').getBoundingClientRect();
   mark=$('cupRulerMark').getBoundingClientRect();
   paintLcdInterface(brush);
  }finally{lcd.style.transform=prior;}
  const line=brush.getImageData(Math.ceil(rect.left-origin.left),Math.ceil(rect.top-origin.top)+7,Math.floor(rect.width)-1,1).data;
  const count=rgb=>Array.from({length:line.length/4},(_,i)=>+(rgb.every((v,n)=>Math.abs(line[4*i+n]-v)<=2))).reduce((a,b)=>a+b,0);
  const marker=brush.getImageData(Math.round(mark.left-origin.left+mark.width/2),Math.ceil(rect.top-origin.top)+5,1,1).data;
  return {ticks:count([105,73,37])+count([154,118,63]),tape:count([244,214,140]),marker:[...marker]};
 });
 assert(ruler.ticks>=10&&ruler.tape>=100,JSON.stringify(ruler));
 assert.deepEqual(ruler.marker,[120,61,35,255]);

 const layout=await page.evaluate(()=>{
  const bounds=id=>$(id).getBoundingClientRect(),panel=$('cupTravel').closest('section').getBoundingClientRect();
  const visible=id=>{const r=bounds(id);return r.height>0&&r.left>=panel.left&&r.top>=panel.top&&r.right<=panel.right&&r.bottom<=panel.bottom};
  return {lcd:[$('lcdUI').offsetWidth,$('lcdUI').offsetHeight],fit:['cupTarget','cupLocation','cupLoadout','cupTravel','cupJoin','cupMine'].every(visible),touch:bounds('cupTravel').height};
 });
 assert.deepEqual(layout.lcd,[480,320]);assert(layout.fit,JSON.stringify(layout));
 if(touch)assert(layout.touch>=44,JSON.stringify(layout));
 const safeState=()=>page.evaluate(()=>[placeId,g.technique(),g.baitChoice(),g.state(),g.pts(),g.caught(45),enteredCup,menu.open]);
 const baseline=await safeState();
 assert.notEqual(baseline[0],96);
 const equipped=[96,2,17,0,baseline[4],baseline[5],0,false];
 // Freeze the game animation just for the real Skip tap. The arrival cannot
 // finish on its own while a busy Chromium handles browser input.
 await page.clock.pauseAt(new Date('2026-11-21T05:00:00Z'));
 await click('#cupTravel');
 assert.deepEqual(await safeState(),equipped);
 assert.equal(await page.locator('#arrivalSkip').isVisible(),true);
 await click('#arrivalSkip');
 assert.equal(await page.evaluate(()=>arrivalSince),null);
 await openCup(page,touch);
 await page.evaluate(()=>{g.setTechnique(0);g.setBait(0);});
 await click('#cupTravel');
 assert.deepEqual(await safeState(),equipped);
 assert.equal(await page.evaluate(()=>arrivalSince),null);
 assert.equal(await page.locator('#arrivalSkip').isVisible(),false);
 // Check actual storage before reload, then let a new page restore the same tackle.
 assert.deepEqual(await page.evaluate(()=>{const save=careerVault().load();return [save.place,save.rig,save.bait,save.pending];}),[96,2,17,null]);
 await page.clock.resume();
 await page.reload();await waitForTargetState(page,ready,'post-reload game init');
 assert.deepEqual(await safeState(),equipped);
 await page.evaluate(()=>g.advance(16,true,false,0));
 await openCup(page,touch);assert.equal(await page.locator('#cupTravel').isDisabled(),true);
 const active=await safeState();assert(active[3]===1||active[3]===2);
 await page.evaluate(()=>$('cupTravel').onclick());
 assert.deepEqual(await safeState(),active);
 await page.evaluate(()=>{g.travel(4);g.place(placeId,currentSlot);g.restoreCatch(45,28);drawCup();});
 assert.equal(await page.locator('#cupTravel').isDisabled(),true);
 await page.evaluate(()=>$('cupTravel').onclick());
 assert.deepEqual(await page.evaluate(()=>[g.state(),g.lengthCm(),g.filed(),g.caught(45),menu.open]),[5,28,0,baseline[5],true]);
 assert(reports.length>0&&reports.every(action=>action==='view'));
 assert.deepEqual(errors,[]);
 console.log('PASS Daily Cup target, metric, artwork, ruler, touch/layout, travel & skip, safe guards and reload: '+language+(touch?' mobile':' desktop'));
}
(async()=>{
 const port=randomInt(24000,30000),base='http://127.0.0.1:'+port;
 const server=spawn(process.execPath,[resolve(__dirname,'../../game/lan/server.mjs')],{env:{...process.env,TW_HOST:'127.0.0.1',TW_BIND:'127.0.0.1',TW_PORT:String(port),TW_UDP_PORT:String(port+1),TW_CUP_DB:':memory:',TW_CERT:'',TW_KEY:''}});
 let browser;
 try{
  await Promise.race([once(server.stdout,'data'),once(server,'exit').then(()=>{throw Error('LAN host exited')})]);
  const invitation=(await (await fetch(base+'/pair')).text()).match(/href="([^"]+)"/)[1];
  browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  for(const [touch,language] of [[true,'th'],[false,'en']]){
   const context=await browser.newContext({viewport:touch?{width:390,height:844}:{width:1280,height:800},isMobile:touch,hasTouch:touch});
   const page=await context.newPage();
   try{await checkTarget(page,invitation,touch,language);}finally{await context.close();}
  }
  const players=[];
  for(let i=0;i<2;i++){
   const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
   const page=await context.newPage();players.push(page);
   await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await page.goto(invitation);await page.waitForFunction(()=>!$('act').disabled);
   await page.locator('#openMenu').tap();await page.locator('[data-to=crew]').tap();
   await page.waitForFunction(()=>!!cupBoard);
   await page.locator('#cupJoin').tap();await page.waitForFunction(()=>enteredCup===cupBoard.goal.day);
   await page.locator('#cupTravel').tap();
   await page.waitForFunction(()=>arrivalSince===null);
   // Resume a held specimen, as after a phone reload, and use the real touch filing path.
   await page.evaluate(bonus=>{const goal=cupBoard.goal;g.restoreCatch(goal.species,goal.minimum+bonus);pendingDay=goal.day;save();},i);
   await page.waitForFunction(()=>!$('catchContinue').hidden);
   assert.equal(await page.evaluate(()=>g.caught(g.species())),0);
   await page.locator('#catchContinue').tap();await page.waitForFunction(()=>cupBoard.best>0&&g.state()===0);
   assert.equal(await page.evaluate(()=>g.caught(g.species())),1);
  }
  const first=players[0];await first.locator('#openMenu').tap();await first.locator('[data-to=crew]').tap();
  await first.waitForFunction(()=>cupBoard.rank===2 && cupBoard.leaders.length===2);
  assert.match(await first.locator('#cupMine').textContent(),/rank #2/);
  assert.equal(await first.locator('#cupLeaders div').count(),2);
  console.log('PASS two phone profiles joined the daily goal, travelled, filed once, and displayed both ranks on the LCD.');
 }finally{await browser?.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
