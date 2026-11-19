const {chromium}=require('playwright-core');
const {spawn}=require('node:child_process');
const {once}=require('node:events');
const {randomInt}=require('node:crypto');
const {resolve}=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const port=randomInt(24000,30000),base='http://127.0.0.1:'+port;
 const server=spawn(process.execPath,[resolve(__dirname,'../../game/lan/server.mjs')],{env:{...process.env,TW_HOST:'127.0.0.1',TW_BIND:'127.0.0.1',TW_PORT:String(port),TW_UDP_PORT:String(port+1),TW_CUP_DB:':memory:',TW_CERT:'',TW_KEY:''}});
 let browser;
 try{
  await Promise.race([once(server.stdout,'data'),once(server,'exit').then(()=>{throw Error('LAN host exited')})]);
  const invitation=(await (await fetch(base+'/pair')).text()).match(/href="([^"]+)"/)[1];
  browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
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
