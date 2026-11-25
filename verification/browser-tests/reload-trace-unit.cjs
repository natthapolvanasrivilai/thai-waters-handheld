const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm');
const {readCheckpoint,probeReload,traceText}=require('./reload-trace.cjs');

function pageWith(raw,{deny=false,ready=true,phase=5,visible=true,nativePlace=14}={}){
 const entries={ '#act':{disabled:!ready},'#catchContinue':{hidden:!visible},'#summarySave':{textContent:''}};
 return {evaluate:(fn,args)=>vm.runInNewContext('('+fn.toString()+')(args)',{
  args,location:{protocol:'file:',href:'file:///SHOULD_NOT_LOG'},document:{readyState:'complete',querySelector:id=>entries[id]},
  g:ready?{state:()=>phase,grams:()=>150}:undefined,placeId:nativePlace,window:{castProbe:Promise.resolve(2)},
  localStorage:{getItem(k){ assert.equal(k,'thai-atlas-v2');if(deny)throw new Error('SHOULD_NOT_LOG access details');return raw;}},
  careerVault:()=>({load:()=>JSON.parse(raw)}),
 })};
}
const synthetic=JSON.stringify({schema:4,place:14,pending:[40,50,0],pendingCapture:{id:40,uid:'SHOULD_NOT_LOG'},history:['SHOULD_NOT_LOG']});
test('records exact phase and only expected-vs-observed flags',async()=>{
 const a=await probeReload(pageWith(synthetic),{place:14,species:40});
 assert.deepEqual({...a},{protocol:'file:',documentReady:'complete',ready:true,phase:5,continueShown:true,activePlaceMatched:true,selectedTimeMode:null,activeSlot:null,saveWarning:false,storage:'present',schema:4,storedPlaceMatched:true,storedPendingMatched:true,storedPendingCapture:true,normalized:'accepted'});
 assert(!traceText(a,a,2).includes('SHOULD_NOT_LOG'));
 const page=pageWith(synthetic);
 assert.equal((await page.evaluate(readCheckpoint,{observe:'cast'})).observed,2);
 assert.equal((await page.evaluate(readCheckpoint,{observe:'weight'})).observed,150);
});
test('distinguishes absent, blocked and malformed storage',async()=>{
 for(const [raw,deny,status] of [[null,false,'missing'],[null,true,'blocked'],['SHOULD_NOT_LOG',false,'malformed']]){
  const a=await probeReload(pageWith(raw,{deny,ready:false,visible:false}),{place:14,species:40});
  assert.equal(a.storage,status);assert.equal(a.ready,false);assert.equal(a.phase,null);assert.equal(a.continueShown,false);
  assert(!traceText(a,null,0).includes('SHOULD_NOT_LOG'));
 }
});
test('tolerates a closed or reloading context and preserves original error path',async()=>{
 assert.deepEqual(await probeReload({evaluate(){throw Error('SHOULD_NOT_LOG');}},{place:14}),{unavailable:true});
});
test('separates wrong saved selection, normalization rejection and native/Continue state',async()=>{
 const mismatched=await probeReload(pageWith(JSON.stringify({schema:4,place:0,pending:null}),{nativePlace:14,phase:0,visible:false}),{place:14,species:40});
 assert.equal(mismatched.activePlaceMatched,true);assert.equal(mismatched.storedPlaceMatched,false);
 assert.equal(mismatched.storedPendingMatched,false);assert.equal(mismatched.phase,0);assert.equal(mismatched.continueShown,false);
 const nativeNotRestored=await probeReload(pageWith(synthetic,{nativePlace:0,phase:0,visible:false}),{place:14,species:40});
 assert.equal(nativeNotRestored.normalized,'accepted');assert.equal(nativeNotRestored.storedPendingMatched,true);
 assert.equal(nativeNotRestored.activePlaceMatched,false);assert.equal(nativeNotRestored.phase,0);
 const vaultRejected={evaluate:(fn,args)=>vm.runInNewContext('('+fn.toString()+')(args)',{
  args,location:{protocol:'http:'},document:{readyState:'complete',querySelector:()=>null},
  localStorage:{getItem:()=>synthetic},careerVault:()=>({load(){throw Error('SHOULD_NOT_LOG');}})
 })};
 const rejected=await probeReload(vaultRejected,{place:14,species:40});
 assert.equal(rejected.normalized,'rejected');assert.equal(rejected.storedPendingMatched,true);
 assert(!traceText(rejected,null,0).includes('SHOULD_NOT_LOG'));
});

