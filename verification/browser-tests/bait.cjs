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
  const travel=async(index,time)=>{
   await open('spots');await showControl(p,'#places');await p.selectOption('#places',{index});
   const destination=Number(await p.locator('#places').inputValue());
   await showControl(p,'#period');await p.selectOption('#period',{label:time});
   await showControl(p,'#fishHere');await p.locator('#fishHere').click();
   // Arrival animation itself has a dedicated test. Use its normal Skip
   // control here so ambient renderer speed cannot change the bait fixture.
   assert.deepEqual(await p.evaluate(()=>{
    const skip=$('arrivalSkip');if(!skip.hidden)skip.click();
    return [arrivalSince===null,!menu.open,placeId,currentSlot,g.state()];
   }),[true,true,destination,['Dawn','Day','Dusk','Night'].indexOf(time),0]);
  };
  const equip=async (food,depth)=>{await open('rod');await showControl(p,'#hookBait');await p.selectOption('#hookBait',{label:food});await showControl(p,'#baitDepth');await p.selectOption('#baitDepth',{label:depth});await p.locator('#resume').click();};
  async function replayCast(empty){
   await p.evaluate(empty=>{
    window.baitProbe=new Promise((resolve,reject)=>{
     $('act').addEventListener('click',()=>queueMicrotask(()=>{
      // Use the live frame callback with bounded deterministic steps.
      // Leave the existing browser frame queued while testing these transitions.
      const schedule=window.requestAnimationFrame;
      window.requestAnimationFrame=()=>0;
      const advance=phase=>{
       for(let i=0;i<160&&g.state()!==phase;i++){
        if(g.state()===6)break;
        frame(prev+80);
       }
       if(g.state()!==phase)throw Error(`Expected phase ${phase}; got ${g.state()}, age ${g.age()}, reason ${g.reason()}, menu ${menu.open}`);
      };
      try{
       if(document.hidden||menu.open||arrivalSince!==null)throw Error('Cannot start cast while game is paused');
       advance(2);
       if(empty){
        const waiting=[g.noStock(),g.lengthCm(),g.teasing()],quiet=$('message').textContent;
        $('openMenu').click();menu.querySelector('[data-to=rod]').click();
        const disabled=menu.open&&$('hookBait').disabled;
        const age=g.age();frame(prev+80);const paused=menu.open&&g.age()===age;
        $('resume').click();
        if(menu.open)throw Error('Rod workshop did not resume');
        advance(6);
        resolve({waiting,quiet,disabled,paused,message:$('message').textContent,
         lost:[g.reason(),g.catches(),g.pts(),g.fileCatch(),motor.some(v=>Array.isArray(v)&&v.length)]});
       }else{
        const waiting=[g.noStock(),g.species(),g.baitChoice()];
        advance(3);const bite=g.age();
        $('act').click();advance(4);
        resolve({waiting,bite,phase:g.state(),caught:g.caught(40)});
       }
      }catch(error){reject(error);}
      finally{window.requestAnimationFrame=schedule;prev=performance.now();}
     }),{once:true});
    });
    window.baitProbe.catch(()=>{});
   },empty);
   await p.locator('#act').click();
   return p.evaluate(()=>window.baitProbe);
  }
  await p.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await p.goto(url);await ready();
  await travel(0,'Dawn');await equip('Live baitfish','Surface');
  const empty=await replayCast(true);
  assert.deepEqual(empty.waiting,[1,0,0]);
  assert.match(empty.quiet,/Quiet water/);
  assert(empty.disabled,'Equipment is disabled during an active cast');
  assert(empty.paused,'Opening the workshop pauses the active cast');
  assert.match(empty.message,/No bites.*bait and depth/);
  assert.deepEqual(empty.lost,[6,0,0,0,false]);
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
  const hooked=await replayCast(false);
  assert.deepEqual(hooked.waiting,[0,40,13]);
  assert(Number.isInteger(hooked.bite)&&hooked.bite>=0&&hooked.bite<=820,JSON.stringify(hooked));
  assert.equal(hooked.phase,4,JSON.stringify(hooked));
  assert.equal(hooked.caught,0);assert.deepEqual(errors,[]);
  console.log('PASS workshop bait and depth, journal clue, reload persistence, incompatible empty cast with no cue or credit, bottom shrimp hooks a dusk prawn.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
