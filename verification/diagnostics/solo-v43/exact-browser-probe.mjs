import {createRequire} from 'node:module';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {prepare,processFor,H,BASE,SHA} from './exact-pack.mjs';
class ProbeError extends Error {}
const check=(ok,phase)=>{if(!ok)throw new ProbeError(phase);};
const require=createRequire(import.meta.url);
let phase='initial-prerequisites';
const main=async()=>{
 check(process.env.POCKET_REEL_DISPOSABLE_RUNNER==='1','runner-not-authorized');
 check(require('playwright-core/package.json').version==='1.62.1','playwright-pin');
 const {chromium}=require('playwright-core');
 check(process.versions.node==='22.16.0','node-pin');
 check(/\b151\.0\.7922\.34\b/.test(execFileSync(chromium.executablePath(),['--version'],{encoding:'utf8'})),'chromium-pin');
 phase='disposable-profile-directory';
 const tmp=await mkdtemp(join(tmpdir(),'reel-v43-solo-browser-'));
 let server,ctx;
 const finishBrowser=async()=>{if(ctx){const pending=ctx;ctx=null;await pending.close();}};
 const finishServer=async()=>{if(server){const pending=server;server=null;await pending.stop();}};
 const errors=[],outside=[];
 const open=async(profile,observe=false)=>{
  const entry=profile==='persistent-source'?'source':'destination';
  phase=entry+'-chromium-launch';
  ctx=await chromium.launchPersistentContext(join(tmp,profile),{headless:true,acceptDownloads:true,reducedMotion:'reduce',
   isMobile:true,hasTouch:true,viewport:{width:844,height:390},serviceWorkers:'block'});
  await ctx.route('**/*',r=>{const url=r.request().url();if(url===BASE||url.startsWith('data:')||url.startsWith('blob:'))return r.continue();outside.push(new URL(url).protocol);return r.abort();});
  const p=ctx.pages()[0]??await ctx.newPage();
  p.setDefaultTimeout(15000);p.on('pageerror',e=>errors.push(e.name));
  if(observe)await p.addInitScript(()=>{try{window.__initialRouteCareer=localStorage.getItem('thai-atlas-v2');}catch{window.__initialRouteCareer=undefined;}});
  phase=entry+'-canonical-page';
  check(H(await (await p.goto(BASE)).body())===SHA,'browser-received-noncanonical-bytes');
  phase=entry+'-boot-home';
  await p.locator('#bootResume').waitFor({state:'visible'});return p;
 };
 const snap=p=>p.evaluate(()=>({raw:localStorage.getItem('thai-atlas-v2'),catchCount:g.caught(1433),epoch:performance.timeOrigin,initial:window.__initialRouteCareer}));
 const career=async(p,restore=false)=>{
  phase=restore?'destination-career-menu':'source-career-menu';
  await p.locator('#openMenu').tap();
  await p.locator('[data-section=home] [data-to=career]').tap();
  await p.locator('#careerExport').waitFor({state:'visible'});
  if(restore){
   // V43 places restore in Career sheet 2/2. Exercise its real touch arrow.
   phase='destination-restore-sheet';
   await p.locator('#sheetNext').tap();
   check(await p.locator('#sheetNumber').textContent()==='2/2','restore-sheet-not-active');
   await p.locator('#careerFile').waitFor({state:'visible'});
  }
 };
 try{
  phase='launcher-first-start';
  const {script}=await prepare(tmp);server=processFor(script);await server.ready;const pid=server.pid;
  let p=await open('persistent-source',true); const fresh=await snap(p);check(fresh.raw===null&&fresh.initial===null,'fresh-source-not-empty');
  phase='source-resume';
  await p.locator('#bootResume').tap();await p.waitForFunction(()=>g?.state()===0&&!$('act').disabled);
  // Canonical #90 deterministic engine-facing cast/fight, no save/restore seeding.
  phase='engine-cast-and-land';
  const witness=await p.evaluate(()=>{
   chooseSpot(98,1,1);stopArrival();g.initialize(25);g.place(98,1);g.conditions(1,11,20779);g.setTechnique(0);if(!g.setBait(17))throw Error('bait');
   g.setAim(.5,.67);g.advance(16,1,0,0);const e=[g.state(),g.species(),g.lengthCm()];g.advance(900,0,0,0);
   for(let i=0;i<1000&&g.state()===2;i++)g.advance(16,0,0,0);
   if(g.state()!==3)throw Error('missing bite');g.advance(16,0,1,0);
   for(let i=0;i<472;i++){if(g.state()!==4)throw Error('early landing');const bottom=!!g.holdingBottom();g.advance(16,0,bottom?1:0,g.fightBeat()===1||bottom?0:.014);}
   const raf=window.requestAnimationFrame;try{window.requestAnimationFrame=()=>0;turns=.014;frame(prev+16);}finally{window.requestAnimationFrame=raf;}
   return {e,landed:g.state(),uid:pendingCapture?.uid};
  });
  check(witness.e.join(',')==='1,1433,27'&&witness.landed===5&&/^[a-f0-9]{32}$/i.test(witness.uid),'unverified-engine-landing');
  phase='trusted-continue';
  await p.evaluate(()=>$('catchContinue').addEventListener('click',e=>{window.__trustedContinue=e.isTrusted;},{once:true}));
  await p.locator('#catchContinue').tap();await p.waitForFunction(()=>g.state()===0);
  check(await p.evaluate(()=>window.__trustedContinue===true),'untrusted-continue');
  phase='filing-readback';
  const saved=await snap(p), data=JSON.parse(saved.raw), cap=data.history?.[0];
  check(saved.catchCount===1&&data.history?.length===1&&cap?.uid===witness.uid&&cap.id===1433&&cap.cm===27&&cap.place===98&&cap.bait===17&&Number.isSafeInteger(cap.grams)&&data.pending===null,'career-write-not-exactly-once');
  await career(p);
  phase='source-export-download';
  const [file]=await Promise.all([p.waitForEvent('download'),p.locator('#careerExport').tap()]);
  check(/^Pocket-Reel-career-\d{4}-\d{2}-\d{2}\.json$/.test(file.suggestedFilename()),'backup-is-not-full-career');
  phase='source-export-readback';
  const bak=await readFile(await file.path());const payload=JSON.parse(bak.toString());
  check(payload.format==='Pocket Reel career'&&payload.version===1&&JSON.stringify(payload.career)===saved.raw,'backup-not-exact-career');
  phase='both-processes-restart';
  await finishBrowser();await finishServer();server=processFor(script);await server.ready;check(server.pid!==pid,'same-launcher-process');
  p=await open('persistent-source',true);
  phase='source-restart-readback';
  const restored=await snap(p);check(restored.epoch!==saved.epoch&&restored.initial===saved.raw&&restored.raw===saved.raw&&restored.catchCount===1,'same-profile-restart-lost-or-rewrote-career');
  await finishBrowser();
  p=await open('isolated-destination',true);check((await snap(p)).raw===null,'profile-not-isolated');
  phase='destination-resume';
  await p.locator('#bootResume').tap();await p.waitForFunction(()=>g?.state()===0&&!$('act').disabled);await career(p,true);
  phase='destination-readback';
  const before=(await snap(p)).raw;
  const input=p.locator('#careerFile');
  phase='invalid-backup-input';
  await input.setInputFiles({name:'broken.json',mimeType:'application/json',buffer:Buffer.from('invalid')});
  await p.waitForFunction(()=>!!$('careerStatus').textContent&&$('careerRestore').hidden);
  check((await snap(p)).raw===before,'invalid-backup-wrote-career');
  const upload=()=>input.setInputFiles({name:'fixture.json',mimeType:'application/json',buffer:bak});
  phase='valid-backup-preview';
  await upload();await p.locator('#careerRestore').waitFor({state:'visible'});
  check((await snap(p)).raw===before,'preview-wrote-career');
  phase='cancel-preview-reload';
  await p.reload();await p.locator('#bootResume').waitFor({state:'visible'});
  check((await snap(p)).raw===before,'cancel-by-reload-wrote-career');
  phase='destination-resume';
  await p.locator('#bootResume').tap();await p.waitForFunction(()=>g?.state()===0&&!$('act').disabled);await career(p,true);
  phase='destination-reselect-backup';
  await upload();
  const preReplaceEpoch=(await snap(p)).epoch;
  phase='explicit-backup-replace';
  await Promise.all([p.waitForNavigation(),p.locator('#careerRestore').tap()]);
  await p.waitForFunction(epoch=>performance.timeOrigin!==epoch,preReplaceEpoch);
  await p.locator('#bootResume').waitFor({state:'visible'});
  phase='destination-import-readback';
  const imported=await snap(p);check(imported.raw===saved.raw&&imported.catchCount===1,'explicit-manual-import-did-not-restore');
  phase='destination-final-restart';
  const importedNewEpoch=imported.epoch;
  await finishBrowser();
  p=await open('isolated-destination',true);
  phase='destination-final-readback';
  const reread=await snap(p);
  check(reread.epoch!==importedNewEpoch&&reread.initial===saved.raw&&reread.raw===saved.raw&&reread.catchCount===1,'manual-import-did-not-persist-after-restart');
  check(errors.length===0&&outside.length===0,'page-error-or-external-request');
  console.log('PASS V43 exact fixed-origin browser restart, engine-generated catch, real backup download/picker, cancel and import.');
 }finally{try{await finishBrowser();}finally{try{await finishServer();}finally{await rm(tmp,{recursive:true,force:true});}}}
};
main().catch(e=>{
 console.error('FAIL Solo browser probe: '+(e instanceof ProbeError?e.message:phase+' (operation failed)'));
 process.exitCode=1;
});
