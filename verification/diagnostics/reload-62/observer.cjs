const {createHash}=require('node:crypto');
const digest=s=>createHash('sha256').update(s).digest('hex').slice(0,16);
const canary='__tw_arrival_probe_62'; // synthetic isolated context only
// Function marshalled by Playwright; be independent of module scope.
function documentProbe({canary,seedEnglish}) {
  if (top!==self) return;
  const read=(store,key)=>{
    try {
      const raw=window[store].getItem(key);
      if (raw===null) return {state:'missing'};
      let h=2166136261;for(let j=0;j<raw.length;j++) h=Math.imul(h^raw.charCodeAt(j),16777619);
      return {state:'present',len:raw.length,fingerprint:(h>>>0).toString(16)};
    } catch(e) { return {state:'blocked',kind:e.name}; }
  };
  const snapshot=()=>{
    const nav=performance.getEntriesByType('navigation')[0];
    return {localCanary:read('localStorage',canary),career:read('localStorage','thai-atlas-v2'),
      sessionCanary:read('sessionStorage',canary),language:read('localStorage','thai-waters-language'),
      protocol:location.protocol,origin:location.origin,navigationType:nav?.type,ready:document.readyState,
      timeOrigin:performance.timeOrigin};
  };
  // IMPORTANT: read before the original test's language write. It may create the new storage namespace.
  const beforeApp=snapshot();
  globalThis.__twProbe62={beforeApp,snapshot};
  if(seedEnglish)localStorage.setItem('thai-waters-language','en'); // untouched original test behavior
}
function classify(x) {
 if(!x.beforeReload||!x.reloadEntry||!x.afterReady)return 'inconclusive';
 const a=x.beforeReload,b=x.reloadEntry,c=x.afterReady;
 const eq=(u,v)=>u?.state==='present'&&v?.state==='present'&&u.len===v.len&&u.fingerprint===v.fingerprint;
 const stable=(x.witness==='language'?'language':'localCanary');
 if(!x.sameURL||!x.sameContext||x.sameTarget===false||x.sameFrame===false||x.loaderChanged===false||x.navigationDelta===0||b.timeOrigin===a.timeOrigin)return 'test-setup-or-nav-identity';
 if(x.sameStorageKey===false)return 'chromium-storage-key-changed';
 if(x.sameStorageKey===null)return 'storage-key-unobservable';
 if(a.career.state!=='present'||a[stable].state!=='present')return 'precondition-failed';
 if(b.career.state==='blocked'||b[stable].state==='blocked')return 'preapp-storage-access-blocked';
 if(b.career.state==='missing'&&b[stable].state==='missing')
   return 'storage-namespace-unavailable-before-app';
 if(b.career.state==='missing'&&eq(a[stable],b[stable])) return 'key-specific-loss-before-app';
 if(!eq(a.career,b.career))return 'changed-career-before-app';
 if(!eq(b.career,c.career))return 'after-init-storage-mutation-or-access';
 if(x.witness==='localCanary'&&(!eq(a.sessionCanary,b.sessionCanary)||!eq(b.sessionCanary,c.sessionCanary)))return 'session-canary-changed';
 if(!eq(a[stable],b[stable]))return 'storage-witness-changed-before-app';
 if(!eq(b[stable],c[stable]))return 'after-init-witness-mutation-or-access';
 if(x.activePlaceMatched===false)return 'restore-live-replay';
 return 'storage-and-live-place-retained';
}
async function attach(page,{seedEnglish=true}={}) {
 const client=await page.context().newCDPSession(page);
 const topState={topNavigations:0,errorCount:0};
 await client.send('Page.enable');
 client.on('Page.frameNavigated',({frame,type})=>{if(!frame.parentId){
   topState.topNavigations++;topState.loader=frame.loaderId;topState.frame=frame.id;topState.navKind=type;
 }});
 page.on('pageerror',()=>topState.errorCount++);
 const id=async()=>{
   const result=await client.send('Target.getTargetInfo');
   const context=result.targetInfo.browserContextId;
   let storeKey=null;
   try{storeKey=(await client.send('Storage.getStorageKeyForFrame',{frameId:topState.frame})).storageKey;}catch{}
   return {...topState,target:digest(result.targetInfo.targetId),context:context==null?null:digest(context),key:storeKey==null?null:digest(storeKey)};
 };
 const caseMarker='case:'+digest(Math.random().toString());
 await page.addInitScript(documentProbe,{canary,seedEnglish});
 return {async seed({writeCanaries=true}={}){
   this.witness=writeCanaries?'localCanary':'language';
   if(writeCanaries)await page.evaluate(({canary,caseMarker})=>{
     localStorage.setItem(canary,caseMarker);sessionStorage.setItem(canary,caseMarker);
   },{canary,caseMarker});
   this.initialId=await id();this.initialURL=page.url();
 },async syntheticKey(){
   await page.evaluate(()=>localStorage.setItem('thai-atlas-v2',JSON.stringify({schema:4,probe:true,place:16})));
 },acceptBefore(snapshot){
    this.beforeReload=snapshot;

 },async before(){
   this.beforeReload=await page.evaluate(()=>globalThis.__twProbe62.snapshot());
 },async report(extra={}){
   const afterReady=await page.evaluate(()=>({entry:globalThis.__twProbe62.beforeApp,live:globalThis.__twProbe62.snapshot()}));
   const final=await id();
   const result={sameURL:page.url()===this.initialURL,sameContext:final.context!=null&&final.context===this.initialId.context,sameTarget:final.target===this.initialId.target,
     sameFrame:this.initialId.frame!=null&&final.frame===this.initialId.frame,
     loaderChanged:this.initialId.loader!=null&&final.loader!=null&&final.loader!==this.initialId.loader,
     sameStorageKey:this.initialId.key!=null&&final.key!=null?final.key===this.initialId.key:null,
     navigationDelta:final.topNavigations-this.initialId.topNavigations,canaryPolicy:this.witness==='language'?'existing-language-no-extra-writes':'seeded-local-and-session',witness:this.witness,
     beforeReload:this.beforeReload,reloadEntry:afterReady.entry,afterReady:afterReady.live,...extra};
   return {...result,pageErrorCount:final.errorCount,classification:classify(result)};
 }};
}
module.exports={attach,classify,documentProbe};
