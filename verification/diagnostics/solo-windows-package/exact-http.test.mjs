import {test} from 'node:test';
import assert from 'node:assert/strict';
import {request} from 'node:http';
import {mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {prepare,processFor,H,BASE,SHA} from './exact-pack.mjs';
const ask=(path='/',method='GET',host='127.0.0.1:17841',headers={})=>new Promise((ok,no)=>{
 const q=request(BASE,{path,method,headers:{Host:host,...headers}},r=>{
  const b=[];r.on('data',v=>b.push(v));r.on('end',()=>ok({status:r.statusCode,h:r.headers,b:Buffer.concat(b)}));
 });q.on('upgrade',(r,s)=>{s.destroy();no(Error('protocol upgrade was granted'));});q.on('connect',(r,s,b)=>{s.destroy();ok({status:r.statusCode,h:r.headers,b});});q.on('error',no);q.end();
});
test('exact f08 HOLD package pins same HTTP bytes on two actual launcher processes',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'Pocket Reel ทดสอบ HTTP '));
 try{
  const {script,manifest,bytes}=await prepare(dir);
  let prevPid;
  for(let i=0;i<2;i++){
   const p=processFor(script);
   try{
    await p.ready;assert.notEqual(p.pid,prevPid);prevPid=p.pid;
    const g=await ask();assert.equal(g.status,200);assert.equal(H(g.b),SHA);assert(g.b.equals(bytes));assert.equal(g.h['cache-control'],'no-store');
    const h=await ask('/','HEAD');assert.equal(h.status,200);assert.equal(h.b.length,0);
    assert.equal(h.h['content-length'],String(bytes.length));
    for(const [path,method,host,status] of [['/?save=1','GET',undefined,404],['/../backup.json','GET',undefined,404],['/','POST',undefined,405],['/','GET','localhost:17841',421]]){
     const r=await ask(path,method,host);assert.equal(r.status,status);assert.equal(r.h['set-cookie'],undefined);assert.equal(r.h['access-control-allow-origin'],undefined);
    }
    const upgrade=await ask('/','GET',undefined,{Connection:'Upgrade',Upgrade:'websocket','Sec-WebSocket-Version':'13','Sec-WebSocket-Key':'dGhlIHNhbXBsZSBub25jZQ=='});
    assert.equal(upgrade.status,400);assert.equal(upgrade.h.upgrade,undefined);assert.equal(upgrade.b.length,0);
    const tunnel=await ask('127.0.0.1:17841','CONNECT');assert.equal(tunnel.status,400);assert.equal(tunnel.b.length,0);
    const contender=processFor(script);try{const d=await contender.done;assert.equal(d.code,1);assert.match(d.err,/fixed port 17841/);assert.doesNotMatch(d.out,/Offline Pocket Reel/);}finally{await contender.stop();}
   }finally{await p.stop();}
   await assert.rejects(ask(),{code:'ECONNREFUSED'});
  }
  await writeFile(manifest,'0'.repeat(64)+'  Thai-Waters-play.html\n');
  const invalid=processFor(script);try{const d=await invalid.done;assert.equal(d.code,1);assert.match(d.err,/checksum mismatch/);await assert.rejects(ask(),{code:'ECONNREFUSED'});}finally{await invalid.stop();}
 }finally{await rm(dir,{recursive:true,force:true});}
});
