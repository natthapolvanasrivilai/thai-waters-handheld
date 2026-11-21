const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const dir=path.resolve(__dirname,'../../game/src');
const script=path.join(dir,'career-storage.js');
const ctx=vm.createContext({});
vm.runInContext(fs.existsSync(script)?fs.readFileSync(script,'utf8'):'',ctx);
const legacy={schema:3,history:[{id:2,cm:18,grams:184},{uid:'aa',id:3,cm:7,grams:47,at:1720000000000,place:4,period:3,weather:2,bait:8}],pendingCapture:{id:4,cm:15,grams:91,place:4},pending:[4,15,20261120],site:0,place:4,time:2,weather:1,finish:1,bait:8,rig:2,book:[[0,0],[1,12],[2,18]],rank:[1,2,0]};
const read=JSON.stringify(legacy),storage={value:read,fail:false,key:null,getItem(){return this.value;},setItem(key,v){if(this.fail)throw Error('quota');this.value=v;this.key=key;}};
Object.assign(ctx,{legacy,storage});
function run(script){return vm.runInContext(script,ctx)}
function plain(x){return JSON.parse(JSON.stringify(x))}
run('const vault=makeCareerStorage(storage,{fish:5,places:6});const legacyCareer=vault.load();');
assert.equal(storage.value,read,'migration must not write on read');
const v=plain(run('legacyCareer'));
assert.equal(v.schema,4);delete v.schema;
const legacyCopy={...legacy};delete legacyCopy.schema;assert.deepEqual(v,legacyCopy);
const exported=run('vault.exportBackup(legacyCareer)');
const decoded=plain(run('vault.parseBackup(vault.exportBackup(legacyCareer))'));
assert.deepEqual(decoded,plain(run('legacyCareer')));
assert.throws(()=>run('vault.parseBackup("wrong")'));
assert.throws(()=>run('vault.parseBackup(JSON.stringify({format:"Pocket Reel career",version:99,career:legacyCareer}))'));
assert.throws(()=>run('vault.parseBackup(JSON.stringify({...JSON.parse(vault.exportBackup(legacyCareer)),career:{...legacyCareer,book:[[1,-20]]}}))'));
assert.throws(()=>run('vault.parseBackup(JSON.stringify({...JSON.parse(vault.exportBackup(legacyCareer)),career:{...legacyCareer,history:[{id:9,cm:1,grams:2}]}}))'));
assert.throws(()=>run('vault.parseBackup(JSON.stringify({...JSON.parse(vault.exportBackup(legacyCareer)),career:{...legacyCareer,pending:[4,22,0]}}))'));
assert.throws(()=>run('vault.parseBackup(" ".repeat(8*1024*1024+1))'));
storage.fail=true;assert.throws(()=>run('vault.commit(legacyCareer)'));assert.equal(storage.value,read);
storage.fail=false;run('vault.commit(legacyCareer)');assert.equal(storage.key,'thai-atlas-v2');
assert.deepEqual(plain(run('vault.load()')),decoded);
storage.value='{"schema":99,"book":[]}';assert.throws(()=>run('vault.load()'));assert.throws(()=>run('vault.commit(legacyCareer)'));assert.equal(storage.value,'{"schema":99,"book":[]}');
storage.value='{"site":2,"book":[[1,12]],"rank":[1,0,0]}';
const oldest=plain(run('vault.load()'));assert.equal(oldest.place,2);assert.deepEqual(oldest.book,[[1,12]]);assert.deepEqual(oldest.pending,null);
storage.value=read;run("vault.commit(legacyCareer,{replace:true})");assert.deepEqual(plain(run("vault.load().pending")),[4,15,0],"Imported catch stays local, never enters Cup");
assert.match(exported,/"format":/);console.log('PASS valid legacy and schema 4, catches/PBs, pending, round trip, invalid input, transactional quota failure and unknown-schema protection');

{
 const makeGuard=run('typeof makeFileCareerGuard==="function" ? makeFileCareerGuard : null');
 assert.equal(typeof makeGuard,'function','file career guard must be available');
 const makeVault=run('makeCareerStorage');
 const opts={fish:5,places:6};
 const entry={state:{untouched:1},marks:0,replaceState(state){this.state=state;this.marks++;}};
 const jar={value:null,denied:false,reads:0,writes:0,getItem(key){
  assert.equal(key,'thai-atlas-v2');this.reads++;if(this.denied)throw Error('denied');return this.value;
 },setItem(key,value){assert.equal(key,'thai-atlas-v2');this.writes++;this.value=value;}};
 const openFile=guard=>makeVault(jar,{...opts,beforeWrite:guard.beforeWrite});
 const first=makeGuard(true,entry);
 assert.equal(openFile(first).load(),null);
 openFile(first).commit(decoded);first.markKnown();first.markKnown();
 assert.equal(jar.writes,1);assert.equal(entry.marks,1);
 assert.deepEqual(plain(entry.state),{untouched:1,pocketReelCareerKnown:true});
 const original=jar.value;
 const sameEntry=makeGuard(true,entry);jar.value=null;
 assert.throws(()=>sameEntry.beforeWrite(openFile(sameEntry).load()),/unavailable/);
 assert.equal(sameEntry.recovering,true);
 assert.throws(()=>openFile(sameEntry).commit(decoded),/unavailable/);
 assert.throws(()=>openFile(sameEntry).commit(decoded,{replace:true}),/unavailable/);
 assert.equal(jar.value,null);assert.equal(jar.writes,1);
 jar.value=original;
 assert.throws(()=>openFile(sameEntry).commit(decoded,{replace:true}),/unavailable/);
 assert.equal(jar.value,original);assert.equal(jar.writes,1);

 for(const [bytes,denied] of [['{corrupt',false],[original,true]]){
  jar.value=bytes;jar.denied=denied;
  const blocked=makeGuard(true,entry),guarded=openFile(blocked);
  assert.throws(()=>guarded.load());
  assert.throws(()=>guarded.commit(decoded));
  assert.throws(()=>guarded.commit(decoded,{replace:true}));
  const reads=jar.reads;
  assert.deepEqual(plain(guarded.parseBackup(guarded.exportBackup(decoded))),decoded);
  assert.equal(jar.reads,reads,'backup preview/export must not access the file career key');
  assert.equal(jar.value,bytes);assert.equal(jar.writes,1);
 }
 const hosted=makeVault(jar,opts);jar.denied=false;jar.value='{corrupt';
 hosted.commit(decoded,{replace:true});
 const replacement=plain(hosted.load());
 assert.equal(jar.writes,2);assert.equal(entry.marks,1);
 assert.deepEqual(replacement.pending,[4,15,0]);
 assert.deepEqual(replacement.pendingCapture,decoded.pendingCapture);
 assert.deepEqual(replacement.history,decoded.history);
 console.log('PASS marked file loss refuses overwrite, damaged/denied stays intact, read-only backup, hosted explicit replacement preserved');
}
