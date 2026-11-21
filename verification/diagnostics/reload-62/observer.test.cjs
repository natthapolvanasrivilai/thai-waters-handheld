const {test}=require('node:test');const assert=require('node:assert/strict');const {classify}=require('./observer.cjs');
const p={state:'present',len:1,fingerprint:'p'};const m={state:'missing'},q={state:'present',len:2,fingerprint:'q'};
const p0={timeOrigin:1,career:p,localCanary:p};const p1={...p0,timeOrigin:2};
const trial=(patch)=>({sameURL:true,sameContext:true,beforeReload:p0,reloadEntry:p1,afterReady:p1,...patch});
for(const [n,x,w] of [
 ['same state',{},'storage-and-live-place-retained'],
 ['missing both before app',{reloadEntry:{...p1,career:m,localCanary:m}},'storage-namespace-unavailable-before-app'],
 ['only career missing',{reloadEntry:{...p1,career:m}},'key-specific-loss-before-app'],
 ['key overwritten after app start',{afterReady:{...p1,career:q}},'after-init-storage-mutation-or-access'],
 ['preserved raw, wrong UI',{activePlaceMatched:false},'restore-live-replay'],
 ['URL changed',{sameURL:false},'test-setup-or-nav-identity'],
 ['context changed',{sameContext:false},'test-setup-or-nav-identity'],
 ['no new document',{reloadEntry:p0},'test-setup-or-nav-identity'],
 ['blocked access',{reloadEntry:{...p1,career:{state:'blocked'}}},'preapp-storage-access-blocked']
])test(n,()=>assert.equal(classify(trial(x)),w));

const vm=require('node:vm');
const {attach}=require('./observer.cjs');
test('paired mocked File and loopback: init sees canaries before any app/English write',async()=>{
  for(const [url,fault] of [['file:///tmp/synthetic.html','local-drop'],['http://127.0.0.1:8123/synthetic.html',null]]){
    const parsed=new URL(url);
    let local=new Map(),session=new Map(),scope,init,now=100,epoch=0,storageWitnessCalls=0;
    const listeners={};
    const wrap=map=>({getItem:key=>map.get(key)??null,setItem:(k,v)=>map.set(k,v)});
    const CDP={
      on:(n,f)=>{listeners[n]=f;},
      send:async(n,opts)=>{
        if(n==='Target.getTargetInfo')return {targetInfo:{targetId:'target',browserContextId:'fresh-ctx'}};
        if(n==='Storage.getStorageKeyForFrame'){assert.equal(opts.frameId,'frame');storageWitnessCalls++;return {storageKey:parsed.origin};}
        return {};
      }
    };
    const page={context:()=>({newCDPSession:async()=>CDP}),on:()=>{},url:()=>url,
      addInitScript:async(f,arg)=>{init=[f,arg];},
      evaluate:async(f,arg)=>{scope.arg=arg;return vm.runInNewContext('('+f.toString()+')(arg)',scope);}};
    const newDoc=()=>{
      ++epoch;now+=10;
      scope={window:{localStorage:wrap(local),sessionStorage:wrap(session)},location:parsed,document:{readyState:'loading'},
        performance:{getEntriesByType:()=>[{type:epoch===1?'navigate':'reload'}],timeOrigin:now}};
      scope.self=scope;scope.top=scope;scope.localStorage=scope.window.localStorage;scope.sessionStorage=scope.window.sessionStorage;
      listeners['Page.frameNavigated']({frame:{id:'frame',loaderId:'loader-'+epoch},type:'Navigation'});
      return page.evaluate(...init);
    };
    const probe=await attach(page,{seedEnglish:false});
    await newDoc();await probe.seed();await probe.syntheticKey();await probe.before();
    if(fault)local=new Map();
    await newDoc();await page.evaluate(()=>{document.readyState='complete';});
    const report=await probe.report();
    assert.equal(storageWitnessCalls,2);
    assert.equal(report.sameURL,true);assert.equal(report.sameContext,true);assert.equal(report.sameTarget,true);
    assert.equal(report.sameStorageKey,true);assert.equal(report.sameFrame,true);
    assert.equal(report.loaderChanged,true);assert.equal(report.navigationDelta,1);
    assert.equal(report.reloadEntry.sessionCanary.state,'present');assert.equal(report.reloadEntry.ready,'loading');
    assert.equal(report.beforeReload.localCanary.state,'present');
    assert.equal(report.reloadEntry.language.state,'missing');
    assert.equal(report.classification,fault?'storage-namespace-unavailable-before-app':'storage-and-live-place-retained');
  }
});
test('actual Arrival witness: existing language missing before original initializer, present afterward',()=>{
  const {documentProbe}=require('./observer.cjs');
  const m=new Map();const storage={getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v)};
  const sc={arg:{canary:'synthetic-unused',seedEnglish:true},window:{localStorage:storage,sessionStorage:storage},
    localStorage:storage,location:new URL('file:///tmp/synthetic.html'),document:{readyState:'loading'},
    performance:{timeOrigin:3,getEntriesByType:()=>[]}};
  sc.self=sc;sc.top=sc;
  vm.runInNewContext('('+documentProbe.toString()+')(arg)',sc);
  assert.equal(sc.__twProbe62.beforeApp.language.state,'missing');
  assert.equal(sc.__twProbe62.snapshot().language.state,'present');
  assert.deepEqual([...m.keys()],['thai-waters-language']);
});
