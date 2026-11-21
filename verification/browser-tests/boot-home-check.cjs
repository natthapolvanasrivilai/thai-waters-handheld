'use strict';
const assert=require('node:assert/strict');

// Observe genuine startup, including fail-closed Recovery, without starting play.
async function requireBootHome(page,{temporary=false}={}){
 await page.waitForFunction(()=>document.getElementById('startupRecovery')?.hidden===false||
  (typeof g!=='undefined'&&!!g&&powered&&bootHome&&$('menu').open&&$('menu').dataset.page==='boot-home'),
  null,{timeout:12000});
 const view=()=>page.evaluate(async()=>{
  const dlg=$('menu'),screen=$('scene');
  if(!$('startupRecovery').hidden)return {recovery:true};
  await document.fonts.ready;
  const start=$('bootStart'),resume=$('bootResume'),dock=$('arcadeDock');
  const routes=[...$('bootRoutes').querySelectorAll('button')];
  const modes=dlg.hasAttribute('data-arcade-modes');
  const rect=el=>el.getBoundingClientRect(),inside=(a,b)=>a.width>0&&a.height>0&&
   a.left>=b.left-1&&a.right<=b.right+1&&a.top>=b.top-1&&a.bottom<=b.bottom+1;
  let saved;
  try{saved={readable:true,raw:localStorage.getItem('thai-atlas-v2')};}
  catch{saved={readable:false,raw:null};}
  return {recovery:false,open:dlg.open,home:bootHome,powered,temporary:sessionOnly,
   locked:['act','dial','catchContinue','joinCrew'].every(id=>$(id).disabled),
   canvas:[screen.width,screen.height],dialog:[dlg.offsetWidth,dlg.offsetHeight],
   modes,routes:routes.map(b=>b.dataset.to),titleVisible:inside(rect(start),rect(dlg)),
   promptUnboxed:getComputedStyle(start).borderTopWidth==='0px'&&getComputedStyle(start).backgroundColor==='rgba(0, 0, 0, 0)',
   railReady:modes&&inside(rect(dock),rect(dlg))&&inside(rect(resume),rect(dock))&&
    dock.scrollHeight>dock.clientHeight&&getComputedStyle(dock).overflowY==='auto'&&
    routes.every(b=>b.offsetHeight>=70&&rect(b).left>=rect(dock).left-1&&rect(b).right<=rect(dock).right+1),
   state:{place:placeId,phase:g.state(),arrival:arrivalSince!==null,saved}};
 });
 const checkBase=({recovery,open,home,powered,temporary:mode,locked,canvas,dialog,routes})=>
  assert.deepEqual({recovery,open,home,powered,temporary:mode,locked,canvas,dialog,routes},
   {recovery:false,open:true,home:true,powered:true,temporary,locked:true,canvas:[480,320],dialog:[480,320],
    routes:['spots','rod','book','crew','career','boot-settings']},
   'Actual 480×320 Home layout and input gate must be ready');
 const before=await view();checkBase(before);
 if(!before.modes){
  assert(before.titleVisible&&before.promptUnboxed,'Startup shows only the borderless start invitation');
  assert(await page.locator('#bootResume').isHidden());
  const start=page.locator('#bootStart');
  assert(await start.isEnabled());
  // Real user-like activation only reveals modes; it must not resume or mutate storage.
  if(await page.evaluate(()=>matchMedia('(pointer: coarse)').matches))await start.tap();
  else await start.press('Enter');
 }
 const after=await view();checkBase(after);
 assert(after.modes&&after.railReady&&!after.titleVisible,'One aligned scroll rail exposes the original six routes');
 assert(temporary||before.state.saved.readable,'Normal startup must have readable save storage');
 assert(after.state.saved.readable===before.state.saved.readable&&after.state.saved.raw===before.state.saved.raw,
  'Entering modes cannot modify the save binding');
 assert.deepEqual({place:after.state.place,phase:after.state.phase,arrival:after.state.arrival},
  {place:before.state.place,phase:before.state.phase,arrival:before.state.arrival},'Entering modes cannot resume, travel, or cast');
 const control=page.locator('#bootResume');
 assert(await control.isVisible());assert(await control.isEnabled());
 return control;
}
module.exports={requireBootHome};
