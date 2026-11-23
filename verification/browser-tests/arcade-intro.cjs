'use strict';
const assert=require('node:assert/strict');
const path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const url=pathToFileURL(path.resolve(process.env.PLAYTEST_HTML||path.join(__dirname,'../../game/Thai-Waters-play.html'))).href;
async function verifyArcadeIntro(browser,urlToTest=url){
  const desktop=await browser.newPage({viewport:{width:900,height:650}});
  await desktop.goto(urlToTest);
  const start=desktop.locator('#bootStart'),skip=desktop.locator('#skipArcade'),play=desktop.locator('#bootResume'),menu=desktop.locator('#menu');
  const snapshot=()=>desktop.evaluate(()=>({
   raw:localStorage.getItem('thai-atlas-v2'),place:placeId,
   phase:g.state(),working:audio!==null,allLocked:['dial','act','catchContinue','joinCrew'].every(id=>$(id).disabled)
  }));
  await start.waitFor({state:'visible'});
  assert(await desktop.locator('#startupRecovery').isHidden());
  assert.equal(await desktop.evaluate(()=>arcadeContext),null,'no audio context before the first gesture');
  const initial=await snapshot();
  assert.equal(initial.allLocked,true);
  await desktop.locator('#menu[data-arcade-phase=title]').waitFor({state:'visible'});
  // Witness one full real pulse before input. A moving touch target can reject
  // a genuine tap even when the text appears visually centered throughout.
  const hitbox=await start.evaluate(async node=>{
   await document.fonts.ready;
   const pulse=node.getAnimations().find(a=>a.animationName==='arcade-start-beat');
   if(!pulse)throw Error('Expected a real Start invitation pulse');
   const duration=pulse.effect.getComputedTiming().duration;
   const begin=performance.now(),first=node.getBoundingClientRect();
   let maxMove=0,minOpacity=1,maxOpacity=0,frames=0;
   do{
    await new Promise(requestAnimationFrame);
    const rect=node.getBoundingClientRect(),opacity=Number(getComputedStyle(node).opacity);
    for(const key of ['x','y','width','height'])maxMove=Math.max(maxMove,Math.abs(rect[key]-first[key]));
    minOpacity=Math.min(minOpacity,opacity);maxOpacity=Math.max(maxOpacity,opacity);frames++;
   }while(performance.now()-begin<duration);
   return {duration,maxMove,minOpacity,maxOpacity,frames};
  });
  assert(hitbox.duration>=2500&&hitbox.frames>8,'must observe a complete rendered invitation cycle');
  assert(hitbox.maxMove<=.1,JSON.stringify(hitbox));
  assert(hitbox.maxOpacity-hitbox.minOpacity>=.35,'the stronger pulse must remain visually distinct');
  const first=await desktop.evaluate(()=>$('scene').getContext('2d').getImageData(60,214,360,17).data.reduce((a,x,i)=>(Math.imul(a,31)+x+i)|0,0));
  await desktop.waitForFunction(hash=>$('scene').getContext('2d').getImageData(60,214,360,17).data.reduce((a,x,i)=>(Math.imul(a,31)+x+i)|0,0)!==hash,first);
  await desktop.locator('#titleAudio').click();
  await desktop.waitForFunction(()=>arcadeAudio.active);
  await desktop.locator('#titleAudio').press('Enter');
  await desktop.waitForFunction(()=>!arcadeAudio.active);
  await start.press('Enter');
  assert.equal(await menu.getAttribute('data-arcade-phase'),'launch');
  assert(await skip.isVisible());
  assert(await play.isHidden());
  assert.equal(await desktop.evaluate(()=>arcadeAudio.active),false,'explicit title mute also mutes the launch');
  assert.deepEqual(await snapshot(),initial,'title launch leaves career, engine and fishing input unchanged');
  await desktop.keyboard.press('Escape');
  assert.equal(await menu.getAttribute('data-arcade-phase'),'modes');
  assert(await play.isVisible());
  assert.deepEqual(await snapshot(),initial);
  await desktop.locator('#titleAudio').click();
  await desktop.waitForFunction(()=>arcadeAudio.active);
  await desktop.locator('#bootRoutes [data-to=boot-settings]').click();
  await desktop.waitForFunction(()=>!arcadeAudio.active);
  await desktop.locator('#back').click();await play.click();
  assert.equal(await desktop.locator('#act').isEnabled(),true);
  assert.equal(await desktop.evaluate(()=>audio===null&&!arcadeAudio.active),true,'gameplay still does not start sound or overlap title');
  await desktop.close();
  const phone=await browser.newPage({viewport:{width:844,height:390},hasTouch:true,isMobile:true,reducedMotion:'reduce'});
  await phone.goto(urlToTest);
  await phone.locator('#bootStart').tap();
  assert.equal(await phone.locator('#menu').getAttribute('data-arcade-phase'),'modes');
  assert(await phone.locator('#skipArcade').isHidden());
  await phone.waitForFunction(()=>arcadeAudio.active); // first real tap also opts in, without the speaker toggle
  await phone.locator('#simPower').tap();
  assert.equal(await phone.evaluate(()=>!powered&&!arcadeAudio.active),true);
  await phone.locator('#simPower').tap();
  assert.equal(await phone.locator('#menu').getAttribute('data-arcade-phase'),'title');
  assert.equal(await phone.evaluate(()=>!arcadeAudio.active&&$('act').disabled),true,'wake never autoplays');
  await phone.close();
  console.log('PASS canonical browser: moving pixels, trusted title audio, mute, launch, Escape skip, exact save and locks, settings/game exits, reduced-motion touch and power.');
}
module.exports={verifyArcadeIntro};
if(require.main===module)(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||chromium.executablePath()});
 try{await verifyArcadeIntro(browser);}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
