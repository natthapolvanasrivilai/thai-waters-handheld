'use strict';

// Single self-contained document-init function, also tested in Node with mock storage.
function traceDocumentStart({expectedPlace}) {
 const canaryKey='pocket-reel-62-arrival-canary', canaryValue='fixture-v1';
 const nav=performance.getEntriesByType('navigation')[0]?.type;
 const navigation=['navigate','reload','back_forward'].includes(nav)?nav:'unavailable';
 const out={navigation, storage:'missing', schema:null, matched:null, canary:'missing'};
 // Seed only the normal initial navigation. Never recreate a vanished canary on reload.
 if(navigation==='navigate'){
  try{localStorage.setItem(canaryKey,canaryValue);}catch{}
 }
 try{
  const c=localStorage.getItem(canaryKey);
  out.canary=c===null?'missing':c===canaryValue?'present':'other';
 }catch{out.canary='blocked';}
 try{
  const raw=localStorage.getItem('thai-atlas-v2');
  if(raw!==null){
   if(raw.length>8*1024*1024)out.storage='oversized';
   else{
    try{
     const s=JSON.parse(raw);
     if(s&&typeof s==='object'&&!Array.isArray(s)){
      out.storage='present';out.schema=Number.isSafeInteger(s.schema)?s.schema:null;
      out.matched=s.place===expectedPlace;
     }else out.storage='wrong-shape';
    }catch{out.storage='malformed';}
   }
  }
 }catch{out.storage='blocked';}
 Object.defineProperty(window,'__pr62docStart',{value:Object.freeze(out)});
 // Preserve the original Arrival test's language setup and ordering before app startup.
 localStorage.setItem('thai-waters-language','en');
}

module.exports={traceDocumentStart};
