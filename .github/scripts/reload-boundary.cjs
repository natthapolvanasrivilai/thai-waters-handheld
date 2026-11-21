// Manual synthetic #62 probe. Do not run with a real browser profile or publish save data.
const assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs/promises');
const http=require('node:http'),path=require('node:path'),{pathToFileURL}=require('node:url');
const canaryKey='pocket-reel-62-ci-canary';
function snapshotStorage(expected){
 const result={key:'missing',schema:null,canary:'missing',place:false,pending:false,filed:false,finish:false};
 let raw,data;
 try{
  const value=localStorage.getItem('pocket-reel-62-ci-canary');
  result.canary=value==='synthetic'?'present':value===null?'missing':'different';
 }catch{result.canary='blocked';}
 try{raw=localStorage.getItem('thai-atlas-v2');}catch{result.key='blocked';return result;}
 if(raw===null)return result;
 if(raw.length>8*1024*1024){result.key='oversized';return result;}
 try{data=JSON.parse(raw);}catch{result.key='malformed';return result;}
 if(!data||typeof data!=='object'||Array.isArray(data)){result.key='wrong-shape';return result;}
 result.key='present';result.schema=Number.isSafeInteger(data.schema)?data.schema:null;
 const row=data.book?.[expected.species];
 result.place=data.place===expected.place;result.pending=data.pending?.[0]===expected.species&&(expected.cm===undefined||data.pending[1]===expected.cm);
 result.filed=Array.isArray(row)&&row[0]===1&&(expected.cm===undefined?row[1]>0:row[1]===expected.cm);result.finish=data.finish===1;
 return result;
}
function expectedStored(shape,x){
 return x?.key==='present'&&x.schema===4&&(
  shape==='destination'?x.place:shape==='pending'?x.pending&&!x.filed:!x.pending&&x.filed&&x.finish
 );
}
function diagnose({shape,start,ready}){
 if(!start)return 'document-start-unavailable';
 if(start.key==='blocked'||start.canary==='blocked')return 'document-start-storage-blocked';
 if(start.canary==='missing'&&start.key==='missing')return 'namespace-empty-before-app';
 if(start.canary==='present'&&start.key==='missing')return 'career-key-missing-before-app';
 if(start.canary!=='present')return 'canary-unavailable-before-app';
 if(!expectedStored(shape,start))return 'wrong-career-state-before-app';
 if(!ready)return 'readiness-failed';
 if(ready.storage.canary!=='present'||!expectedStored(shape,ready.storage))return 'persisted-state-changed-during-boot';
 return ready.verified?'pass':'career-present-but-not-restored';
}
async function observe(page,expected,shape){
 const storage=await page.evaluate(snapshotStorage,expected);
 const state=await page.evaluate(({place,species})=>{
  let normalized='unread';
  try{normalized=careerVault().load()?'accepted':'empty';}catch{normalized='rejected';}
  return {normalized,atPlace:placeId===place,landed:g.state()===5,continued:!$('catchContinue').hidden,
   caught:g.caught(species),best:g.best(species),heldWeight:g.state()===5?g.grams():null,finish:finish===1,
   warning:!!$('summarySave').textContent};
 },expected);
 return {storage,state,shape};
}
function verified(sample,reference){
 const {state,shape}=sample;
 if(shape==='pending')return state.normalized==='accepted'&&state.landed&&state.continued&&state.caught===0&&state.heldWeight===reference.heldWeight;
 if(shape==='filed')return state.normalized==='accepted'&&!state.landed&&state.caught===1&&state.best===reference.best&&state.finish;
 return state.normalized==='accepted'&&state.atPlace;
}
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');

