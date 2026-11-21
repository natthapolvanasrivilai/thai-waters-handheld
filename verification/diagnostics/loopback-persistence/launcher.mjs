import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {createServer} from 'node:http';
import {pathToFileURL} from 'node:url';

export const HOST='127.0.0.1';
export const PORT=17841; // local prototype allocation; do not change across upgrades
export const ORIGIN=`http://${HOST}:${PORT}`;
const authority=`${HOST}:${PORT}`;

export async function start({artifact,expectedSha}){
 if(typeof expectedSha!=='string'||!(/^[a-f0-9]{64}$/).test(expectedSha))throw Error('Supply the verified packed HTML SHA-256');
 let bytes;
 try{bytes=await readFile(artifact);}catch{throw Error('Could not read the packed HTML');}
 if(createHash('sha256').update(bytes).digest('hex')!==expectedSha)throw Error('Packed HTML checksum mismatch');
 const server=createServer((req,res)=>{
  res.setHeader('Cache-Control','no-store');
  res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('X-Content-Type-Options','nosniff');
  const reject=(code,message)=>{res.writeHead(code,{'Content-Type':'text/plain; charset=utf-8'});res.end(req.method==='HEAD'?undefined:message);};
  if(req.headers.host!==authority||req.socket.localAddress!==HOST||req.socket.remoteAddress!==HOST)return reject(421,'Loopback authority required.');
  if(req.method!=='GET'&&req.method!=='HEAD'){res.setHeader('Allow','GET, HEAD');return reject(405,'Method not available.');}
  if(req.url!=='/')return reject(404,'Not available.');
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':bytes.length});
  res.end(req.method==='HEAD'?undefined:bytes);
 });
 await new Promise((resolve,reject)=>{
  const failure=e=>reject(Object.assign(new Error(e.code==='EADDRINUSE'?
   `Pocket Reel's fixed port ${PORT} is already in use. Close the other listener, then restart; no alternate port was selected.`:
   'Could not start the loopback listener.'),{code:e.code}));
  server.once('error',failure);
  server.listen({host:HOST,port:PORT,exclusive:true},()=>{
   server.removeListener('error',failure);resolve();
  });
 });
 return {origin:ORIGIN,address:server.address(),close:()=>new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()))};
}
if(process.argv[1]&&pathToFileURL(process.argv[1]).href===import.meta.url){
 const [artifact,expectedSha]=process.argv.slice(2);
 try{
  if(!artifact)throw Error('Usage: node launcher.mjs <verified packed HTML> <published SHA-256>');
  const h=await start({artifact,expectedSha});
  console.log(`Offline Pocket Reel: ${h.origin}/ (close this process to stop)`);
 }catch(e){console.error(e.message);process.exitCode=1;}
}
