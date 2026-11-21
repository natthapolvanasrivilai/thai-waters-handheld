const {requireBootHome}=require('./boot-home-check.cjs');
const {showControl}=require('./menu-controls.cjs');
const assert=require('node:assert/strict');
const {chromium}=require('playwright-core');
const {pathToFileURL}=require('node:url');
const path=require('node:path');
// Inspect the final image composited by the real gameplay draw call. A DOM
// overlay can pass click tests while disappearing from the device texture.
async function raster(page) {
 return page.evaluate(()=>{
  const original=ctx.drawImage;
  let overlay;
  ctx.drawImage=function(image,...args){overlay=image;return original.call(this,image,...args);};
  try{draw();}finally{ctx.drawImage=original;}
  const data=overlay.getContext('2d').getImageData(0,0,480,320).data;
  function samples(left,top,width,height){
   let visible=0,hash=2166136261;
   for(let y=top;y<top+height;y++)for(let x=left;x<left+width;x++){
    const i=4*(480*y+x);if(data[i+3])visible++;
    for(let k=0;k<4;k++)hash=Math.imul(hash^data[i+k],16777619);
   }
   return {visible,hash};
  }
  return {size:[overlay.width,overlay.height],transparent:samples(170,0,60,25).visible,
   header:samples(6,0,130,29).visible,action:samples(420,286,59,33).visible,
   drawer:samples(245,38,222,266),hitOpacity:getComputedStyle(lcdUI).opacity};
 });
}
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
   headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const url=pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
  const p=await browser.newPage({viewport:{width:1050,height:780}});
  await p.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await p.goto(url);
  await (await requireBootHome(p)).click();
  await p.waitForFunction(()=>g&&document.documentElement.dataset.view==='screen');
  await p.locator('#viewMode').click();await p.waitForFunction(()=>physicalView&&document.documentElement.dataset.view==='device');
  const main=await raster(p);
  assert.deepEqual(main.size,[480,320]);assert.equal(main.hitOpacity,'0');
  assert.equal(main.transparent,0,'sky visible between HUD labels');
  assert(main.header>40&&main.action===0,'visible header and clear water for direct casting');
  const power=await p.evaluate(()=>{
   const plane=document.createElement('canvas');plane.width=480;plane.height=320;
   const ink=plane.getContext('2d');
   function sample(value){
    $('simBattery').value=value;draw();ink.clearRect(0,0,480,320);paintLcdInterface(ink);
    const power=$('lcdPower'),x=power.offsetLeft+3,y=power.offsetTop+2;
    const colors=[0,1,2,3].map(i=>Array.from(ink.getImageData(x+4+i*5,y+4,1,1).data).join(','));
    return colors;
   }
   const result=[sample('72'),sample('12')];$('simBattery').value='72';draw();return result;
  });
  assert.equal(power[0][0],power[0][2]);assert.notEqual(power[0][2],power[0][3],'three lit battery segments at 72%');
  assert.notEqual(power[1][0],power[1][1]);assert.equal(power[1][1],power[1][3],'one lit battery segment at 12%');
  const rasterPages=new Set();
  await p.locator('#openMenu').click();
  for(const route of ['book','spots','rod','sound','sensors','crew']){
   await p.locator('[data-section=home] [data-to="'+route+'"]').click();
   assert(await p.evaluate(()=>{
    const shell=$('lcdUI').getBoundingClientRect(),dialog=$('menu').getBoundingClientRect();
    return $('menu').closest('#product')&&dialog.top>=shell.top&&dialog.right<=shell.right+1
      &&dialog.bottom<=shell.bottom+1&&($('menu').dataset.page==='book'?dialog.width>=shell.width*.99:dialog.left>shell.left+shell.width*.12&&dialog.width<shell.width*.85);
   }),'Route left the modeled screen: '+route);
   const drawer=(await raster(p)).drawer;
   assert(drawer.visible>50000,'missing drawer pixels on '+route);rasterPages.add(drawer.hash);
   if(route==='book'){
    await p.locator('#species-0').click();assert(await p.locator('#bookDetail').isVisible());
    assert.notEqual((await raster(p)).drawer.hash,drawer.hash,'specimen detail must change its pixels');
    await p.locator('#back').click();
   }
   if(route==='sound'){
    await showControl(p,'#rumbleLevel + button');await p.locator('#rumbleLevel + button').click();
    assert.notEqual((await raster(p)).drawer.hash,drawer.hash,'choice picker must replace the menu pixels');
    await p.getByRole('option',{name:'High',exact:true}).click();
    assert.equal(await p.locator('#rumbleLevel').inputValue(),await p.locator('#rumbleLevel option').last().getAttribute('value')??'High');
   }
   if(route==='book'&&process.env.LCD_REVIEW_PNG)await p.locator('#product').screenshot({path:process.env.LCD_REVIEW_PNG});
   await p.locator('#back').click();
  }
  assert.equal(rasterPages.size,6,'six distinct rasterized routes');
  await p.locator('#resume').click();assert.equal(await p.locator('#menu').isVisible(),false);
  const phone=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:390,height:844}});
  await phone.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));
  await phone.goto(url);
  await (await requireBootHome(phone)).tap();
  await phone.waitForFunction(()=>g);
  await phone.setViewportSize({width:844,height:390});
  await phone.waitForFunction(()=>document.documentElement.classList.contains('immersive'));
  const dims=await phone.evaluate(()=>{
   const stage=$('flatStage').getBoundingClientRect(),dial=$('dial').getBoundingClientRect();
   const tools=document.querySelector('.viewtools').getBoundingClientRect();
   return {height:stage.height,aspect:stage.width/stage.height,overlap:Math.max(0,stage.right-dial.left),
           toolsOverlap:Math.max(0,stage.bottom-tools.top),scroll:document.documentElement.scrollHeight-innerHeight};
  });
  assert(dims.height>=330&&Math.abs(dims.aspect-1.5)<.02&&dims.overlap<1&&dims.toolsOverlap<1&&dims.scroll<2,JSON.stringify(dims));
  if(process.env.PHONE_OVERLAY_PNG)await phone.evaluate(()=>{chooseSpot(0,0);g.restoreEntry(0,1,21);refresh();});
  assert((await raster(phone)).action===0,'phone water is clear for direct casting');
  await phone.locator('#openMenu').tap();
  if(process.env.PHONE_MENU_PNG)await phone.locator('#flatStage').screenshot({path:process.env.PHONE_MENU_PNG});
  await phone.locator('[data-section=home] [data-to="book"]').tap();
  assert(await phone.locator('#records').isVisible());
  if(process.env.PHONE_OVERLAY_PNG)await phone.locator('#flatStage').screenshot({path:process.env.PHONE_OVERLAY_PNG});await phone.locator('#resume').tap();
  await phone.setViewportSize({width:390,height:844});
  await phone.waitForFunction(()=>document.documentElement.classList.contains('immersive')&&innerHeight>innerWidth);
  assert(await phone.locator('#mobileFullscreen').isVisible(),'portrait retains explicit fullscreen control');
  console.log('PASS 480x320 framebuffer, transparent HUD, direct casting, all six menu rasters, journal pages, picker controls, projected hits and phone rotation.');
 }finally{await browser.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
