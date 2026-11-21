const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm');
const {snapshotStorage,diagnose,expectedStored}=require('./reload-boundary.cjs');
const fixture=[['thai-atlas-v2',JSON.stringify({schema:4,place:3,pending:[40,18,0],book:Array.from({length:41},(_,i)=>i===40?[1,22]:[0,0]),finish:1,private:'must not escape'})],['pocket-reel-62-ci-canary','synthetic']];
function observe(rows,throws=new Set(),cm){
 const storage=new Map(rows);
 return vm.runInNewContext('('+snapshotStorage.toString()+')({place:3,species:40,cm})',{cm,localStorage:{getItem(k){if(throws.has(k))throw Error('private unprinted');return storage.get(k)??null;}}});
}
test('document-start probe reports only flags and never payloads',()=>{
 assert.deepEqual(JSON.parse(JSON.stringify(observe(fixture))),{
  key:'present',schema:4,canary:'present',place:true,pending:true,filed:true,finish:true
 });
 const s=observe([['thai-atlas-v2','private invalid JSON'],fixture[1]]);
 assert.equal(s.key,'malformed');assert.equal(s.canary,'present');assert.doesNotMatch(JSON.stringify(s),/private|synthetic|22/);
});
test('fixture lengths are matched without emitting values',()=>{
 const pending=observe(fixture,new Set(),18),filed=observe(fixture,new Set(),22);
 assert(pending.pending&&!pending.filed);assert(filed.filed&&!filed.pending);
});
test('blocked application storage does not erase separately observed canary',()=>{
 const s=observe(fixture,new Set(['thai-atlas-v2']));
 assert.equal(s.key,'blocked');assert.equal(s.canary,'present');
});
test('distinguishes pre-bootstrap storage loss, post-bootstrap mutation and restore failure',()=>{
 const pending=observe(fixture.map(([key,data])=>[key,key==='thai-atlas-v2'?JSON.stringify({...JSON.parse(data),book:[]}):data]));
 const before=observe(fixture.map(([key,data])=>[key,key==='thai-atlas-v2'?JSON.stringify({...JSON.parse(data),pending:null}):data]));
 const empty=observe([]),keyOnly=observe([fixture[1]]);
 assert(expectedStored('pending',pending));assert(expectedStored('destination',pending));
 assert(!expectedStored('filed',pending));assert(!expectedStored('pending',before));
 const valid={storage:before,verified:true};
 assert.equal(diagnose({shape:'filed',start:before,ready:valid}), 'pass');
 assert.equal(diagnose({shape:'filed',start:empty,ready:{storage:empty,verified:false}}),'namespace-empty-before-app');
 assert.equal(diagnose({shape:'filed',start:keyOnly,ready:{storage:keyOnly,verified:false}}),'career-key-missing-before-app');
 assert.equal(diagnose({shape:'filed',start:before,ready:{storage:empty,verified:false}}),'persisted-state-changed-during-boot');
 assert.equal(diagnose({shape:'filed',start:before,ready:{storage:before,verified:false}}),'career-present-but-not-restored');
 assert.equal(diagnose({shape:'filed',start:before,ready:null}),'readiness-failed');
});
