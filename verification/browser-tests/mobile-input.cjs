const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright-core');
const T = require('three');

(async () => {
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
   headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:390,height:844}});
  await page.addInitScript(()=>{
   const api={requestPermission:async()=>window.testPermission};
   Object.defineProperty(window,'DeviceMotionEvent',{value:api});
   Object.defineProperty(window,'DeviceOrientationEvent',{value:api});
   window.testPermission='denied';
  });
  await page.goto(pathToFileURL(process.env.PLAYTEST_HTML||path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);
  await page.waitForFunction(()=>g);
  await page.locator('#openMenu').tap();await page.locator('[data-to=sensors]').tap();
  await page.locator('#enableMotion').tap();
  await page.waitForFunction(()=>$('motionStatus').textContent.includes('declined'));
  await page.evaluate(()=>window.testPermission='granted');await page.locator('#enableMotion').tap();
  async function orientation(beta,gamma,n){
   await page.evaluate(async({beta,gamma,n})=>{
    for(let i=0;i<n;i++){
     window.dispatchEvent(Object.assign(new Event('devicemotion'),{accelerationIncludingGravity:null}));
     window.dispatchEvent(Object.assign(new Event('deviceorientation'),{beta,gamma}));
     await new Promise(r=>setTimeout(r,18));
    }
   },{beta,gamma,n});
  }
  await orientation(0,0,26);assert(await page.evaluate(()=>basePose));
  await page.locator('#resume').tap();
  await orientation(0,30,17);await orientation(0,0,19);
  const motionResult=await page.evaluate(()=>({state:g.state(),rodAngle,basePose,calibratedMobile,menu:menu.open,arrivalSince,message:$('message').textContent}));
  assert([1,2].includes(motionResult.state),'Right / left axis lift must cast from one neutral measurement. '+JSON.stringify(motionResult));
  await page.evaluate(()=>{g.travel(0);recenterOnRotation();});
  await orientation(0,0,25);await orientation(-30,0,18);await orientation(0,0,19);
  assert(await page.evaluate(()=>g.state()===1||g.state()===2),'After rotation the new axis must cast without opening settings.');
  await page.locator('#openMenu').tap();await page.locator('[data-to=sensors]').tap();
  await page.locator('#wristReel').check();await page.locator('#resume').tap();
  await page.evaluate(()=>{g.travel(0);g.setTechnique(1);g.advance(16,1,0,0);g.advance(651,0,0,0);});
  await orientation(0,0,15);await orientation(-32,0,18);await orientation(0,0,16);
  assert.equal(await page.evaluate(()=>wristTurns),0,'A rod lift cannot wind line.');
  await orientation(0,34,18);await orientation(0,34,11);
  assert.equal(await page.evaluate(()=>wristTurns),.5,'A held side twist must generate one half turn.');
  await orientation(0,0,17);
  assert.equal(await page.evaluate(()=>wristTurns),.5,'Returning the wrist cannot pay out or add line.');
  assert(Math.abs(await page.evaluate(()=>g.lureTravel())-.5)<.02,'Actual spoon must receive the wrist encoder turns.');
  await page.locator('#openMenu').tap();await orientation(0,-34,16);await orientation(0,0,18);
  assert.equal(await page.evaluate(()=>wristTurns),.5,'Paused motion cannot wind.');
  await page.locator('#resume').tap();await orientation(0,0,12);await orientation(0,-34,18);await orientation(0,0,18);
  assert.equal(await page.evaluate(()=>wristTurns),1,'Either side twist is accepted after centering.');
  await page.evaluate(()=>recenterOnRotation());await orientation(0,40,24);
  assert.equal(await page.evaluate(()=>wristTurns),1,'Changing screen orientation and centering must not wind.');
  await page.evaluate(()=>{
   const read=samplePointerWheel;window.netTurns=0;
   samplePointerWheel=a=>{const result=read(a);window.netTurns+=result;return result;};
  });
  const cdp=await page.context().newCDPSession(page);
  const touch=(type,point)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:point?[{x:point[0],y:point[1],id:1}]:[]});
  async function wind(point){
   await touch('touchStart',point(0));
   for(let i=1;i<=18;i++)await touch('touchMove',point(i/18));
   await touch('touchEnd');
  }
  const dial=page.locator('#dial');await dial.scrollIntoViewIfNeeded();
  const b=await dial.boundingBox(),cx=b.x+b.width/2,cy=b.y+b.height/2,r=b.width*.42;
  await wind(t=>[cx+r*Math.cos(2*Math.PI*t),cy+r*Math.sin(2*Math.PI*t)]);
  assert(Math.abs(await page.evaluate(()=>window.netTurns)-1)<.07,'Touch rim must return a full encoder revolution.');
  await touch('touchStart',[cx,cy]);assert(await page.evaluate(()=>held));await touch('touchEnd');assert(!await page.evaluate(()=>held));
  await page.locator('#viewMode').tap();await page.waitForFunction(()=>document.documentElement.dataset.device==='ready');
  const product=page.locator('#product');await product.scrollIntoViewIfNeeded();
  const box=await product.boundingBox(),aspect=box.width/box.height,half=Math.max(41,67/aspect);
  const camera=new T.OrthographicCamera(-half*aspect,half*aspect,half,-half,.1,900);
  camera.position.set(132,46,242);camera.lookAt(7,0,12);camera.updateMatrixWorld(true);
  await page.evaluate(()=>{window.netTurns=0;});
  await wind(t=>{
   const a=.9-2*Math.PI*t;
   const p=new T.Vector3(65,7.8*Math.cos(a),14.8+7.8*Math.sin(a)).project(camera);
   return [box.x+(p.x+1)*box.width/2,box.y+(1-p.y)*box.height/2];
  });
  assert(Math.abs(await page.evaluate(()=>window.netTurns)-1)<.1,'Touch on the projected crank must retrieve a full turn.');
  console.log('PASS motion denial recovery, orientation fallback, automatic neutral and rotation recentering, gesture casts, pitch/roll isolation, wrist clutch half turns without return/paused/rotation credit, flat center hold and two real touch crank revolutions.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
