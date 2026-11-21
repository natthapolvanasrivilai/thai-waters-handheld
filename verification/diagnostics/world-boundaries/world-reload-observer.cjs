// Local test-only observer. Never print URLs, raw save bytes, identifiers or fingerprints.
const {readCheckpoint,storageBoundary}=require('./reload-trace.cjs');
function captureWorldStartup(){
 try {
  if(top===self){
   const status=k=>{try{return localStorage.getItem(k)===null?'missing':'present';}catch{return 'blocked';}};
   let raw=null;try{raw=localStorage.getItem('thai-atlas-v2');}catch{}
   const hash=raw===null||raw.length>8*1024*1024||!crypto.subtle?Promise.resolve(null):
       crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw)).then(x=>[...new Uint8Array(x)].join(','),()=>null);
   Object.defineProperty(window,'__twWorldReload',{value:Object.freeze({
    career:status('thai-atlas-v2'),language:status('thai-waters-language'),
    marker:(()=>{try{return history.state?.pocketReelCareerKnown===true;}catch{return null;}})(),
    documentReady:document.readyState,epoch:performance.timeOrigin,hash
   })});
  }
 }catch{} // Observation must not affect original fixture behavior.
 localStorage.setItem('thai-waters-language','en'); // original fixture write from same init script
}
async function worldBefore(page,kind,species=null){
 try{
  if(species===null)species=await page.evaluate(()=>g.species());
  const before=await page.evaluate(async({kind,species})=>{
   let raw=null;
   try{raw=localStorage.getItem('thai-atlas-v2');}catch{return {storage:'blocked'};}
   if(raw===null)return {storage:'missing'};
   if(raw.length>8*1024*1024)return {storage:'oversized'};
   let decoded=null;try{decoded=careerVault().load();}catch{}
   const invariant=decoded?(kind==='pending'?
    decoded.pending?.[0]===species&&decoded.pendingCapture?.id===species&&g.state()===5:
    Array.isArray(decoded.book?.[species])&&decoded.book[species][0]===g.caught(species)&&g.caught(species)===1):false;
   const hash=crypto.subtle?await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw)).then(x=>[...new Uint8Array(x)].join(','),()=>null):null;
   return {storage:'present',codecAccepted:!!decoded,invariant,hash,marker:history.state?.pocketReelCareerKnown===true};
  },{kind,species});
  const start=await page.evaluate(()=>{const a=window.__twWorldReload;return a?{epoch:a.epoch,marker:a.marker}:null;});
  return {before,start,species,kind};
 }catch{return null;}
}
async function worldReceipt(stage,page,checkpoint){
 if(!checkpoint)return console.log('synthetic world reload trace '+JSON.stringify({stage,observationUnavailable:true}));
 const {species,start,before,kind}=checkpoint;
 let after,startup,matches;
 try{after=(await page.evaluate(readCheckpoint,{species})).trace;}catch{}
 try{
  startup=await page.evaluate(async()=>{const s=window.__twWorldReload;if(!s)return null;return {...s,hash:await s.hash};});
  matches=before?.hash&&startup?.hash?before.hash===startup.hash:null;
 }catch{}
 let recovery=null;
 try{recovery=await page.evaluate(()=>typeof fileCareerGuard==='undefined'?null:fileCareerGuard.recovering===true);}catch{}
 const boundary=storageBoundary(start,startup,after);
 console.log('synthetic world reload trace '+JSON.stringify({stage,kind,preWriteBoundary:{
  storage:before?.storage??null,codecAccepted:before?.codecAccepted??null,fixtureInvariantMatched:before?.invariant??null,knownMarker:before?.marker??null
 },newDocument:boundary.newDocument,preAppReady:boundary.documentReady,preAppStorage:boundary.career,
 preAppKnownMarker:startup?.marker??null,preAppExactBytesMatchPreReload:matches??null,classification:boundary.classification,
 afterAppReady:after?.ready??null,afterAppPhase:after?.phase??null,afterAppStorage:after?.storage??null,
 afterAppCodec:after?.normalized??null,afterAppGuardLocked:recovery}));
}
module.exports={captureWorldStartup,worldBefore,worldReceipt};
