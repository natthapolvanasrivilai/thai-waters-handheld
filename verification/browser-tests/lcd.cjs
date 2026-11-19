const assert=require('node:assert/strict');
const {chromium}=require('playwright-core');
const {pathToFileURL}=require('node:url');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
   headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const url=pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
  const p=await browser.newPage({viewport:{width:1050,height:780}});
  await p.goto(url);await p.waitForFunction(()=>g&&physicalView);
  await p.locator('#openMenu').click();
  for(const route of ['book','spots','rod','sound','sensors','crew']){
   await p.locator('[data-to="'+route+'"]').click();
   assert(await p.evaluate(()=>{
    const shell=$('lcdUI').getBoundingClientRect(),dialog=$('menu').getBoundingClientRect();
    return $('menu').closest('#product')&&dialog.top>=shell.top&&dialog.right<=shell.right+1
      &&dialog.bottom<=shell.bottom+1&&dialog.left>shell.left+shell.width*.43&&dialog.width<shell.width*.55;
   }),'Route left the modeled screen: '+route);
   if(route==='sound'){
    await p.locator('#rumbleLevel + button').click();
    await p.getByRole('option',{name:'High',exact:true}).click();
    assert.equal(await p.locator('#rumbleLevel').inputValue(),await p.locator('#rumbleLevel option').last().getAttribute('value')??'High');
   }
   if(route==='book'&&process.env.LCD_REVIEW_PNG)await p.locator('#product').screenshot({path:process.env.LCD_REVIEW_PNG});
   await p.locator('#back').click();
  }
  await p.locator('#resume').click();assert.equal(await p.locator('#menu').isVisible(),false);
  const phone=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:390,height:844}});
  await phone.goto(url);await phone.waitForFunction(()=>g);
  await phone.setViewportSize({width:844,height:390});
  await phone.waitForFunction(()=>document.documentElement.classList.contains('immersive'));
  const dims=await phone.evaluate(()=>{
   const stage=$('flatStage').getBoundingClientRect(),dial=$('dial').getBoundingClientRect();
   return {height:stage.height,overlap:Math.max(0,stage.right-dial.left),scroll:document.documentElement.scrollHeight-innerHeight};
  });
  assert(dims.height>=380&&dims.overlap<1&&dims.scroll<2,JSON.stringify(dims));
  if(process.env.PHONE_OVERLAY_PNG)await phone.evaluate(()=>{chooseSpot(0,0);g.restoreEntry(0,1,21);refresh();});
  await phone.locator('#openMenu').tap();
  if(process.env.PHONE_MENU_PNG)await phone.locator('#flatStage').screenshot({path:process.env.PHONE_MENU_PNG});
  await phone.locator('[data-to="book"]').tap();
  assert(await phone.locator('#records').isVisible());
  if(process.env.PHONE_OVERLAY_PNG)await phone.locator('#flatStage').screenshot({path:process.env.PHONE_OVERLAY_PNG});await phone.locator('#resume').tap();
  await phone.setViewportSize({width:390,height:844});
  await phone.waitForFunction(()=>!document.documentElement.classList.contains('immersive'));
  console.log('PASS all six routes inside the projected LCD, in-screen setting selection and phone landscape/portrait transitions.');
 }finally{await browser.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
