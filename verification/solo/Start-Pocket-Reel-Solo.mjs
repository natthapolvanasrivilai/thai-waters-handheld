import {createHash} from 'node:crypto';
import {lstat,readFile} from 'node:fs/promises';
import {createServer} from 'node:http';
import {pathToFileURL} from 'node:url';

export const HOST='127.0.0.1';
export const PORT=17841; // preserve across upgrades
export const ORIGIN=`http://${HOST}:${PORT}`;
const authority=`${HOST}:${PORT}`;

const html=new URL('./Thai-Waters-play.html',import.meta.url);
const manifest=new URL('./Pocket-Reel-HTML.sha256',import.meta.url);
async function checkedSibling(file,description,maxBytes){
 let stat;
 try{stat=await lstat(file);}
 catch{throw Error('Missing '+description+' beside the launcher. Keep the solo package together.');}
 if(!stat.isFile()||stat.size<1||stat.size>maxBytes)throw Error('Invalid '+description+' beside the launcher.');
 try{
  const data=await readFile(file);if(data.length<1||data.length>maxBytes)throw Error();
  return data;
 }catch{throw Error('Could not read '+description+' beside the launcher.');}
}
export async function start(){
 if(Number(process.versions.node.split('.')[0])<22)throw Error('Pocket Reel Solo requires Node.js 22 or later.');
 const bytes=await checkedSibling(html,'packed HTML',64*1024*1024);
 const signature=await checkedSibling(manifest,'HTML checksum manifest',100);
 const text=signature.toString('utf8');
 const match=/^([a-f0-9]{64})  Thai-Waters-play\.html\r?\n$/.exec(text);
 if(!match||match[0]!==text)throw Error('Invalid HTML checksum manifest format.');
 if(createHash('sha256').update(bytes).digest('hex')!==match[1])throw Error('Packed HTML checksum mismatch.');
 const server=createServer((req,res)=>{
  res.setHeader('Cache-Control','no-store');
  res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('X-Content-Type-Options','nosniff');
  const reject=(code,message)=>{res.writeHead(code,{'Content-Type':'text/plain; charset=utf-8'});res.end(req.method==='HEAD'?undefined:message);};
  if(req.headers.host!==authority||req.socket.localAddress!==HOST||req.socket.remoteAddress!==HOST)return reject(421,'Loopback authority required.');
  if(req.headers.upgrade)return reject(400,'Protocol upgrade is not available.');
  if(req.method!=='GET'&&req.method!=='HEAD'){res.setHeader('Allow','GET, HEAD');return reject(405,'Method not available.');}
  if(req.url!=='/')return reject(404,'Not available.');
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':bytes.length});
  res.end(req.method==='HEAD'?undefined:bytes);
 });
 // Decline Upgrade and CONNECT before any protocol hand-off or content.
 const refuseSocket=(_request,socket)=>socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n');
 server.on('upgrade',refuseSocket);
 server.on('connect',refuseSocket);
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
 try{
  if(process.argv.length!==2)throw Error('Usage: node Start-Pocket-Reel-Solo.mjs (no arguments)');
  const h=await start();
  console.log(`Offline Pocket Reel: ${h.origin}/ (close this process to stop)`);
 }catch(e){console.error(e.message);process.exitCode=1;}
}
