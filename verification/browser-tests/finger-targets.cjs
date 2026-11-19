const {showControl}=require('./menu-controls.cjs');
const assert=require('node:assert/strict'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');
(async()=>{
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{for(const [width,height] of [[844,390],[667,375],[390,844],[320,568]]){
 const p=await browser.newPage({viewport:{width,height},isMobile:true,hasTouch:true});
 await p.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);
 await p.waitForFunction(()=>g&&!$('act').disabled);let smallest=Infinity;
 async function hit(selector){
  await showControl(p,selector);const item=p.locator(selector).first();if(['#fullscreen','#testPhoneMotor'].includes(selector)&&!await item.isVisible())return;
  await item.scrollIntoViewIfNeeded({timeout:3000}).catch(e=>{throw Error(width+' '+selector+': '+e.message)});
  const b=await item.evaluate(el=>{const r=el.getBoundingClientRect();const hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {w:r.width,h:r.height,ok:el.contains(hit)};});
  assert(b.ok,selector+' unreachable at '+width+' '+JSON.stringify(b));assert(b.w>=43.9&&b.h>=43.9,selector+' too small at '+width+' '+JSON.stringify(b));smallest=Math.min(smallest,b.w,b.h);
 }
 for(const el of ['#act','#rigHud','#fullscreen','#openMenu'])await hit(el);
 await p.locator('#openMenu').tap();await hit('[data-language=th]');
 for(const page of ['spots','book','rod','sound','sensors','crew']){
  const route='[data-to='+page+']';await hit(route);await p.locator(route).tap();
  await hit('#back');await hit('#resume');
  if(page==='book'){await hit('#bookSearch');await hit('#species-0');await hit('#bookNext');await p.locator('#species-0').tap();await hit('#back');await p.locator('#back').tap();}
  if(page==='rod'){await hit('#hookBait + button');await p.locator('#hookBait + button').tap();for(let i=0;i<6;i++)await hit('.bait-option[data-index="'+i+'"]');await hit('#lcdPicker .menubar button');await p.locator('#lcdPicker .menubar button').first().tap();}
  if(page==='sound')await hit('#testPhoneMotor');
  if(page==='sensors')await hit('label:has(#handheldEnable)');
  if(page==='spots')await hit('#fishHere');
  if(page==='crew')await hit('#cupJoin');
  await p.locator('#back').tap();
 }
 console.log(width+'×'+height+' smallest checked control '+smallest.toFixed(1)+' CSS px');await p.close();
 }}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
