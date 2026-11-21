const {requireBootHome}=require('./boot-home-check.cjs');
const {showControl}=require('./menu-controls.cjs');
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
   if(window.AudioBufferSourceNode){
    const start=AudioBufferSourceNode.prototype.start;
    window.uiPcm=[];
    AudioBufferSourceNode.prototype.start=function(...args){
     const b=this.buffer;
     if(b?.sampleRate===16000&&[192,288,432].includes(b.length)){
      const pcm=b.getChannelData(0);
      uiPcm.push({frames:b.length,peak:pcm.reduce((peak,x)=>Math.max(peak,Math.abs(x)),0)});
     }
     return start.apply(this,args);
    };
   }
   Object.defineProperty(navigator,'vibrate',{configurable:true,value:undefined});
  });
  await p.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await p.goto('http://127.0.0.1:'+server.address().port);
  const play=await requireBootHome(p);
  const quietBeforeSpeaker=()=>p.evaluate(()=>({noAudio:audio===null,phase:g.state(),sources:window.probe?.sources||0}));
  assert.deepEqual(await quietBeforeSpeaker(),{noAudio:true,phase:0,sources:0},'Cold Home is quiet and cannot start a cast');
  await play.tap();
  assert.deepEqual(await quietBeforeSpeaker(),{noAudio:true,phase:0,sources:0},'Play itself must not opt in to sound or cast');
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
  await p.locator('#openMenu').tap();await p.locator('[data-section=home] [data-to=sound]').tap();
  const resumeMode=await p.evaluate(()=>navigator.audioSession?.type);
  if(graph&&resumeMode)assert.equal(resumeMode,'playback');
  await showControl(p,'#testSound');await p.locator('#testSound').tap();
  await showControl(p,'#rumbleStatus');assert.match(await p.locator('#rumbleStatus').innerText(),/Safari/);
  assert.equal(await p.locator('#testPhoneMotor').isVisible(),false);
  if(await p.evaluate(()=> 'switch' in document.createElement('input'))){
   await showControl(p,'#iosSwitch');await p.locator('#iosSwitch').tap();assert.equal(await p.locator('#cue').inputValue(),'Light');
   await showControl(p,'#iosSwitch');await p.locator('#iosSwitch').tap();assert.equal(await p.locator('#cue').inputValue(),'Light + tone');
  }
  if(graph){
   await p.evaluate(async()=>{await audio.suspend();});await showControl(p,'#testSound');await p.locator('#testSound').tap();
   await p.waitForFunction(()=>audio.state==='running');
  }
  if(graph&&await p.evaluate(()=>Array.isArray(window.uiPcm))){
   await p.locator('#resume').tap();
   await p.evaluate(()=>uiPcm.length=0);
   const frames=()=>p.evaluate(()=>uiPcm.map(({frames})=>frames));
   await p.locator('#openMenu').tap();
   assert.deepEqual(await frames(),[432],'one menu cue for a real tap');
   assert(await p.evaluate(()=>uiPcm[0].peak>.003),'menu cue contains nonzero PCM');
   await p.evaluate(()=>{$('resume').click();$('openMenu').click();$('resume').click();});
   assert.deepEqual(await frames(),[432],'programmatic menu clicks stay silent');
   await p.locator('#openMenu').press('Enter');
   assert.deepEqual(await frames(),[432,432],'keyboard activation has exactly one menu cue');
   // Both existing destination sheets keep their order; the map is optional page 3.
   await p.locator('[data-section=home] [data-to=spots]').press('Enter');
   assert.equal(await p.locator('#sheetNumber').textContent(),'1/3');
   assert(await p.locator('#locationMapOpen').isVisible(),'the destination list remains page one');
   assert(await p.locator('#sheetPrev').isDisabled(),'the list starts the pager');
   assert.deepEqual(await frames(),[432,432,432],'opening the destination menu uses a menu cue');
   await p.locator('#sheetNext').press('Enter');
   assert.equal(await p.locator('#sheetNumber').textContent(),'2/3');
   assert(await p.locator('#period + button').isVisible(),'conditions remain page two');
   assert.deepEqual(await frames(),[432,432,432,192],'one detent for a real conditions page change');
   await p.locator('#sheetNext').press('Enter');
   assert.equal(await p.locator('#sheetNumber').textContent(),'3/3');
   assert(await p.locator('#waterbodyMapSheet').isVisible()&&await p.locator('#waterbodyMap').isVisible(),'optional map is the final page');
   assert.deepEqual(await frames(),[432,432,432,192,192],'the map page emits the same single detent');
   assert(await p.locator('#sheetNext').isDisabled(),'the final page cannot emit another detent');
   await p.evaluate(()=>uiPcm.length=0);
   // Give the actual menu one real scrolling region
   // for this test so scrolling can be driven by the browser, not dispatchEvent.
   await p.evaluate(()=>{
    const area=document.createElement('section');area.id='uiAudioScrollFixture';area.tabIndex=0;
    area.style.cssText='position:absolute;inset:70px 16px auto;width:230px;height:110px;overflow:auto;pointer-events:auto;z-index:12';
    const inner=document.createElement('div');inner.style.height='600px';area.append(inner);
    $('menu').append(area);
    area.scrollTop=30;
   });
   await p.waitForTimeout(140);
   assert(await p.locator('#uiAudioScrollFixture').evaluate(el=>el.scrollTop>0),'scroll fixture moved');
   assert.deepEqual(await frames(),[],'programmatic scrolling stays silent');
   const area=p.locator('#uiAudioScrollFixture'),startTop=await area.evaluate(el=>el.scrollTop);
   await area.press('PageDown');
   await p.waitForFunction(top=>$('uiAudioScrollFixture').scrollTop>top,startTop);
   assert.deepEqual(await frames(),[192],'one cue for an actual keyboard scroll');
   await p.evaluate(()=>{$('uiAudioScrollFixture').remove();window.priorFx=$('fx').selectedIndex;$('fx').selectedIndex=0;$('fx').dispatchEvent(new Event('change',{bubbles:true}));});
   await p.locator('#resume').tap();await p.locator('#openMenu').tap();
   assert.deepEqual(await frames(),[192],'FX mute also suppresses trusted menu interactions');
   await p.evaluate(()=>{$('fx').selectedIndex=priorFx;$('fx').dispatchEvent(new Event('change',{bubbles:true}));});
   await p.locator('#resume').tap();
   await p.evaluate(()=>uiPcm.length=0);
   await p.locator('#act').tap();
   assert.deepEqual(await frames(),[288],'one short cue for a trusted play-control tap');
  }
  await p.evaluate(()=>document.fonts.ready);
  assert(await p.evaluate(()=>document.fonts.check('600 14px "Atkinson Hyperlegible Next"')&&
    ['spot','menuTitle','resume','soundStatus','startSound'].every(id=>getComputedStyle(document.getElementById(id)).fontFamily.includes('Atkinson Hyperlegible Next'))));

  assert.deepEqual(issues,[]);
  console.log('PASS '+(webkitRun?'WebKit':'Chromium')+' mobile profile: journal font, speaker WAV, Safari haptic controls; '+(graph?'running graph, PCM, music buffers and interruption recovery.':'host engine has no Web Audio backend; physical output untested.'));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
