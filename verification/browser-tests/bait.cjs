const {showControl}=require('./menu-controls.cjs');
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');

(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 try{
  const p=await browser.newPage({viewport:{width:900,height:680}});
  const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(()=>{
   // Stable session seed. Every travel, bait setting, cast and hook uses the player's controls.
   Date.now=()=>416*4294967296+7;
   window.motor=[];Object.defineProperty(navigator,'vibrate',{value:v=>(motor.push(v),true)});
  });
  const url=pathToFileURL(path.resolve(process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html'))).href;
  const ready=()=>p.waitForFunction(()=>document.querySelector('#act')?.disabled===false);
  const open=async section=>{await p.locator('#openMenu').click();await p.locator('[data-to='+section+']').click();};
  const travel=async(index,time)=>{await open('spots');await showControl(p,'#places');await p.selectOption('#places',{index});await showControl(p,'#period');await p.selectOption('#period',{label:time});await showControl(p,'#fishHere');await p.locator('#fishHere').click();};
  const equip=async (food,depth)=>{await open('rod');await showControl(p,'#hookBait');await p.selectOption('#hookBait',{label:food});await showControl(p,'#baitDepth');await p.selectOption('#baitDepth',{label:depth});await p.locator('#resume').click();};
  await p.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await p.goto(url);await ready();
  await travel(0,'Dawn');await equip('Live baitfish','Surface');
  await p.locator('#act').click();await p.waitForFunction(()=>g.state()===2);
  assert.deepEqual(await p.evaluate(()=>[g.noStock(),g.lengthCm(),g.teasing()]),[1,0,0]);
  await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('Quiet water'));
  await open('rod');assert(await p.locator('#hookBait').isDisabled());await p.locator('#resume').click();
  await p.waitForFunction(()=>g.state()===6);
  assert.match(await p.locator('#message').innerText(),/No bites.*bait and depth/);
  assert.deepEqual(await p.evaluate(()=>[g.reason(),g.catches(),g.pts(),g.fileCatch(),motor.some(p=>Array.isArray(p)&&p.length)]),[6,0,0,0,false]);
  await travel(1,'Dusk');await open('book');await p.evaluate(()=>{bookOffset=Math.floor(40/bookSize);renderBook();});
  await p.locator('#species-40').click();
  assert.match(await p.locator('#bookDetail').innerText(),/Raw shrimp.*Bottom/i);
  assert.equal(await p.locator('#bookDetail [aria-label=Dusk]').count(),1);
  await p.locator('#resume').click();
  await equip('Raw shrimp','Surface');
  assert.deepEqual(await p.evaluate(()=>[g.baitChoice(),g.baitScore(40,g.baitChoice())]),[1,0]);
  await equip('Raw shrimp','Bottom');await p.reload();await ready();
  await open('rod');assert.equal(await p.locator('#hookBait').inputValue(),'Raw shrimp');assert.equal(await p.locator('#baitDepth').inputValue(),'Bottom');
  assert.equal(await p.evaluate(()=>JSON.parse(localStorage.getItem('thai-atlas-v2')).bait),13);
  await p.locator('#resume').click();
  await p.evaluate(()=>{
   window.prawnHook=new Promise((resolve,reject)=>{
    let waiting,bite,done=false,timeout;
    const step=()=>{
     if(done)return;
     const phase=g.state();
     if(phase===2&&!waiting)waiting=[g.noStock(),g.species(),g.baitChoice()];
     if(phase===3&&bite===undefined){bite=g.age();$('act').click();}
     if(phase===4||phase===6){
      done=true;clearTimeout(timeout);resolve({waiting,bite,phase,reason:g.reason()});return;
     }
     requestAnimationFrame(step);
    };
    // Strike in the live game's render loop rather than making a driver
    // round trip during the prawn's short bite window.
    $('act').addEventListener('click',()=>{
     timeout=setTimeout(()=>{done=true;reject(new Error('Prawn did not hook; state='+g.state()+', reason='+g.reason()));},30000);
     requestAnimationFrame(step);
    },{once:true});
   });
   window.prawnHook.catch(()=>{});
  });
  await p.locator('#act').click();
  const hooked=await p.evaluate(()=>window.prawnHook);
  assert.deepEqual(hooked.waiting,[0,40,13]);
  assert(Number.isInteger(hooked.bite)&&hooked.bite>=0&&hooked.bite<=820,JSON.stringify(hooked));
  assert.equal(hooked.phase,4,JSON.stringify(hooked));
  assert.equal(await p.evaluate(()=>g.caught(40)),0);assert.deepEqual(errors,[]);
  console.log('PASS workshop bait and depth, journal clue, reload persistence, incompatible empty cast with no cue or credit, bottom shrimp hooks a dusk prawn.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
