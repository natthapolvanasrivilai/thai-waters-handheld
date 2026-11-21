// Future test only: never point at an existing profile or unverified product bytes.
import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {execFileSync,spawn} from 'node:child_process';
import {createServer,request} from 'node:http';
import {createRequire} from 'node:module';
import {ORIGIN,HOST} from './launcher.mjs';

const artifactHash='2f9b1663f1ba573869ee6ef84907825b0ca63c8d43efaf9e7a3888b8aba3e425';
assert.equal(process.argv.length,3,'Supply only the extracted exact HTML path');
const fixture=pathToFileURL(resolve(process.argv[2]));
const storageKey='thai-atlas-v2';
const packageVersion='1.62.1',version='151.0.7922.34';
const require=createRequire(import.meta.url);
async function main(){
 assert.equal(process.env.POCKET_REEL_AUTHORIZED_TEST_RUNNER,'1','Use the separately authorized disposable runner only');
 assert.equal(process.versions.node,'22.16.0');
 assert.equal(require('playwright-core/package.json').version,packageVersion);
 const {chromium}=require('playwright-core');
 const chromiumPath=chromium.executablePath();
 assert.match(execFileSync(chromiumPath,['--version'],{encoding:'utf8'}),new RegExp('(^|\\s)'+version.replaceAll('.','\\.')+'($|\\s)'));
 const temp=await mkdtemp(join(tmpdir(),'pocket-reel-loopback-profile-'));
 const stable=join(temp,'profile-kept-between-process-restarts');
 const separate=join(temp,'profile-isolated');
 const blocked=[];
 let loop,current,alternate;
 const app=async()=>{
  const launcher=fileURLToPath(new URL('./launcher.mjs',import.meta.url));
  const child=spawn(process.execPath,[launcher,fileURLToPath(fixture),artifactHash],{stdio:['ignore','pipe','pipe']});
  const closed=new Promise(ok=>child.once('exit',(code,signal)=>ok({code,signal})));
  try{
   await new Promise((ok,no)=>{
    const timeout=setTimeout(()=>no(Error('Verified launcher did not become ready')),10000);
    let stdout='';
    child.once('error',()=>{clearTimeout(timeout);no(Error('Could not launch verified helper'));});
    child.once('exit',()=>{clearTimeout(timeout);no(Error('Launcher exited before fixed origin was ready'));});
    child.stdout.on('data',b=>{
     stdout+=b;
     if(stdout.includes('Offline Pocket Reel: '+ORIGIN+'/')){clearTimeout(timeout);ok();}
    });
    child.stderr.resume();
   });
  }catch(e){child.kill('SIGTERM');throw e;}
  return {origin:ORIGIN,close:async()=>{if(child.exitCode===null)child.kill('SIGTERM');await closed;}};
 };
 const closeContext=async()=>{if(current){const x=current;current=null;await x.close();}};
 const disposeApp=async()=>{if(loop){const x=loop;loop=null;await x.close();}};
 const disposeAlt=async()=>{if(alternate){const x=alternate;alternate=null;await new Promise((ok,no)=>x.close(e=>e?no(e):ok()));}};
 const open=async(profile,allowed)=>{
  assert(profile===stable||profile===separate);
  current=await chromium.launchPersistentContext(profile,{executablePath:chromiumPath,headless:true,serviceWorkers:'block'});
  await current.route('**/*',route=>{
   const u=new URL(route.request().url());
   if(u.origin===allowed&&u.pathname==='/'&&!u.search)return route.continue();
   blocked.push(u.protocol);
   return route.abort();
  });
  return current.pages()[0]??await current.newPage();
 };
 const read=async p=>p.evaluate(async k=>{
  const raw=localStorage.getItem(k);
  if(raw===null)return {present:false};
  const valid=careerVault().load();
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw)))).join(',');
  return {present:true,finish:valid.finish,count:valid.book[0][0],hash};
 },storageKey);
 try{
  loop=await app();
  assert.equal(loop.origin,ORIGIN);
  let p=await open(stable,ORIGIN);
  await p.goto(ORIGIN+'/');await p.waitForFunction(()=>!!g&&!document.querySelector('#act').disabled);
  assert.deepEqual(await read(p),{present:false});
  const beforeEpoch=await p.evaluate(()=>performance.timeOrigin);
  await p.evaluate(()=>{
   // Only the fixture initializes an entry. The normal in-game Rod Finish change handler saves the career.
   g.restoreEntry(0,1,atlas.fish[0].low);
   const select=document.querySelector('#finish');
   select.selectedIndex=2;select.dispatchEvent(new Event('change',{bubbles:true}));
  });
  const expected=await read(p);
  assert.equal(expected.finish,2);assert.equal(expected.count,1);
  await closeContext();await disposeApp();
  // launchPersistentContext again opens a new Chromium process with the same disposable profile.
  loop=await app();assert.equal(loop.origin,ORIGIN);
  p=await open(stable,ORIGIN);await p.goto(ORIGIN+'/');
  await p.waitForFunction(()=>!!g&&!document.querySelector('#act').disabled);
  assert.notEqual(await p.evaluate(()=>performance.timeOrigin),beforeEpoch);
  const saved=await read(p);
  assert.equal(saved.present&&saved.finish===expected.finish&&saved.count===expected.count&&saved.hash===expected.hash,true,'Exact synthetic game bytes and decoded values survive the restart');
  assert.deepEqual(await p.evaluate(()=>[g.caught(0),document.querySelector('#finish').selectedIndex]),[1,2]);
  await closeContext();

  // Different profile on the exact same origin must not see that fixture.
  p=await open(separate,ORIGIN);await p.goto(ORIGIN+'/');
  await p.waitForFunction(()=>!!g&&!document.querySelector('#act').disabled);
  assert.deepEqual(await read(p),{present:false});await closeContext();

  // Alternate port serves inert HTML only to prove separation with the same test profile.
  alternate=createServer((q,s)=>{
   if(q.method!=='GET'||q.url!=='/'||q.socket.remoteAddress!==HOST){s.writeHead(404);s.end();return;}
   s.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});s.end('<title>Inert origin fixture</title>');
  });
  await new Promise((ok,no)=>{alternate.once('error',no);alternate.listen({host:HOST,port:0,exclusive:true},ok);});
  const other='http://'+HOST+':'+alternate.address().port;
  assert.notEqual(other,ORIGIN);assert.equal(alternate.address().address,HOST);
  p=await open(stable,other);await p.goto(other+'/');
  assert.equal(await p.evaluate(k=>localStorage.getItem(k)===null,storageKey),true);
  await closeContext();await disposeAlt();
  // Host alias isolation is not inferred from a rejected frontend route. Verify actual rejection only.
  const denied=await new Promise((ok,no)=>{
   const q=request(ORIGIN+'/',{headers:{Host:'localhost:'+new URL(ORIGIN).port}},r=>{r.resume();ok(r.statusCode);});
   q.on('error',no);q.end();
  });
  assert.equal(denied,421);
  assert.deepEqual(blocked,[]);
  console.log('PASS fixed origin and test profile retain an in-game career across separate browser and launcher starts; other port/profile isolated, alias denied.');
 }finally{
  await closeContext();await disposeAlt();await disposeApp();await rm(temp,{recursive:true,force:true});
 }
}

main().catch(()=>{console.error('FAIL fixed-origin synthetic browser probe; no browser/profile data logged.');process.exitCode=1;});
