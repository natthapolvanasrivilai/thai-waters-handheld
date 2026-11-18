const {chromium}=require('playwright-core'),{pathToFileURL}=require('url'),path=require('path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 try{
  const pg=await browser.newPage({viewport:{width:850,height:900}}),errors=[];pg.on('pageerror',e=>errors.push(e.message));
  await pg.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);
  await pg.waitForFunction(()=>!document.querySelector('#act').disabled,null,{timeout:12000});
  await pg.waitForFunction(()=>document.documentElement.dataset.device);if(await pg.locator('#product').isVisible())await pg.locator('#viewMode').click();
  const menu=async n=>{await pg.locator('#openMenu').click();await pg.locator('[data-to='+n+']').click();};
  await menu('spots');assert.equal(await pg.locator('#places option').count(),117);
  await pg.selectOption('#waterType','salt');assert.equal(await pg.locator('#places option').count(),21);
  await pg.selectOption('#places',{label:'Phuket coastal waters'});await pg.selectOption('#period',{label:'Dusk'});await pg.locator('#fishHere').click();
  assert.equal(await pg.locator('#spot').innerText(),'Phuket coastal waters');await menu('spots');await pg.selectOption('#places',{label:'Chao Phraya River'});await pg.selectOption('#period',{label:'Dusk'});await pg.locator('#fishHere').click();
  // Choose a repeatable encounter through the same PRNG and normal cast entry point.
  await pg.evaluate(()=>{for(let seed=1;seed<10000;seed++){g.initialize(seed);g.place(placeId,currentSlot);g.advance(16,1,0,0);if(g.species()===40){g.initialize(seed);g.place(placeId,currentSlot);break;}}});
  await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===2);
  await pg.locator('#openMenu').click();let age=await pg.evaluate(()=>g.age());await pg.waitForTimeout(500);assert.equal(await pg.evaluate(()=>g.age()),age);await pg.locator('#resume').click();
  await pg.waitForFunction(()=>g.state()===3);await pg.locator('#act').click();await pg.waitForFunction(()=>g.state()===4);await pg.keyboard.down('r');await pg.waitForFunction(()=>g.state()===5,null,{timeout:22000});await pg.keyboard.up('r');
  assert.match(await pg.locator('#metrics').innerText(),/Rare.*Length.*Weight/);assert.match(await pg.locator('#origin').innerText(),/claws/);
  await menu('rod');await pg.selectOption('#finish','Copper');await pg.locator('#builds button').nth(1).click();assert.equal(await pg.evaluate(()=>g.rank(1)),1);await pg.locator('#resume').click();
  await pg.reload();await pg.waitForFunction(()=>!document.querySelector('#act').disabled);assert.equal(await pg.evaluate(()=>g.caught(40)),1);assert.equal(await pg.evaluate(()=>finish),1);
  await menu('book');assert.equal(await pg.locator('.record').count(),52);await pg.locator('#resume').click();
  await pg.setViewportSize({width:390,height:844});await menu('sensors');
  // Gravity in m/s², rest / raised vectors and stable dwell.
  for(const [xyz,button] of [[[0,0,9.80665],'restPose'],[[0,6.30,7.51],'liftPose']]){
   await pg.evaluate(async xyz=>{for(let i=0;i<64;i++){onMotion({accelerationIncludingGravity:{x:xyz[0],y:xyz[1],z:xyz[2]},rotationRate:{alpha:0,beta:2,gamma:1}});await new Promise(r=>setTimeout(r,17));}},xyz);
   await pg.locator('#'+button).click();
  }
  assert.equal(await pg.evaluate(()=>calibratedMobile),true);
  await pg.locator('#resume').click();assert.equal(await pg.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  assert.equal(errors.length,0,errors.join(';'));console.log('PASS 117 locations and 21 marine filters, dusk prawn catch, pause, metrics/origin, 52 records, tackle persistence, mobile layout and two-pose motion calibration.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});