async function run(){
 const {chromium}=require('playwright-core');
 const [input,repeatString='4']=process.argv.slice(2);
 assert(input,'Provide the exact packaged HTML path');
 const file=path.resolve(input), repeats=Number(repeatString),expectedSha=process.env.EXACT_HTML_SHA256;
 assert(Number.isInteger(repeats)&&repeats>=1&&repeats<=100);
 assert.match(expectedSha||'',/^[a-f0-9]{64}$/);
 assert(process.env.BROWSER_PATH,'Set BROWSER_PATH to the CI-pinned executable');
 const bytes=await fs.readFile(file);assert.equal(hash(bytes),expectedSha,'HTML does not match expected provenance');
 const endpoint='/'+encodeURIComponent(path.basename(file));
 const server=http.createServer((req,res)=>{
  if(req.method==='GET'&&req.url===endpoint){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':bytes.length});res.end(bytes);}
  else res.writeHead(404).end();
 });
 let browser;
 try{
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const loopback='http://127.0.0.1:'+server.address().port+endpoint;
  const fetched=await fetch(loopback);assert(fetched.ok);assert.equal(hash(Buffer.from(await fetched.arrayBuffer())),expectedSha);
  browser=await chromium.launch({executablePath:process.env.BROWSER_PATH,headless:true});
  if(process.env.EXPECT_BROWSER_VERSION)assert.equal(browser.version(),process.env.EXPECT_BROWSER_VERSION,'Different browser from CI');
  const urls={file:pathToFileURL(file).href,http:loopback},counts={};
  console.log(JSON.stringify({sourceSha256:expectedSha,browser:browser.version(),repeats}));
  for(let i=0;i<repeats;i++)for(const shape of ['pending','destination','filed'])for(const mobile of [false,true])for(const transport of (i%2?['http','file']:['file','http'])){
   const ctx=await browser.newContext(mobile?{viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'}:{viewport:{width:850,height:900}});
   try{
    const page=await ctx.newPage();let pageErrors=0;page.on('pageerror',()=>pageErrors++);
    const waitReady=()=>page.waitForFunction(()=>typeof g!=='undefined'&&g&&document.querySelector('#act')?.disabled===false,undefined,{timeout:12000});
    await page.goto(urls[transport]);await waitReady();
    const expected=await page.evaluate(()=>({place:originalAtlas.locations.find(x=>x.name==='Kwan Phayao').id,species:40,cm:18}));
    // Register *after* initial boot. On the next document this read runs before app code and never writes.
    await page.addInitScript({content:
     'Object.defineProperty(window,"__pocketReel62Start",{value:Object.freeze(('+snapshotStorage.toString()+')('+JSON.stringify(expected)+'))})'});

    const fresh=await page.evaluate(snapshotStorage,expected);
    assert.equal(fresh.canary,'missing','Unexpected retained canary in fresh test context');
    assert.equal(fresh.key,'missing','Unexpected retained career in fresh test context');
    // The canary is written BEFORE the app's fixture writes, not as a flush/delay after them.
    await page.evaluate(k=>localStorage.setItem(k,'synthetic'),canaryKey);
    await page.evaluate(({place,species,cm,shape})=>{
     if(shape==='destination'){
      chooseSpot(place,1);stopArrival();
     }else{
      g.restoreCatch(species,cm);pendingDay=0;pendingCapture=captureLanding();save();
     }
    },{...expected,shape});
    if(shape==='filed'){
     await page.locator('#catchContinue').click();
     await page.waitForFunction(()=>g.state()===0);
     await page.evaluate(()=>{$('finish').selectedIndex=1;$('finish').dispatchEvent(new Event('change'));});
    }
    if(shape==='pending')await page.waitForFunction(()=>g.state()===5&&!$('catchContinue').hidden);
    const before=await observe(page,expected,shape);
    assert(expectedStored(shape,before.storage)&&before.storage.canary==='present'&&verified(before,before.state),'Synthetic precondition did not reach persisted state');
    const response=await page.reload();
    if(transport==='http')assert(response?.ok());
    assert.equal(page.url(),urls[transport],'Reload navigated to a different URL');
    const start=await page.evaluate(()=>window.__pocketReel62Start??null);
    const navigation=await page.evaluate(()=>performance.getEntriesByType('navigation')[0]?.type??null);
    assert.equal(navigation,'reload');
    const alive=await waitReady().then(()=>true,()=>false);
    let after=null;
    if(alive){
     if(shape==='pending'&&start?.pending)await page.waitForFunction(()=>g.state()===5&&!$('catchContinue').hidden,undefined,{timeout:3000}).catch(()=>{});
     after=await observe(page,expected,shape);
     after.verified=verified(after,before.state);
    }
    const category=diagnose({shape,start,ready:after});
    const summarize=ob=>ob&&({storage:ob.storage,normalized:ob.state.normalized,atPlace:ob.state.atPlace,landed:ob.state.landed,continued:ob.state.continued,
     caughtNone:ob.state.caught===0,caughtOnce:ob.state.caught===1,bestSame:ob.state.best===before.state.best,weightSame:ob.state.heldWeight===before.state.heldWeight,finish:ob.state.finish,warning:ob.state.warning});
    counts[category]=(counts[category]||0)+1;
    console.log(JSON.stringify({i,mobile,transport,shape,category,navigation,pageErrors,before:summarize(before),documentStart:start,after:summarize(after)}));
   }finally{await ctx.close();}
  }
  console.log(JSON.stringify({counts}));
  if(Object.keys(counts).some(k=>k!=='pass'))process.exitCode=1;
 }finally{
  if(browser)await browser.close();
  if(server.listening)await new Promise(resolve=>server.close(resolve));
 }
}
module.exports={snapshotStorage,diagnose,expectedStored};
if(require.main===module)run().catch(error=>{console.error('Synthetic reload comparison aborted:',error.name,error.message);process.exitCode=1;});
