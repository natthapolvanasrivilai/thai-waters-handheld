'use strict';
const http=require('node:http'),fs=require('node:fs/promises'),crypto=require('node:crypto');
const HOST='127.0.0.1',PORT=43180,ENTRY='/Thai-Waters-play.html';
const URL='http://127.0.0.1:43180/Thai-Waters-play.html';

// Only the explicit persistence specs use this single immutable artifact.
// Opening the game from a downloaded file is independently hard-gated.
async function openPersistenceEntry(file,externalUrl){
 if(externalUrl)return {url:externalUrl,close:async()=>{}};
 const bytes=await fs.readFile(file);
 const hash=crypto.createHash('sha256').update(bytes).digest('hex');
 let observed=false;
 const server=http.createServer((req,res)=>{
  if(req.headers.host!==HOST+':'+PORT||req.url!==ENTRY||req.method!=='GET'){
   res.writeHead(404);res.end();return;
  }
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':bytes.length,'Cache-Control':'no-store'});
  res.end(bytes);
  if(!observed){observed=true;console.log('TW_LANE loopback '+hash);}
 });
 await new Promise((resolve,reject)=>{
  server.once('error',reject);
  server.listen(PORT,HOST,()=>{server.removeListener('error',reject);resolve();});
 });
 return {url:URL,close:()=>new Promise((resolve,reject)=>{
  server.close(e=>e?reject(e):resolve());
  server.closeAllConnections();
 })};
}
module.exports={openPersistenceEntry};
