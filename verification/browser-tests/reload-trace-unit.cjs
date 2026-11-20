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
