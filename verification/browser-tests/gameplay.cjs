const {showControl}=require('./menu-controls.cjs');
const {captureReloadStartup,readCheckpoint,reloadFailureText}=require('./reload-trace.cjs');
const {openPersistenceEntry}=require('./persistence-entry.cjs');
const {chromium}=require('playwright-core'),path=require('path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 let entry;
 try{
  entry=await openPersistenceEntry(path.resolve(process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html')));
  const pg=await browser.newPage({viewport:{width:850,height:900}}),errors=[];pg.on('pageerror',e=>errors.push(e.message));
  await pg.addInitScript(()=>{
   const draw=CanvasRenderingContext2D.prototype.drawImage;
   window.specimenFrames=[];
   CanvasRenderingContext2D.prototype.drawImage=function(img,...args){
    if(this.canvas.id==='scene'&&((img instanceof HTMLCanvasElement&&img.width===96&&img.height===50)||(img instanceof HTMLImageElement&&img.naturalWidth===960&&img.naturalHeight===300))){
     if(window.specimenFrames.length<1000)window.specimenFrames.push({phase:g.state(),age:g.age(),x:args.at(-4),y:args.at(-3),w:args.at(-2)});
    }
    return draw.call(this,img,...args);
   };
  });
  await pg.addInitScript(captureReloadStartup);
  await pg.goto(entry.url);
  await pg.waitForFunction(()=>!document.querySelector('#act').disabled,null,{timeout:12000});
  await pg.waitForFunction(()=>document.documentElement.dataset.device);if(await pg.locator('#product').isVisible())await pg.locator('#viewMode').click();
  const menu=async n=>{await pg.locator('#openMenu').click();await pg.locator('[data-to='+n+']').click();};
  await menu('spots');assert.equal(await pg.locator('#places option').count(),117);
  await showControl(pg,'#waterType');await pg.selectOption('#waterType','salt');assert.equal(await pg.locator('#places option').count(),21);
  await showControl(pg,'#places');await pg.selectOption('#places',{label:'Phuket coastal waters'});await showControl(pg,'#period');await pg.selectOption('#period',{label:'Dusk'});await showControl(pg,'#fishHere');await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);
  await pg.waitForFunction(()=>document.querySelector('#spot').textContent==='Phuket coastal waters');
  await pg.waitForFunction(()=>Math.floor(lastLandscape/4)===113*4+2);
  const firstShore=await pg.evaluate(()=>landscapeCanvas.toDataURL());
  await menu('spots');await showControl(pg,'#places');await pg.selectOption('#places',{label:'Krabi coastal waters'});await showControl(pg,'#fishHere');await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);
  await pg.waitForFunction(()=>Math.floor(lastLandscape/4)===114*4+2);
  assert.notEqual(await pg.evaluate(()=>landscapeCanvas.toDataURL()),firstShore,'two places in the same coastal pool show different scenery');
  await menu('spots');await showControl(pg,'#places');await pg.selectOption('#places',{label:'Chao Phraya River'});await showControl(pg,'#period');await pg.selectOption('#period',{label:'Dusk'});await showControl(pg,'#fishHere');await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);
  // Choose a repeatable encounter through the same PRNG and normal cast entry point.
  await pg.evaluate(()=>{for(let seed=1;seed<10000;seed++){g.initialize(seed);g.place(placeId,currentSlot);g.setBait(g.recommendedBait(40));g.advance(16,1,0,0);if(g.species()===40){g.initialize(seed);g.place(placeId,currentSlot);g.setBait(g.recommendedBait(40));break;}}});
  await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===2);
  await pg.locator('#openMenu').click();let age=await pg.evaluate(()=>g.age());await pg.waitForTimeout(500);assert.equal(await pg.evaluate(()=>g.age()),age);await pg.locator('#resume').click();
  await pg.waitForFunction(()=>g.state()===3);await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===4);
  // Follow the on-screen fight cues using the same reel input as the player.
  let winding=false;
  for(let i=0;i<400;i++){
   const [phase,run]=await pg.evaluate(()=>[g.state(),g.surging()]);if(phase!==4)break;
   if(winding===!!run){if(run)await pg.keyboard.up('r');else await pg.keyboard.down('r');winding=!winding;}
   await pg.waitForTimeout(80);
  }
  await pg.keyboard.up('r');assert.equal(await pg.evaluate(()=>g.state()),5,'Reading runs and gathering slack should land the fish');
  assert.match(await pg.locator('#metrics').innerText(),/Rare.*Body length \d+ cm.*Estimated weight \d+ g/i);assert.match(await pg.locator('#origin').innerText(),/claws/);
  await pg.waitForFunction(()=>g.age()>=2600);
  assert.equal(await pg.evaluate(()=>g.caught(40)),0);
  const widths=await pg.evaluate(()=>window.specimenFrames.map(f=>f.w));
  assert(widths.length>1 && widths.every(w=>w===widths[0]),'Specimen stays full size until filed');
  const {observed:heldWeight,trace:beforePendingRestore,startup:beforePendingStartup}=await pg.evaluate(readCheckpoint,{species:40,observe:'weight'});
  try{
   await pg.reload();await pg.waitForFunction(()=>g?.state()===5 && !$('catchContinue').hidden);
   assert.equal(await pg.evaluate(()=>g.caught(40)),0);
   assert.equal(await pg.evaluate(()=>g.grams()),heldWeight,'Pending catch retains its individual weight after reload');
  }catch(error){console.error(await reloadFailureText(pg,{stage:'gameplay-pending',before:beforePendingRestore,beforeStartup:beforePendingStartup,expected:{species:40},pageErrors:errors.length}));throw error;}
  await pg.locator('#catchContinue').click();await pg.waitForFunction(()=>g.state()===0&&!document.querySelector('#menu').open);
  assert.equal(await pg.evaluate(()=>g.caught(40)),1,'Transfer must not count the catch twice');
  await menu('rod');await showControl(pg,'#finish');await pg.selectOption('#finish','Copper');await showControl(pg,'#technique');await pg.selectOption('#technique',{label:'Vertical jig'});await showControl(pg,'#builds button');await pg.locator('#builds button').nth(1).click();assert.equal(await pg.evaluate(()=>g.rank(1)),1);await pg.locator('#resume').click();
  const journalSnapshot=(withStartup=false)=>pg.evaluate(withStartup=>{
   const b=JSON.parse(localStorage.getItem('thai-atlas-v2'));
   return {...(withStartup?{startup:window.__twReloadStartup62}:{}),book:b?.book?.[40],best:g.best(40),ram:g.caught(40),storedFinish:b?.finish,notice:$('summarySave').textContent};
  },withStartup);
  const {startup:beforeFiledStartup,...beforeReload}=await journalSnapshot(true);
  assert.deepEqual(beforeReload.book,[1,beforeReload.best],'Catch must be stored before reload: '+JSON.stringify(beforeReload));
  try{
   await pg.reload();await pg.waitForFunction(()=>!document.querySelector('#act').disabled);
   const afterReload=await journalSnapshot(), evidence=JSON.stringify({beforeReload,afterReload});
   assert.deepEqual(afterReload.book,beforeReload.book,'Reload must retain the exact saved catch: '+evidence);
   assert.equal(afterReload.ram,1,'The replayed journal must contain exactly one catch: '+evidence);
   assert.equal(await pg.evaluate(()=>finish),1);
   assert.equal(await pg.evaluate(()=>g.technique()),2,'Remember the selected presentation');
  }catch(error){
   console.error(await reloadFailureText(pg,{stage:'gameplay-filed',before:{storage:'present',journalMatched:true},
    beforeStartup:beforeFiledStartup,expected:{species:40},pageErrors:errors.length}));throw error;
  }
  await menu('book');assert.equal(await pg.locator('.record').count(),8);await pg.locator('#bookFind').click();await pg.locator('#bookFilter + button').click();await pg.locator('#lcdPicker').getByRole('option',{name:'Mythic',exact:true}).click();await pg.locator('#bookFindDone').click();assert.equal(await pg.locator('.record').count(),5);await pg.locator('#resume').click();
  await pg.setViewportSize({width:390,height:844});await menu('sensors');
   // Replay the same physical rest/lift samples in page time, so locator
   // actionability cannot age out the final sample before either button.
   const calibration=await pg.evaluate(()=>{
    const ownNow=Object.getOwnPropertyDescriptor(performance,'now');
    let sampleTime=performance.now()-128*17;
    Object.defineProperty(performance,'now',{configurable:true,value:()=>sampleTime});
    const feed=([x,y,z])=>{
     for(let i=0;i<64;i++){
      sampleTime+=17;
      onMotion({accelerationIncludingGravity:{x,y,z},rotationRate:{alpha:0,beta:2,gamma:1}});
     }
    };
    try{
     feed([0,0,9.80665]);$('restPose').click();
     const centered=basePose;
     feed([0,6.30,7.51]);
     const ready=!!steady(),span=rodAngle;
     $('liftPose').click();
     return {centered,ready,span,calibrated:calibratedMobile,status:$('motionStatus').textContent};
    }finally{
     if(ownNow)Object.defineProperty(performance,'now',ownNow);else delete performance.now;
    }
   });
   assert(calibration.centered&&calibration.ready&&calibration.calibrated,JSON.stringify(calibration));
   assert.match(calibration.status,/Custom lift saved/);
  await pg.locator('#resume').click();assert.equal(await pg.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  // Use normal touch controls for a complete active presentation of each lure.
  for(const [name,rig] of [['Stop-and-go spoon',1],['Vertical jig',2]]){
   await menu('rod');await showControl(pg,'#technique');await pg.selectOption('#technique',{label:name});await pg.locator('#resume').click();
   await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===2);
   const needed=await pg.evaluate(()=>g.strokesNeeded());
   for(let i=0;i<needed;i++){
    for(let n=0;n<(rig===1?3:1);n++)await pg.locator('#act').click();
    if(i+1<needed)await pg.waitForFunction(i=>g.strokes()>i,i);
   }
   await pg.waitForFunction(()=>g.state()===3);await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===4);
   // Travel through the normal menu to abandon this cast before selecting the next rig.
   await menu('spots');await showControl(pg,'#places');await pg.selectOption('#places',{index:rig+3});await showControl(pg,'#fishHere');await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);await pg.waitForFunction(()=>g.state()===0);
  }
  const fights=await pg.evaluate(()=>{
   const curve=ctx.quadraticCurveTo,shots=[];
   let tip;
   ctx.quadraticCurveTo=function(cx,cy,x,y){tip=[x,y];return curve.call(this,cx,cy,x,y);};
   try{
    for(const [species,pool,time] of [[40,1,2],[41,3,3],[47,4,1]]){
     let found=false;
     for(let seed=1;seed<12000&&!found;seed++){
      g.initialize(seed);g.visit(pool,time);g.setBait(g.recommendedBait(species));g.advance(16,1,0,0);found=g.species()===species;
     }
     if(!found)throw Error('Fixture species unavailable');
     g.advance(g.flightMs(),0,0,0);g.advance(6500,0,0,0);g.advance(20,0,1,0);
     draw();shots.push({phase:g.state(),hint:$('message').textContent,tip});
    }
   }finally{ctx.quadraticCurveTo=curve;}
   return shots;
  });
  assert(fights.every(s=>s.phase===4));
  assert.match(fights[0].hint,/wind gently/);assert.match(fights[1].hint,/Holding bottom/);assert.match(fights[2].hint,/Fast run/);
  assert(fights[1].tip[1]>fights[0].tip[1]+20,'The planted ray should visibly bend the rod more than the picking prawn.');
  const card=await pg.evaluate(async()=>{
   await document.fonts.ready;
   const drawText=ctx.fillText,drawSprite=ctx.drawImage,problems=[],positions=new Set();
   const footer=L(catchContinueLabel);
   let footerCount=0;
   let leftmost=480,rightmost=0,lowest=0;
   try{
    ctx.fillText=function(text,x,y){
     if(text===footer){
      footerCount++;
      const half=ctx.measureText(text).width/2;
      if(ctx.textAlign!=='center'||x!==240||y!==310||x-half<12||x+half>468)problems.push([text,x,y,x-half,x+half]);
      return;
     }
     const right=x+ctx.measureText(text).width;
     leftmost=Math.min(leftmost,x);rightmost=Math.max(rightmost,right);lowest=Math.max(lowest,y);
     if(x<200 || right>468 || y>286 || y<72)problems.push([text,x,y,right]);
    };
    ctx.drawImage=function(img,...args){if(img===fishSheet||img===portraitCache.get(g.species()))positions.add(JSON.stringify(args.slice(-4)));};
    for(let id=0;id<atlas.fish.length;id++){
     g.restoreCatch(id,atlas.fish[id].high);
     for(placeId=0;placeId<atlas.locations.length;placeId++)landedCatch(0);
    }
   }finally{ctx.fillText=drawText;ctx.drawImage=drawSprite;placeId=0;}
   g.restoreEntry(41,3,240);g.restoreCatch(41,240);draw();
   return {problems:problems.slice(0,5),positions:[...positions],
    layouts:atlas.fish.length*atlas.locations.length,footerCount,leftmost,rightmost,lowest,legacy:[g.best(41),g.grams(),$('metrics').textContent]};
  });
  assert.deepEqual(card.problems,[],'All species and water names and the centered action fit the catch card');
  assert.equal(card.footerCount,card.layouts,'Every catch layout draws its action once');
  assert.deepEqual(card.positions,['[11,112,178,93]'],'All fish retain their full size in the left column');
  assert.equal(card.legacy[0],240);assert.equal(card.legacy[1],0);assert.match(card.legacy[2],/Recorded size.*Unweighed/);
  console.log('PASS '+card.layouts+' catch card layouts; right edge '+card.rightmost.toFixed(1)+' px, last baseline '+card.lowest+' px.');
  assert.equal(errors.length,0,errors.join(';'));console.log('PASS location, catch, collection, mobile motion and distinct loaded-rod visuals for prawn, ray and runner.');
 }finally{try{await browser.close();}finally{await entry?.close();}}
})().catch(e=>{console.error(e);process.exitCode=1;});


