import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {randomInt} from 'node:crypto';
import dgram from 'node:dgram';
import assert from 'node:assert/strict';
const port=randomInt(20000,30000),udpPort=port+1,base='http://127.0.0.1:'+port;
const child=spawn(process.execPath,[new URL('server.mjs',import.meta.url).pathname.replace(/^\/([A-Z]:)/,'$1')],{env:{...process.env,TW_BIND:'127.0.0.1',TW_HOST:'127.0.0.1',TW_PORT:String(port),TW_UDP_PORT:String(udpPort),TW_CERT:'',TW_KEY:'',TW_QR:''}});
const udp=dgram.createSocket('udp4');
try{
 await Promise.race([once(child.stdout,'data'),once(child,'exit').then(()=>{throw Error('Host failed');})]);
 const html=await (await fetch(base+'/pair')).text();const join=html.match(/href="(http[^"]+)"/)[1];
 const login=async()=>(await fetch(join,{redirect:'manual'})).headers.get('set-cookie').split(';')[0];
 const a=await login(),b=await login();
 async function poll(cookie,spot,round=0,score=0){
  return (await fetch(base+'/event',{method:'POST',headers:{cookie,'Content-Type':'application/json'},body:JSON.stringify({spot,round,score})})).json();
 }
 const one=await poll(a,104),two=await poll(b,104);
 assert.equal(one.round,two.round);assert.equal(two.players,2);
 const hardware=async(round,score)=>{
  const received=once(udp,'message');udp.send('TW1 77311 104 '+round+' '+score,udpPort,'127.0.0.1');
  const [buf]=await Promise.race([received,new Promise((_,reject)=>setTimeout(()=>reject(Error('UDP timeout')),1500))]);return buf.toString().split(' ').map((x,i)=>i?Number(x):x);
 };
 let reply=await hardware(0,0);assert.equal(reply[3],one.round);assert.equal(reply[5],3);
 await poll(a,104,one.round,3);await poll(b,104,one.round,2);await hardware(one.round,3);
 assert.equal((await poll(a,104,one.round,3)).total,8);assert.equal((await hardware(one.round,1))[6],8);
 assert.equal((await poll(b,3)).total,0);assert.equal((await fetch(base+'/')).status,403);
 console.log('PASS two browser sessions and one handheld-protocol UDP client shared a location, reached 8 catches, deduplicated reordered reports and isolated a second room.');
}finally{udp.close();child.kill();}

