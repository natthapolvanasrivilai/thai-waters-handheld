const assert=require('node:assert/strict'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');
(async()=>{
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
 const page=await browser.newPage({viewport:{width:844,height:390},isMobile:true,hasTouch:true});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);
 await page.waitForFunction(()=>g&&$('rigHud').dataset.kit&&$('lcdUI').hasAttribute('data-casting-water'));
 const getHud=()=>page.locator('#rigIcons').evaluate(el=>el.toDataURL());
 const snap=async name=>{if(process.env.HUD_PREVIEW)await page.locator('#flatStage').screenshot({path:path.join(process.env.HUD_PREVIEW,name+'.png')});};
 await snap('Thai-Waters-tackle-hud');
 const initial=await getHud();
 await page.locator('#rigHud').tap();assert.equal(await page.locator('#menu').getAttribute('data-page'),'rod');
 for(const [field,index] of [['hookBait',1],['baitDepth',2],['technique',1],['finish',2]]){
  await page.locator('#'+field+' + button').tap();await page.locator('#lcdPicker .choice-list button').nth(index).tap();
 }
 await page.locator('#resume').tap();await page.waitForFunction(()=>$('rigHud').dataset.kit==='th/2/1/13');
 assert.notEqual(await getHud(),initial);
 const size=await page.locator('#rigHud').boundingBox();assert(size.height>=44);
 assert.equal(await page.locator('#act').evaluate(el=>getComputedStyle(el).opacity),'0');
 await page.evaluate(()=>scenePress(.75,.15));assert.equal(await page.evaluate(()=>g.state()),0);
 await page.locator('#act').tap({position:{x:180,y:90}});await page.waitForFunction(()=>g.state()===1||g.state()===2);
 const aim=await page.evaluate(()=>[g.aimX(),g.aimY()]);assert(aim[0]<.45 && aim[1]>.44);
 await page.evaluate(()=>{
  g.initialize(37);g.visit(0,1);g.setAim(.64,.67);g.advance(16,1,0,0);g.advance(g.flightMs(),0,0,0);g.advance(6500,0,0,0);g.advance(20,0,1,0);
  if(g.state()!==4)throw Error('fight fixture failed '+g.state());
  const original=tensionLight;
  window.tensionSamples=[];
  tensionLight=function(c,heat,x,y){if(tensionSamples.length<80)tensionSamples.push([x,y,heat]);original(c,heat,x,y);};
 });
 await page.waitForFunction(()=>tensionSamples.length>4);
 const samples=await page.evaluate(()=>tensionSamples);assert(samples.every(([x,y])=>Number.isFinite(x)&&x<450&&y>80));assert(new Set(samples.map(s=>s[1])).size>1);
 await snap('Thai-Waters-line-tension');
 const gauge=await page.evaluate(()=>{
  const samples=[];
  for(const [x,y,load] of [[1,180,.2],[250,220,.6],[479,301,.99]]){
   const layer=document.createElement('canvas');layer.width=480;layer.height=320;
   const c=layer.getContext('2d');tensionLight(c,load,x,y);
   const data=c.getImageData(0,0,480,320).data;let left=480,right=0,top=320,bottom=0;
   for(let i=3;i<data.length;i+=4){if(!data[i])continue;const px=(i>>2)%480,py=Math.floor((i>>2)/480);left=Math.min(left,px);right=Math.max(right,px);top=Math.min(top,py);bottom=Math.max(bottom,py);}
   samples.push({left,right,top,bottom});
  }
  return samples;
 });
 assert(gauge.every(b=>b.left>=0&&b.right<480&&b.bottom-b.top===9));
 assert(gauge[0].right<50&&gauge[1].left>225&&gauge[1].right<275&&gauge[2].left>430);
 await page.evaluate(()=>{g.initialize(10);g.place(placeId,currentSlot);refresh();});
 await page.locator('#openMenu').tap();await page.locator('[data-to=book]').tap();
 assert(await page.locator('#discovered').innerText().then(t=>t.includes('ทั่วไทย')));
 const national=await page.evaluate(()=>bookMatches().length);assert(national>2100);
 for(const [label,mode] of [['Inland',5],['Sea',6]]){
  await page.locator('#bookFilter + button').tap();if(mode>=6)await page.locator('#lcdPicker .menubar button').last().tap();await page.locator('#lcdPicker [data-index="'+mode+'"]').tap();
  assert(await page.evaluate(()=>bookMatches().length>100));
 }
 assert.deepEqual(errors,[]);console.log('PASS Thai tackle icons and workshop, aimed water tap, tension tracks moving line, and nationwide/sea/inland collection ('+national+').');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
