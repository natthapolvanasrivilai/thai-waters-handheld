import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync,spawn} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
import {join,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
export const H=b=>createHash('sha256').update(b).digest('hex');
export const BASE='http://127.0.0.1:17841/';
export const SHA='8c41baca1b3ac54dd78401f2c6b21fd0086e6d70e181d509c2151a2985d47e96';
const outer='a01b2f7d2cd7a5bacacd08ba8ed2d0fb2f0a14e11cd4458bcd8ac868c7681344';
const source='0ba72cf4c55f141fbd0f692a7e2bf8cfb83ba984';
import {readFileSync} from 'node:fs';
const wrapperSHA='186be8b941cad03feb94f90bc24d10316397979d4cefd479fcdab5cac52dd41c';
const launcherSHA='0b0791dcb8bcb5c5a049eff2d56b4e535a56e54e20ea1569506d424691006705';
export async function prepare(dir){
 const path=relative=>fileURLToPath(new URL(relative,import.meta.url));
 const browser=process.env.POCKET_REEL_SOLO_BROWSER_ZIP,zip=process.env.POCKET_REEL_SOLO_WRAPPER_ZIP;
 assert(browser&&zip&&isAbsolute(browser)&&isAbsolute(zip),'Pinned disposable package paths required');
 const verified=JSON.parse(execFileSync('python3',[
  path('./pack.py'),'verify','--output',zip,
  '--browser',browser,
  '--browser-sha256',outer,'--source',source,
  '--launcher',path('./Start-Pocket-Reel-Solo-upgrade-reject.mjs')
 ],{encoding:'utf8'}));
 assert.equal(verified.wrapperZipSha256,wrapperSHA);assert.equal(H(readFileSync(zip)),wrapperSHA);
 const get=name=>execFileSync('unzip',['-p',zip,name],{maxBuffer:20*2**20});
 const bytes=get('Thai-Waters-play.html'); assert.equal(H(bytes),SHA);
 const program=get('Start-Pocket-Reel-Solo.mjs');assert.equal(H(program),launcherSHA);
 const pinned=get('Pocket-Reel-HTML.sha256');assert.equal(pinned.toString(),SHA+'  Thai-Waters-play.html\n');
 const script=join(dir,'Start-Pocket-Reel-Solo.mjs'), manifest=join(dir,'Pocket-Reel-HTML.sha256');
 await writeFile(script,program,{flag:'wx'});
 await writeFile(join(dir,'Thai-Waters-play.html'),bytes,{flag:'wx'});
 await writeFile(manifest,pinned,{flag:'wx'});
 return {script,manifest,bytes,wrapperSHA};
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
