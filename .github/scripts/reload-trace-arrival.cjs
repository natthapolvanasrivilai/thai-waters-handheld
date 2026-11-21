// Only for exact synthetic browser regressions; no literal URLs, save payloads,
// catch IDs, species names, or exception messages are emitted.
async function readCheckpoint({place,placeName,species,observe}) {
 const observed=observe==='cast'?await window.castProbe:observe==='weight'?g.grams():null;
 try {
  if(placeName)place=atlas.locations.find(l=>l.name===placeName)?.id;
  const trace=(()=>{

   const act=document.querySelector('#act'),button=document.querySelector('#catchContinue');
   const out={
    protocol:['file:','https:','http:'].includes(location.protocol)?location.protocol:'other',
    documentReady:document.readyState,ready:!!act&&!act.disabled,
    phase:typeof g==='undefined'||!g?null:g.state(),
    continueShown:!!button&&!button.hidden,
    activePlaceMatched:Number.isInteger(place)&&typeof placeId!=='undefined'?placeId===place:null,
    selectedTimeMode:typeof timeMode!=='undefined'&&Number.isInteger(timeMode)&&timeMode>=0&&timeMode<=4?timeMode:null,
    activeSlot:typeof currentSlot!=='undefined'&&Number.isInteger(currentSlot)&&currentSlot>=0&&currentSlot<=3?currentSlot:null,
    saveWarning:document.querySelector('#summarySave')?.textContent==='Progress is available for this session only.',
    storage:'missing',schema:null,storedPlaceMatched:null,storedPendingMatched:null,storedPendingCapture:null,
    normalized:'not-read',canary:'missing',documentStart:window.__pr62docStart??null
   };
   try {
    const c=localStorage.getItem('pocket-reel-62-arrival-canary');
    out.canary=c===null?'missing':c==='fixture-v1'?'present':'other';
   }catch{out.canary='blocked';}
   let raw;
   try{raw=localStorage.getItem('thai-atlas-v2');}catch{out.storage='blocked';return out;}
   if(raw===null)return out;
   if(raw.length>8*1024*1024){out.storage='oversized';return out;}
   let s;
   try{s=JSON.parse(raw);}catch{out.storage='malformed';return out;}
   out.storage=s&&typeof s==='object'&&!Array.isArray(s)?'present':'wrong-shape';
   if(out.storage!=='present')return out;
   out.schema=Number.isSafeInteger(s.schema)?s.schema:null;
   out.storedPlaceMatched=Number.isInteger(place)?s.place===place:null;
   out.storedPendingMatched=Number.isInteger(species)?Array.isArray(s.pending)&&s.pending[0]===species:null;
   out.storedPendingCapture=s.pendingCapture!=null;
   if(typeof careerVault==='function'){
    try{out.normalized=careerVault().load()?'accepted':'empty';}catch{out.normalized='rejected';}
   }
   return out;
  })();
  return {observed,trace};
 }catch{return {observed,trace:{unavailable:true}};}
}
async function probeReload(page, expected) {
 try{return (await page.evaluate(readCheckpoint,expected)).trace;}
 catch{return {unavailable:true};}
}
const traceText=(before,after,pageErrors)=>'reload trace '+JSON.stringify({before,after,pageErrors});
module.exports={readCheckpoint,probeReload,traceText};
