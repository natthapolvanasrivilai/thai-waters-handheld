'use strict';
const assert=require('node:assert/strict');

// Observe the real visible Home, never open or dismiss it on the app's behalf.
// A Recovery screen terminates the normal ready wait without a silent fallback.
async function requireBootHome(page,{temporary=false}={}){
 await page.waitForFunction(()=>document.getElementById('startupRecovery')?.hidden===false||
  (typeof g!=='undefined'&&!!g&&powered&&bootHome&&$('menu').open&&$('menu').dataset.page==='boot-home'),
  null,{timeout:12000});
 const observed=await page.evaluate(async()=>{
  const dlg=$('menu'),player=$('act'),screen=$('scene');
  if(!$('startupRecovery').hidden)return {recovery:true};
  await document.fonts.ready;
  const action=$('bootResume'),routes=[...$('bootRoutes').querySelectorAll('button')];
  const box=dlg.getBoundingClientRect();
  const contained=[...routes,action].every(el=>{
   const r=el.getBoundingClientRect();
   return r.width>0&&r.height>0&&r.left>=box.left-1&&r.right<=box.right+1&&r.top>=box.top-1&&r.bottom<=box.bottom+1;
  });
  return {recovery:false,open:dlg.open,home:bootHome,powered,temporary:sessionOnly,actLocked:player.disabled,
   canvas:[screen.width,screen.height],dialog:[dlg.offsetWidth,dlg.offsetHeight],routes:routes.length,contained};
 });
 assert.deepEqual(observed,{recovery:false,open:true,home:true,powered:true,temporary,actLocked:true,
  canvas:[480,320],dialog:[480,320],routes:6,contained:true},'Actual 480×320 Home layout and input gate must be ready');
 const control=page.locator('#bootResume');
 assert(await control.isVisible());assert(await control.isEnabled());
 return control;
}
module.exports={requireBootHome};
