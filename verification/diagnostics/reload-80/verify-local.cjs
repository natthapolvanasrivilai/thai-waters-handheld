'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.join(__dirname,'work/verification/browser-tests');
const {attach,evaluateBoundary,readWithProbe}=require(root+'/observe-paired-reload.cjs');
const {captureReloadStartup,readCheckpoint}=require(root+'/reload-trace.cjs');
const {exactBundle,serveExact}=require('./run-paired.cjs');
const text=(tree,n)=>fs.readFileSync(path.join(__dirname,tree,'verification/browser-tests',n+'.cjs'),'utf8');
test('exact original Gameplay assertions and pre-reload boundaries remain in instrumented file',()=>{
 const old=text('base','gameplay'),work=text('work','gameplay');
 for(const a of old.split('\n').map(x=>x.trim()).filter(x=>x.startsWith('assert')))assert(work.includes(a),a);
 assert.equal((work.match(/await pg\.reload\(\)/g)||[]).length,2);
 assert.doesNotMatch(work,/localStorage\.(setItem|removeItem|clear)\(/g);
 assert.equal(text('base','reload-trace'),text('work','reload-trace'));
 assert.equal(text('base','menu-controls'),text('work','menu-controls'));
 assert.match(work,/observer.remember\(identity,beforePendingProbe\);\s*try\{\s*await pg.reload\(\)/);
 assert.match(work,/observer.remember\(identity,beforeFiledProbe\);\s*try\{\s*await pg.reload\(\)/);
 for(const stage of ['gameplay-pending','gameplay-filed'])assert(work.includes("await report('"+stage+"',false);throw error;"));
});
test('exact pinned HTML bytes via loopback before and after same URL fetch',async()=>{
 const bytes=exactBundle(),server=await serveExact(bytes);
 try{
  for(const i of [0,1]){
   assert.match(server.url,/^http:\/\/127\.0\.0\.1:\d+\/Thai-Waters-play\.html$/);
   const response=await fetch(server.url);
   assert.equal(response.status,200);assert.equal(response.headers.get('cache-control'),'no-store');
   assert(Buffer.from(await response.arrayBuffer()).equals(bytes),i);
  }
  assert.equal((await fetch(server.url,{method:'POST'})).status,404);
  assert.equal((await fetch(new URL('/x',server.url))).status,404);
 }finally{await server.close();}
});
test('classifier partitions file loss before app, key-only loss, later overwrite, and route mismatch',()=>{
 const p={state:'present',size:22,fingerprint:100},m={state:'missing'},q={state:'present',size:22,fingerprint:200};
 const a={career:p,language:p,session:m},b={...a,state:'loading',type:'reload'},c={...a,state:'complete'};
 const id={sameURL:true,samePage:true,sameContext:true,sameTarget:true,sameFrame:true,changedLoader:true,
  newDocument:true,topNavigationCount:1,sameStorageKey:true};
 const boundary=(v=b,w=c,cert=id,failed=false)=>evaluateBoundary(a,v,w,cert,failed);
 assert.equal(boundary(),'career-retained');
 assert.equal(boundary({...b,career:m,language:m}),'career-and-language-missing-before-app');
 assert.equal(boundary({...b,career:m}),'career-only-missing-before-app');
 assert.equal(boundary(b,{...c,career:q}),'career-changed-after-app');
 assert.equal(boundary(b,c,{...id,sameStorageKey:false}),'storage-key-differed');
 assert.equal(boundary(b,c,{...id,sameFrame:false}),'unexpected-navigation-identity');
 assert.equal(boundary(b,c,id,true),'career-retained-live-assertion-failed');
});
test('actual integrated init script observes local and session first and adds no storage mutations',async()=>{
 const calls=[],local=new Map([['thai-atlas-v2','SYNTHETIC']]),session=new Map(),wrap=(label,map)=>({
  getItem(key){calls.push([label,'read',key]);return map.get(key)??null;},
  setItem(key,value){calls.push([label,'write',key]);map.set(key,value);}
 });
 const scope={location:new URL('file:///synthetic'),document:{readyState:'loading'},performance:{timeOrigin:10,getEntriesByType:()=>[{type:'reload'}]}};
 scope.localStorage=wrap('local',local);scope.sessionStorage=wrap('session',session);
 scope.window=scope;scope.top=scope;scope.self=scope;
 const mock={context:()=>({newCDPSession:async()=>({send:async()=>{},on(){}})}),addInitScript:async ({content})=>vm.runInNewContext(content,scope)};
 await attach(mock,captureReloadStartup,readCheckpoint);
 assert.equal(scope.__pocketReel80Probe.entry.career.state,'present');
 assert.equal(scope.__pocketReel80Probe.entry.language.state,'missing');
 assert.equal(scope.__pocketReel80Probe.entry.session.state,'missing');
 assert.deepEqual(calls.filter(x=>x[1]==='write'),[['local','write','thai-waters-language']]);
 const languageLookup=calls.findIndex(x=>x[1]==='read'&&x[2]==='thai-waters-language');
 const originalWrite=calls.findIndex(x=>x[1]==='write');assert(languageLookup>=0&&languageLookup<originalWrite);
 assert.equal(scope.__twReloadStartup62.language,'missing');
 assert.equal(scope.__pocketReel80Probe.snapshot().language.state,'present');
 const captured=await vm.runInNewContext('('+readWithProbe.toString()+')({})',scope);
 assert.equal(captured.startup.language,'missing');assert.equal(captured.probe.language.state,'present');
});
