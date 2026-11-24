import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {lstat,readFile,writeFile} from 'node:fs/promises';
import {join,isAbsolute} from 'node:path';
export const H=b=>createHash('sha256').update(b).digest('hex');
export const BASE='http://127.0.0.1:17841/';
export const SHA='0f87d0c63afd86d97602b401967a8c13d75aabfda9a674e6d16a17efc3457f2e';
export async function prepare(dir){
 const folder=process.env.POCKET_REEL_HOLD_PACKAGE;
 assert(folder&&isAbsolute(folder),'Absolute disposable extracted package required');
 const get=async name=>{const src=join(folder,name);assert((await lstat(src)).isFile());return readFile(src)};
 const bytes=await get('Thai-Waters-play.html');
 assert.equal(H(bytes),SHA);
 const program=await get('Start-Pocket-Reel-Solo.mjs');
 assert.equal(H(program),'0b0791dcb8bcb5c5a049eff2d56b4e535a56e54e20ea1569506d424691006705');
 const pinned=await get('Pocket-Reel-HTML.sha256');
 assert.equal(pinned.toString(),SHA+'  Thai-Waters-play.html\n');
 assert.match((await get('HOLD.txt')).toString(),/^ENGINEERING HOLD/);
 const script=join(dir,'Start-Pocket-Reel-Solo.mjs'),manifest=join(dir,'Pocket-Reel-HTML.sha256');
 await writeFile(script,program,{flag:'wx'});
 await writeFile(join(dir,'Thai-Waters-play.html'),bytes,{flag:'wx'});
 await writeFile(manifest,pinned,{flag:'wx'});
 return {script,manifest,bytes};
}
export function processFor(script){
 const child=spawn(process.execPath,[script],{stdio:['ignore','pipe','pipe']});
 const done=new Promise(resolve=>{
  let out='',err='';child.stdout.on('data',x=>out+=x);child.stderr.on('data',x=>err+=x);
  child.once('close',code=>resolve({code,out,err}));
 });
 const ready=new Promise((ok,no)=>{
  let out='';const t=setTimeout(()=>no(Error('Launcher did not become ready')),5000);
  child.stdout.on('data',x=>{out+=x;if(out.includes('Offline Pocket Reel: '+BASE+' ')){clearTimeout(t);ok();}});
  child.once('close',()=>{clearTimeout(t);no(Error('Launcher exited without readiness'));});
 });
 ready.catch(()=>{});
 return {pid:child.pid,ready,done,stop:async()=>{if(child.exitCode===null&&child.signalCode===null)child.kill('SIGTERM');await done;}};
}
