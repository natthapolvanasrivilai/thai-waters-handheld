// Only for exact synthetic browser regressions; no literal URLs, save payloads,
// catch IDs, species names, or exception messages are emitted.
// As a single Playwright init script, read both keys before the pre-existing
// language fixture write. Only flags live on the isolated test document.
function captureReloadStartup() {
 try{
  if(top===self){
   const status=key=>{try{return localStorage.getItem(key)===null?'missing':'present';}catch{return 'blocked';}};
   Object.defineProperty(window,'__twReloadStartup62',{value:Object.freeze({
    career:status('thai-atlas-v2'),language:status('thai-waters-language'),
    documentReady:document.readyState,epoch:performance.timeOrigin
   })});
  }
 }catch{} // Observation must not interrupt the existing fixture setup.
 localStorage.setItem('thai-waters-language','en');
}

async function readCheckpoint({place,placeName,species,observe}) {
 const observed=observe==='cast'?await window.castProbe:observe==='weight'?g.grams():null;
 const startup=typeof window==='undefined'?null:window.__twReloadStartup62??null;
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
    normalized:'not-read'
   };
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
  return {observed,trace,startup};
 }catch{return {observed,trace:{unavailable:true},startup};}
}
async function probeReload(page, expected) {
 try{return (await page.evaluate(readCheckpoint,expected)).trace;}
 catch{return {unavailable:true};}
}
function storageBoundary(beforeStartup,afterStartup,after) {
 const allowed=['missing','present','blocked'];
 const newDocument=Number.isFinite(beforeStartup?.epoch)&&Number.isFinite(afterStartup?.epoch)
  ?beforeStartup.epoch!==afterStartup.epoch:null;
 const documentReady=['loading','interactive','complete'].includes(afterStartup?.documentReady)?afterStartup.documentReady:null;
 const career=allowed.includes(afterStartup?.career)?afterStartup.career:null;
 const language=allowed.includes(afterStartup?.language)?afterStartup.language:null;
 let classification='document-start-unavailable';
 if(newDocument===false)classification='reload-did-not-replace-document';
 if(newDocument&&documentReady==='loading'&&career){
  if(career==='missing')classification='missing-before-app';
  else if(career==='blocked')classification='blocked-before-app';
  else if(!after?.ready)classification='present-before-app-post-ready-unavailable';
  else if(after.storage==='missing')classification='lost-after-document-start';
  else if(after.storage==='blocked')classification='blocked-after-document-start';
  else if(after.storage==='present')classification='present-at-both-boundaries';
  else classification='post-start-other-storage-state';
 }
 return {newDocument,documentReady,career,language,classification};
}
async function reloadFailureText(page,{stage,before,beforeStartup,expected,pageErrors}) {
 let result=null;
 try{result=await page.evaluate(readCheckpoint,expected);}catch{}
 const after=result?.trace??{unavailable:true};
 return 'reload trace '+JSON.stringify({stage,before,after,pageErrors,
  boundary:storageBoundary(beforeStartup,result?.startup,after)});
}
const traceText=(before,after,pageErrors)=>'reload trace '+JSON.stringify({before,after,pageErrors});
module.exports={captureReloadStartup,readCheckpoint,probeReload,traceText,storageBoundary,reloadFailureText};
