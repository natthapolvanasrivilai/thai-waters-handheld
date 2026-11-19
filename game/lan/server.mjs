import http from 'node:http';
import https from 'node:https';
import dgram from 'node:dgram';
import fs from 'node:fs';
import os from 'node:os';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import qr from 'qrcode';
import {DatabaseSync} from 'node:sqlite';
import {tournament} from '../sites/cup.mjs';
const game=fileURLToPath(new URL('../Thai-Waters-play.html',import.meta.url));
const spots=JSON.parse(fs.readFileSync(new URL('../locations.json',import.meta.url)));
const stock=JSON.parse(fs.readFileSync(new URL('../sites/cup-stock.json',import.meta.url)));
const leaderboard=new DatabaseSync(process.env.TW_CUP_DB||fileURLToPath(new URL('./tournament.sqlite',import.meta.url)));
leaderboard.exec('CREATE TABLE IF NOT EXISTS cup_entries(day INTEGER NOT NULL,angler TEXT NOT NULL,best INTEGER NOT NULL,PRIMARY KEY(day,angler))');
const cupDB={
 prepare(sql){return {bind(...values){return {sql,values}}}},
 batch(statements){
  leaderboard.exec('BEGIN');
  try{
   const results=statements.map(({sql,values})=>({results:leaderboard.prepare(sql).all(...values)}));
   leaderboard.exec('COMMIT');return results;
  }catch(error){leaderboard.exec('ROLLBACK');throw error;}
 }
};
const sessions=new Map(), rooms=new Map();
const invite=crypto.randomBytes(18).toString('hex');
const host=process.env.TW_HOST||Object.values(os.networkInterfaces()).flat().find(a=>a.family==='IPv4'&&!a.internal)?.address;
if(!host||!/^[a-zA-Z0-9.-]+$/.test(host))throw Error('Set TW_HOST to the LAN IPv4 address or certificate hostname.');
const port=Number(process.env.TW_PORT||8443),udpPort=Number(process.env.TW_UDP_PORT||42438);
const tls=process.env.TW_CERT&&process.env.TW_KEY;
const joinURL=(tls?'https://':'http://')+host+':'+port+'/?join='+invite;
const picture=await qr.toDataURL(joinURL,{margin:4,width:420});
if(process.env.TW_QR)await qr.toFile(process.env.TW_QR,joinURL,{width:540,margin:4});
function event(id,spot,round,score){
 const now=Date.now();
 if(!Number.isInteger(spot)||spot<0||spot>=spots.length||!Number.isSafeInteger(score)||score<0||score>5000||!Number.isInteger(round))return null;
 let room=rooms.get(spot);
 if(!room||now>=room.end){room={id:crypto.randomInt(1,0x7fffffff),end:now+180000,players:new Map()};rooms.set(spot,room);}
 let player=room.players.get(id);
 if(!player){if(room.players.size>=64)return null;player={score:0,seen:now};room.players.set(id,player);}
 if(round===room.id)player.score=Math.max(player.score,score);
 player.seen=now;
 const all=[...room.players.values()];
 return {round:room.id,spot,seconds:Math.max(0,Math.ceil((room.end-now)/1000)),players:all.filter(p=>now-p.seen<5000).length,total:all.reduce((a,b)=>a+b.score,0),goal:8};
}
function handler(req,res){
 const url=new URL(req.url,'http://local');res.setHeader('Cache-Control','no-store');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('X-Content-Type-Options','nosniff');
 const reply=(status,type,data)=>{res.writeHead(status,{'Content-Type':type});res.end(data);};
 if(req.method==='GET'&&url.pathname==='/pair'){
  if(!['::1','127.0.0.1','::ffff:127.0.0.1'].includes(req.socket.remoteAddress))return reply(403,'text/plain','Open pairing on the host computer.');
  return reply(200,'text/html','<title>Thai Waters pairing</title><h1>Scan to fish</h1><img alt="Private LAN invitation" src="'+picture+'"><p>Use the same Wi-Fi. Motion needs trusted HTTPS.</p><a href="'+joinURL+'">Open game</a>');
 }
 if(req.method==='GET'&&url.pathname==='/'&&url.searchParams.get('join')===invite){
  const token=crypto.randomBytes(18).toString('hex');sessions.set(token,Date.now());res.setHeader('Set-Cookie','tw='+token+'; HttpOnly; SameSite=Strict; Path=/'+(tls?'; Secure':''));res.writeHead(303,{Location:'/'});return res.end();
 }
 const token=/\btw=([0-9a-f]{36})\b/.exec(req.headers.cookie||'')?.[1];
 if(!sessions.has(token))return reply(403,'text/plain','Scan the invitation on the host computer.');
 if(req.method==='GET'&&url.pathname==='/'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});return fs.createReadStream(game).pipe(res);}
 if(req.method==='POST' && url.pathname==='/event/cup' && req.headers['content-type']==='application/json'){
  let body='';req.on('data',b=>{body+=b;if(body.length>512)req.destroy();});req.on('end',async()=>{
   try{const result=await tournament(cupDB,token,JSON.parse(body),spots,stock);reply(result.error?400:200,'application/json',JSON.stringify(result));}
   catch{reply(400,'application/json','{"error":"Invalid report"}');}
  });return;
 }
 if(req.method==='POST'&&url.pathname==='/event'&&req.headers['content-type']==='application/json'){
  let body='';req.on('data',b=>{body+=b;if(body.length>512)req.destroy();});req.on('end',()=>{try{const b=JSON.parse(body),v=event(token,b.spot,b.round,b.score);reply(v?200:400,'application/json',JSON.stringify(v));}catch{reply(400,'text/plain','Invalid event');}});return;
 }
 reply(404,'text/plain','Unavailable');
}
const server=tls?https.createServer({cert:fs.readFileSync(process.env.TW_CERT),key:fs.readFileSync(process.env.TW_KEY)},handler):http.createServer(handler);
server.listen(port,process.env.TW_BIND||'0.0.0.0',()=>console.log('Host pairing page '+(tls?'https':'http')+'://localhost:'+port+'/pair'));
const udp=dgram.createSocket('udp4');
udp.on('message',async(buf,from)=>{
 const cup=/^TWC1 (\d{1,10}) (\d{1,3}) (\d{1,8}) (\d{1,3}) (\d{1,4})$/.exec(buf.toString());
 if(cup){
  const [id,spot,day,species,cm]=cup.slice(1).map(Number);
  if(!id||spot>=spots.length)return;
  const angler='device/'+id, goal=(await tournament(cupDB,angler,{action:'view'},spots,stock)).goal;
  const result=await tournament(cupDB,angler,cm?{action:'file',day,spot,species,cm}:{action:'join',day:goal.day},spots,stock);
  udp.send(['TWCR',id,goal.day,goal.spot,goal.species,goal.minimum,result.rank||0,result.best,result.leaders[0]?.cm||0].join(' '),from.port,from.address);return;
 }

 if(buf.length>100)return;const m=/^TW1 (\d{1,10}) (\d{1,3}) (\d{1,10}) (\d{1,4})$/.exec(buf.toString());if(!m)return;
 const [id,spot,round,score]=m.slice(1).map(Number);const v=event(from.address+'/'+id,spot,round,score);if(v)udp.send(['TW1R',id,spot,v.round,v.seconds,v.players,v.total].join(' '),from.port,from.address);
});
udp.bind(udpPort,process.env.TW_BIND||'0.0.0.0');


