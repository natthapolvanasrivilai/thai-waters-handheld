const {chromium}=require('playwright-core'),{pathToFileURL}=require('url'),path=require('path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 try{
  const pg=await browser.newPage({viewport:{width:850,height:900}}),errors=[];pg.on('pageerror',e=>errors.push(e.message));
  await pg.addInitScript(()=>{
   const draw=CanvasRenderingContext2D.prototype.drawImage;
   window.specimenFrames=[];
   CanvasRenderingContext2D.prototype.drawImage=function(img,...args){
    if(this.canvas.id==='scene'&&img instanceof HTMLImageElement&&img.naturalWidth===960&&img.naturalHeight===400){
     if(window.specimenFrames.length<1000)window.specimenFrames.push({phase:g.state(),age:g.age(),x:args[4],y:args[5],w:args[6]});
    }
    return draw.call(this,img,...args);
   };
  });
  await pg.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await pg.goto(pathToFileURL(path.resolve(process.argv[2]||path.join(__dirname,'../../game/Thai-Waters-play.html'))).href);
  await pg.waitForFunction(()=>!document.querySelector('#act').disabled,null,{timeout:12000});
  await pg.waitForFunction(()=>document.documentElement.dataset.device);if(await pg.locator('#product').isVisible())await pg.locator('#viewMode').click();
  const menu=async n=>{await pg.locator('#openMenu').click();await pg.locator('[data-to='+n+']').click();};
  await menu('spots');assert.equal(await pg.locator('#places option').count(),117);
  await pg.selectOption('#waterType','salt');assert.equal(await pg.locator('#places option').count(),21);
  await pg.selectOption('#places',{label:'Phuket coastal waters'});await pg.selectOption('#period',{label:'Dusk'});await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);
  await pg.waitForFunction(()=>document.querySelector('#spot').textContent==='Phuket coastal waters');
  await pg.waitForFunction(()=>Math.floor(lastLandscape/4)===113*4+2);
  const firstShore=await pg.evaluate(()=>landscapeCanvas.toDataURL());
  await menu('spots');await pg.selectOption('#places',{label:'Krabi coastal waters'});await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);
  await pg.waitForFunction(()=>Math.floor(lastLandscape/4)===114*4+2);
  assert.notEqual(await pg.evaluate(()=>landscapeCanvas.toDataURL()),firstShore,'two places in the same coastal pool show different scenery');
  await menu('spots');await pg.selectOption('#places',{label:'Chao Phraya River'});await pg.selectOption('#period',{label:'Dusk'});await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);
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
  const heldWeight=await pg.evaluate(()=>g.grams());
  await pg.reload();await pg.waitForFunction(()=>g?.state()===5 && !$('catchContinue').hidden);
  assert.equal(await pg.evaluate(()=>g.caught(40)),0);
  assert.equal(await pg.evaluate(()=>g.grams()),heldWeight,'Pending catch retains its individual weight after reload');
  await pg.locator('#catchContinue').click();await pg.waitForFunction(()=>g.state()===0&&!document.querySelector('#menu').open);
  assert.equal(await pg.evaluate(()=>g.caught(40)),1,'Transfer must not count the catch twice');
  await menu('rod');await pg.selectOption('#finish','Copper');await pg.selectOption('#technique',{label:'Vertical jig'});await pg.locator('#builds button').nth(1).click();assert.equal(await pg.evaluate(()=>g.rank(1)),1);await pg.locator('#resume').click();
  await pg.reload();await pg.waitForFunction(()=>!document.querySelector('#act').disabled);assert.equal(await pg.evaluate(()=>g.caught(40)),1);assert.equal(await pg.evaluate(()=>finish),1);
  assert.equal(await pg.evaluate(()=>g.technique()),2,'Remember the selected presentation');
  await menu('book');assert.equal(await pg.locator('.record').count(),8);await pg.locator('#bookFilter').selectOption({label:'Mythic'});assert.equal(await pg.locator('.record').count(),5);await pg.locator('#resume').click();
  await pg.setViewportSize({width:390,height:844});await menu('sensors');
  // Gravity in m/s², rest / raised vectors and stable dwell.
  for(const [xyz,button] of [[[0,0,9.80665],'restPose'],[[0,6.30,7.51],'liftPose']]){
   await pg.evaluate(async xyz=>{for(let i=0;i<64;i++){onMotion({accelerationIncludingGravity:{x:xyz[0],y:xyz[1],z:xyz[2]},rotationRate:{alpha:0,beta:2,gamma:1}});await new Promise(r=>setTimeout(r,17));}},xyz);
   await pg.locator('#'+button).click();
  }
  assert.equal(await pg.evaluate(()=>calibratedMobile),true);
  await pg.locator('#resume').click();assert.equal(await pg.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  // Use normal touch controls for a complete active presentation of each lure.
  for(const [name,rig] of [['Stop-and-go spoon',1],['Vertical jig',2]]){
   await menu('rod');await pg.selectOption('#technique',{label:name});await pg.locator('#resume').click();
   await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===2);
   const needed=await pg.evaluate(()=>g.strokesNeeded());
   for(let i=0;i<needed;i++){
    for(let n=0;n<(rig===1?3:1);n++)await pg.locator('#act').click();
    if(i+1<needed)await pg.waitForFunction(i=>g.strokes()>i,i);
   }
   await pg.waitForFunction(()=>g.state()===3);await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===4);
   // Travel through the normal menu to abandon this cast before selecting the next rig.
   await menu('spots');await pg.selectOption('#places',{index:rig+3});await pg.locator('#fishHere').click();await pg.waitForFunction(()=>arrivalSince===null);await pg.waitForFunction(()=>g.state()===0);
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
     g.advance(651,0,0,0);g.advance(6500,0,0,0);g.advance(20,0,1,0);
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
   const drawText=ctx.fillText,drawSprite=ctx.drawImage,problems=[],positions=[];
   let leftmost=480,rightmost=0,lowest=0;
   try{
    ctx.fillText=function(text,x,y){
     if(text==='Tap to continue'){if(x!==240||y!==310)problems.push([text,x,y]);return;}
     const right=x+ctx.measureText(text).width;
     leftmost=Math.min(leftmost,x);rightmost=Math.max(rightmost,right);lowest=Math.max(lowest,y);
     if(x<200 || right>468 || y>286 || y<72)problems.push([text,x,y,right]);
    };
    ctx.drawImage=function(img,...args){if(img===fishSheet)positions.push([args[4],args[5],args[6],args[7]]);};
    for(let id=0;id<atlas.fish.length;id++){
     g.restoreCatch(id,atlas.fish[id].high);
     for(placeId=0;placeId<atlas.locations.length;placeId++)landedCatch(0);
    }
   }finally{ctx.fillText=drawText;ctx.drawImage=drawSprite;placeId=0;}
   g.restoreEntry(41,3,240);g.restoreCatch(41,240);draw();
   return {problems:problems.slice(0,5),positions:[...new Set(positions.map(JSON.stringify))],
    leftmost,rightmost,lowest,legacy:[g.best(41),g.grams(),$('metrics').textContent]};
  });
  assert.deepEqual(card.problems,[],'All 52 species and 117 waters fit the right column above the action button');
  assert.deepEqual(card.positions,['[11,112,178,93]'],'All fish retain their full size in the left column');
  assert.equal(card.legacy[0],240);assert.equal(card.legacy[1],0);assert.match(card.legacy[2],/Recorded size.*Unweighed/);
  console.log('PASS 6,084 catch card layouts; right edge '+card.rightmost.toFixed(1)+' px, last baseline '+card.lowest+' px.');
  assert.equal(errors.length,0,errors.join(';'));console.log('PASS location, catch, collection, mobile motion and distinct loaded-rod visuals for prawn, ray and runner.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});


