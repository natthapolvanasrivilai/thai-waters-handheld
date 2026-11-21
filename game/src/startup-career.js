// Strict pre-publication staging for the future boot Home. The caller owns an
// initialized, isolated engine and must not publish it if any step throws.
function stageStartupCareer({engine,vault,locations,slotForTime}){
 return applyStartupCareer({engine,save:vault.load(),locations,slotForTime});
}
// Applies only values already normalized by career-storage.js. A temporary
// backup retains the catch record but cannot claim a live Daily Cup entry.
function applyStartupCareer({engine,save,locations,slotForTime,sessionOnly=false}){
 if(save===null)return null;
 if(sessionOnly&&save.pendingCapture?.uid&&save.history.some(entry=>entry.uid?.toLowerCase()===save.pendingCapture.uid.toLowerCase()))
  throw Error('The pending catch is already recorded in this backup');
 const currentSlot=slotForTime(save.time);
 const location=locations[save.place];
 if(!location)throw Error('Saved destination is unavailable');
 for(let i=0;i<save.book.length;i++)engine.restoreEntry(i,...save.book[i]);
 for(let i=0;i<save.rank.length;i++)for(let k=0;k<save.rank[i];k++)engine.purchase(i);
 engine.setBait(save.bait);engine.setTechnique(save.rig);
 engine.place(save.place,currentSlot);
 if(save.pending!==null)engine.restoreCatch(save.pending[0],save.pending[1]);
 return {
  catchHistory:save.history,pendingCapture:save.pendingCapture,placeId:save.place,
  weatherMode:save.weather,timeMode:save.time,finish:save.finish,locationId:location.pool,
  pendingDay:sessionOnly?0:(save.pending?.[2]??0),currentSlot
 };
}
if(typeof module!=='undefined'&&module.exports)module.exports={stageStartupCareer,applyStartupCareer};