const {captureReloadStartup,reloadFailureText}=require('./reload-trace.cjs');
// Fresh isolated document over a synthetic store. Observe the actual init function,
// then inject loss at a specific boundary; no reliance on timing or browser storage.
function fixture({epoch,career,language='en',deny=false,topLevel=true}){
 const bucket=new Map();if(career!==null)bucket.set('thai-atlas-v2',career);
 if(language!==null)bucket.set('thai-waters-language',language);
 const writes=[];
 const scope={document:{readyState:'loading',querySelector:()=>null},
  window:{},location:{protocol:'file:',href:'file:///SHOULD_NOT_LOG'},performance:{timeOrigin:epoch},
  localStorage:{getItem(k){if(deny&&k==='thai-atlas-v2')throw Error('SHOULD_NOT_LOG');return bucket.get(k)??null;},
    setItem(k,v){writes.push([k,v]);bucket.set(k,v);}}};
 scope.top=scope;scope.self=topLevel?scope:{};
 const page={evaluate:(f,args)=>vm.runInNewContext('('+f.toString()+')(args)',{...scope,args})};
 return {scope,bucket,writes,page,
  init:()=>page.evaluate(captureReloadStartup),
  ready(){scope.document.readyState='complete';scope.document.querySelector=id=>id==='#act'?{disabled:false}:null;}};
}
const rendered=async(f,old)=>JSON.parse((await reloadFailureText(f.page,{
 stage:'arrival-mobile',before:{storage:'present'},beforeStartup:old,expected:{place:14},pageErrors:0
})).slice('reload trace '.length));
test('different results for lost before app and lost after document-start',async()=>{
 const old=fixture({epoch:100,career:synthetic});await old.init();
 const beforeStartup=old.scope.window.__twReloadStartup62;
 const filePartition=fixture({epoch:200,career:null,language:null});await filePartition.init();filePartition.ready();
 const bootMutation=fixture({epoch:200,career:synthetic});await bootMutation.init();
 bootMutation.bucket.delete('thai-atlas-v2');bootMutation.ready();
 const a=await rendered(filePartition,beforeStartup),b=await rendered(bootMutation,beforeStartup);
 assert.equal(a.after.storage,'missing');assert.equal(b.after.storage,'missing');
 assert.deepEqual(a.boundary,{newDocument:true,documentReady:'loading',career:'missing',language:'missing',classification:'missing-before-app'});
 assert.deepEqual(b.boundary,{newDocument:true,documentReady:'loading',career:'present',language:'present',classification:'lost-after-document-start'});
 assert.deepEqual(filePartition.writes,[['thai-waters-language','en']]);assert.deepEqual(bootMutation.writes,filePartition.writes);
 assert.equal(a.stage,'arrival-mobile');assert(!JSON.stringify({a,b}).includes('SHOULD_NOT_LOG'));
 assert(!Object.hasOwn(b.boundary,'epoch'));
});
test('does not mistake an old document or incomplete boot for a storage loss',async()=>{
 const f=fixture({epoch:200,career:synthetic});await f.init();
 const before=f.scope.window.__twReloadStartup62;
 assert.equal((await rendered(f,before)).boundary.classification,'reload-did-not-replace-document');
 assert.equal((await rendered(f,{epoch:100})).boundary.classification,'present-before-app-post-ready-unavailable');
 const unreadable={page:{evaluate(){throw Error('SHOULD_NOT_LOG');}}};const a=await rendered(unreadable,before);
 assert.equal(a.boundary.classification,'document-start-unavailable');assert.deepEqual(a.after,{unavailable:true});
 assert(!JSON.stringify(a).includes('SHOULD_NOT_LOG'));
});
test('read denial is distinct and cross-frame init preserves only the original language write',async()=>{
 const f=fixture({epoch:200,career:synthetic,deny:true});await f.init();f.ready();
 assert.equal((await rendered(f,{epoch:100})).boundary.classification,'blocked-before-app');
 const sub=fixture({epoch:200,career:synthetic,topLevel:false});await sub.init();
 assert.equal(sub.scope.window.__twReloadStartup62,undefined);
 assert.deepEqual(sub.writes,[['thai-waters-language','en']]);
});

// Also exercise the Recovery panel's async backup-preview guard in this CI lane.
require('./startup-recovery-unit.cjs');
