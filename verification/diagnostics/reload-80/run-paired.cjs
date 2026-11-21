'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const crypto=require('node:crypto'),{spawn,execFileSync}=require('node:child_process');
const {createInterface}=require('node:readline');
const src='01db3b50b4b73dd7e0eee9cc566efe7a105ddc6e';
const html='1874a1cdc822eff6f2012e27355f56808a66411f101d0dd8beca42e723b6f02e';
const wasm='a6323da4983b12797f080bebe8c5eec5c7bc4a855327f7c995cb66ad78e5f270';
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const root=path.join(__dirname,'artifact'),filename=path.join(root,'Thai-Waters-play.html');
function exactBundle(){
 const bytes=fs.readFileSync(filename);
 assert.equal(hash(bytes),html);assert.equal(hash(fs.readFileSync(path.join(root,'atlas.wasm'))),wasm);
 assert.equal(fs.readFileSync(path.join(root,'BUILD.txt'),'utf8').split('\n')[0],'SOURCE_COMMIT='+src);
 return bytes;
}
const endpoint='/Thai-Waters-play.html';
async function serveExact(bytes){
 const server=http.createServer((req,res)=>{
  if(req.method!=='GET'||req.url!==endpoint){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':bytes.length,'Cache-Control':'no-store'});
  res.end(bytes);
 });
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',()=>{server.removeListener('error',reject);resolve();});});
 const url='http://127.0.0.1:'+server.address().port+endpoint;
 return {url,close:()=>new Promise((r,j)=>{server.close(e=>e?j(e):r());server.closeAllConnections();})};
}
async function one(scheme,url){
 const env={...process.env};delete env.TW80_LOOPBACK_URL;
 if(scheme==='loopback')env.TW80_LOOPBACK_URL=url;
 const script=path.join(__dirname,'work/verification/browser-tests/gameplay.cjs');
 const child=spawn(process.execPath,[script,filename],{env,cwd:path.dirname(script),stdio:['ignore','pipe','pipe']});
 const stages=[];let blocker=null;
 const filters=['paired reload ','paired observer failure ','reload trace '];
 for(const input of [child.stdout,child.stderr])createInterface({input}).on('line',line=>{
  if(line.includes('socket() failed: Operation not permitted'))blocker='chromium-process-singleton-socket-denied';
  if(line.includes("Cannot find module 'playwright-core'"))blocker='playwright-core-not-on-Node-path';
  const prefix=filters.find(x=>line.startsWith(x));if(!prefix)return;
  try{
   const row=JSON.parse(line.slice(prefix.length));if(prefix==='paired reload ')stages.push(row.stage);
   console.log(prefix+JSON.stringify({scheme,...row}));
  }catch{}
 });
 const state=await new Promise((r,j)=>{child.once('error',j);child.once('close',(code,signal)=>r({code,signal}));});
 console.log('cohort result '+JSON.stringify({scheme,stages,blocker,...state}));
 return {scheme,stages,blocker,...state};
}
async function main(){
 assert(process.argv.length===2,'Run one pair only');
 const bytes=exactBundle();
 const browser=process.env.BROWSER_PATH;
 assert(browser,'Set BROWSER_PATH to the executable');
 const installed=execFileSync(browser,['--version'],{encoding:'utf8'}).match(/\b\d+\.\d+\.\d+\.\d+\b/)?.[0];
 const required=process.env.EXPECT_BROWSER_VERSION||'151.0.7922.34';
 assert.equal(installed,required,'Browser version pin did not match');
 const service=await serveExact(bytes);
 try{
  const first=await fetch(service.url);assert.equal(first.status,200);
  assert.equal(hash(Buffer.from(await first.arrayBuffer())),html);
  console.log('verified bundle '+JSON.stringify({source:src,html,wasm,browser:installed,ciBrowser:installed==='151.0.7922.34'}));
  const a=await one('file'),b=await one('loopback',service.url);
  // An instrumented pass requires both hard gates, both stage receipts, and full canonical script exit 0.
  if([a,b].some(x=>x.code!==0||x.stages.join(',')!=='gameplay-pending,gameplay-filed'))process.exitCode=1;
 }finally{await service.close();}
}
if(require.main===module)main().catch(e=>{console.error('Pair setup failed: '+e.name+(e.code?' '+e.code:''));process.exitCode=1;});
module.exports={exactBundle,serveExact};
