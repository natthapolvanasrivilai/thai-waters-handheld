const {chromium}=require('playwright-core'),{pathToFileURL}=require('url'),path=require('path'),assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1080,height:830},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await page.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);await page.waitForFunction(()=>document.documentElement.dataset.device&&g);
  assert.equal(await page.evaluate(()=>document.documentElement.dataset.device),'ready',errors.join('\n'));
  await page.waitForTimeout(900);
  const b=await page.locator('#product').boundingBox();console.log('bounds',b);
  const T=require('three');const w=b.width,h=b.height,aspect=w/h,half=Math.max(41,67/aspect);
  const camera=new T.OrthographicCamera(-half*aspect,half*aspect,half,-half,.1,900);camera.up.set(0,1,0);camera.position.set(132,46,242);camera.lookAt(7,0,12);camera.updateMatrixWorld(true);
  function xy(v){const p=v.clone().project(camera);return [b.x+(p.x+1)*w/2,b.y+(1-p.y)*h/2];}
  await page.mouse.click(...xy(new T.Vector3(0,0,28.53)));await page.waitForFunction(()=>g.state()===1||g.state()===2);
  await page.evaluate(()=>{if(g.state()===1)g.advance(650,0,0,0);g.advance(7500,0,0,0);g.advance(25,0,1,0);});assert.equal(await page.evaluate(()=>g.state()),4);
  // A running fish takes line independently of the crank. Measure signed
  // encoder turns at the input boundary, before fight physics modifies line.
  await page.evaluate(()=>{
    const read=samplePointerWheel;
    window.encoderTravel=0;
    samplePointerWheel=angle=>{const delta=read(angle);window.encoderTravel+=delta;return delta;};
  });
  function reelPoint(a){return xy(new T.Vector3(65,7.8*Math.cos(a),14.8+7.8*Math.sin(a)));}
  await page.mouse.move(...reelPoint(.9));await page.mouse.down();
  for(let i=1;i<=44;i++){await page.mouse.move(...reelPoint(.9-i*2*Math.PI/44));await page.waitForTimeout(18);}
  await page.mouse.up();
  const forward=await page.evaluate(()=>window.encoderTravel);
  assert(Math.abs(forward-1)<.08,'Clockwise turn at the right-side grip: '+forward);
  await page.mouse.move(...reelPoint(.9));await page.mouse.down();
  for(let i=1;i<=44;i++){await page.mouse.move(...reelPoint(.9+i*2*Math.PI/44));await page.waitForTimeout(18);}
  await page.mouse.up();const reverse=await page.evaluate(()=>window.encoderTravel)-forward;
  assert(Math.abs(reverse+1)<.08,'Counterclockwise turn at the right-side grip: '+reverse);
  console.log('PASS LCD tap casts. Right-side crank reads '+forward.toFixed(2)+' turn clockwise and '+reverse.toFixed(2)+' counterclockwise.');
  await page.locator('#foldButton').click();assert.equal(await page.locator('#foldButton').innerText(),'Open reel');await page.locator('#foldButton').click();
  const beforeGrip=await page.locator('#lcdUI').boundingBox();
  await page.locator('#gripButton').click();assert.equal(await page.locator('#gripButton').innerText(),'Remove rod grip');
  assert((await page.locator('#lcdUI').boundingBox()).width<beforeGrip.width*.75);
  if(process.env.GRIP_REVIEW_PNG){await page.evaluate(()=>{g.initialize(23);g.place(placeId,currentSlot);});await page.waitForTimeout(1000);await page.locator('#product').screenshot({path:process.env.GRIP_REVIEW_PNG});}
  await page.locator('#gripButton').click();assert.equal(await page.locator('#gripButton').innerText(),'Attach rod grip');
  await page.locator('#viewMode').click();assert(await page.locator('#flatStage').isVisible());await page.locator('#viewMode').click();
  await page.locator('#powerPin').click();
  assert.equal(await page.locator('#simPower').textContent(),'Power on');
  assert(await page.locator('#act').isDisabled());
  const pausedAge=await page.evaluate(()=>g.age());
  await page.waitForTimeout(160);assert.equal(await page.evaluate(()=>g.age()),pausedAge);
  await page.locator('#simPower').click();assert(!await page.locator('#act').isDisabled());
  const labels=await page.evaluate(()=>{
    const labels=[];
    for(const value of ['72','12','42+','USB','--']){$('simBattery').value=value;draw();labels.push($('lcdPower').textContent);}
    return labels;
  });
  assert.deepEqual(labels,['SIM 72%','SIM 12%','SIM ⚡42%','SIM USB','SIM --']);
  console.log('PASS top-left power key, paused simulator and battery status modes.');
  console.log('errors',errors);assert(!errors.length);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});


