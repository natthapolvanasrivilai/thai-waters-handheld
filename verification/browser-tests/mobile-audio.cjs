const {chromium,webkit,devices}=require('playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');

(async()=>{
 const webkitRun=process.env.TEST_WEBKIT==='1';
 const browser=webkitRun?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const html=fs.readFileSync(process.env.PLAYTEST_HTML||path.resolve(__dirname,'../../game/Thai-Waters-play.html'));
 const server=http.createServer((req,res)=>{res.setHeader('content-type','text/html');res.end(html);});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const p=await browser.newPage({...devices['iPhone 13'],viewport:{width:844,height:390}});
  const issues=[];p.on('pageerror',e=>issues.push(String(e)));
  await p.addInitScript(()=>{
   // Tap the graph immediately before the real output, without changing its destination.
   if(!window.AudioNode)return;
   const connect=AudioNode.prototype.connect;
   window.probe={peak:0,sources:0};
   AudioNode.prototype.connect=function(dest,...args){
    if(dest===this.context.destination){
     if(!window.probe.tap){
      const tap=this.context.createAnalyser();tap.fftSize=1024;window.probe.tap=tap;
      setInterval(()=>{const pcm=new Float32Array(tap.fftSize);tap.getFloatTimeDomainData(pcm);
       for(const value of pcm)window.probe.peak=Math.max(window.probe.peak,Math.abs(value));},8);
     }
     connect.call(this,window.probe.tap);
     if(this instanceof AudioBufferSourceNode)window.probe.sources++;
    }
    return connect.call(this,dest,...args);
   };
   Object.defineProperty(navigator,'vibrate',{configurable:true,value:undefined});
  });
  await p.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await p.goto('http://127.0.0.1:'+server.address().port);
  await p.waitForFunction(()=>typeof g!=='undefined'&&g);
  const graph=await p.evaluate(()=>Boolean(window.AudioContext||window.webkitAudioContext));
  const dial=p.locator('#dial'),rail=await dial.boundingBox(),field=await p.locator('#flatStage').boundingBox();
  assert(rail.width>=104&&rail.x>=field.x+field.width,'Right thumb target clears the fishing surface.');
  assert((await dial.locator('.dial-hub').boundingBox()).width>=44,'Visible hold target meets finger size.');
  await p.locator('#startSound').tap();
  assert(await p.locator('#dialAutoRow').isVisible(),'iPhone exposes its user-operated reel control.');
  {
   await p.evaluate(()=>{
    window.trustedReelTaps=[];window.startTurns=dialAngle;
    document.getElementById('dialAuto').addEventListener('change',e=>trustedReelTaps.push(e.isTrusted));
   });
   await p.locator('#dialAuto').tap();assert(await p.locator('#dialAuto').isChecked());
   await p.waitForFunction(()=>dialAngle-startTurns>65);
   await p.locator('#dialAuto').tap();assert(!await p.locator('#dialAuto').isChecked());
   const stopped=await p.evaluate(()=>dialAngle);await p.waitForTimeout(200);
   assert.equal(await p.evaluate(()=>dialAngle),stopped);
   assert.deepEqual(await p.evaluate(()=>trustedReelTaps),[true,true]);
   await p.locator('#dialAuto').tap();await p.locator('#dial').tap({position:{x:8,y:60}});
   assert(!await p.locator('#dialAuto').isChecked(),'Manual winding disengages automatic winding.');
  }
  if(graph)await p.waitForFunction(()=>audio?.state==='running'&&probe.peak>.004&&probe.sources>4);
  assert(await p.evaluate(async()=>{
   const bytes=await (await fetch(speakerCheck.src)).arrayBuffer();
   return new DataView(bytes).getUint32(0)===0x52494646&&new Int16Array(bytes,44).some(n=>n>5000);
  }));
  await p.locator('#openMenu').tap();await p.locator('[data-to=sound]').tap();
  const resumeMode=await p.evaluate(()=>navigator.audioSession?.type);
  if(graph&&resumeMode)assert.equal(resumeMode,'playback');
  await p.locator('#testSound').tap();
  assert.match(await p.locator('#rumbleStatus').innerText(),/Safari/);
  assert.equal(await p.locator('#testPhoneMotor').isVisible(),false);
  if(await p.evaluate(()=> 'switch' in document.createElement('input'))){
   await p.locator('#iosSwitch').tap();assert.equal(await p.locator('#cue').inputValue(),'Light');
   await p.locator('#iosSwitch').tap();assert.equal(await p.locator('#cue').inputValue(),'Light + tone');
  }
  if(graph){
   await p.evaluate(async()=>{await audio.suspend();});await p.locator('#testSound').tap();
   await p.waitForFunction(()=>audio.state==='running');
  }
  await p.evaluate(()=>document.fonts.ready);
  assert(await p.evaluate(()=>document.fonts.check('600 14px "Atkinson Hyperlegible Next"')&&
    ['spot','menuTitle','resume','soundStatus','startSound'].every(id=>getComputedStyle(document.getElementById(id)).fontFamily.includes('Atkinson Hyperlegible Next'))));

  assert.deepEqual(issues,[]);
  console.log('PASS '+(webkitRun?'WebKit':'Chromium')+' mobile profile: journal font, speaker WAV, Safari haptic controls; '+(graph?'running graph, PCM, music buffers and interruption recovery.':'host engine has no Web Audio backend; physical output untested.'));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
