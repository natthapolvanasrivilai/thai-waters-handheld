const {chromium}=require('playwright-core'),{pathToFileURL}=require('url'),path=require('path'),assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1080,height:830},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);await page.waitForFunction(()=>document.documentElement.dataset.device&&g);
  assert.equal(await page.evaluate(()=>document.documentElement.dataset.device),'ready',errors.join('\n'));
  await page.waitForTimeout(900);
  const b=await page.locator('#product').boundingBox();console.log('bounds',b);
  const T=require('three');const w=b.width,h=b.height,aspect=w/h,half=Math.max(41,67/aspect);
  const camera=new T.OrthographicCamera(-half*aspect,half*aspect,half,-half,.1,900);camera.up.set(0,1,0);camera.position.set(132,-54,242);camera.lookAt(7,0,12);camera.updateMatrixWorld(true);
  function xy(v){const p=v.clone().project(camera);return [b.x+(p.x+1)*w/2,b.y+(1-p.y)*h/2];}
  await page.mouse.click(...xy(new T.Vector3(0,0,28.53)));await page.waitForFunction(()=>g.state()===1||g.state()===2);
  await page.evaluate(()=>{if(g.state()===1)g.advance(650,0,0,0);g.advance(7500,0,0,0);g.advance(25,0,1,0);});assert.equal(await page.evaluate(()=>g.state()),4);
  const initial=await page.evaluate(()=>g.remaining());
  function reelPoint(a){return xy(new T.Vector3(65,7.8*Math.cos(a),14.8+7.8*Math.sin(a)));}
  await page.mouse.move(...reelPoint(.9));await page.mouse.down();
  for(let i=1;i<=44;i++){await page.mouse.move(...reelPoint(.9+i*2*Math.PI/44));await page.waitForTimeout(18);}
  await page.mouse.up();
  let after=await page.evaluate(()=>g.remaining());assert(after<initial-.55,'Physical drag must retrieve line: '+initial+' -> '+after);
  console.log('PASS LCD click casts and a full mouse revolution on the 3D grip retrieved '+(initial-after).toFixed(2)+' turns.');
  await page.locator('#foldButton').click();assert.equal(await page.locator('#foldButton').innerText(),'Open reel');await page.locator('#foldButton').click();
  await page.locator('#viewMode').click();assert(await page.locator('#flatStage').isVisible());await page.locator('#viewMode').click();
  console.log('errors',errors);assert(!errors.length);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});


