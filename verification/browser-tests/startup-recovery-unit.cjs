'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {bindStartupRecovery}=require('../../game/src/startup-recovery.js');

function fixture(){
 const elements=new Map();
 const $=id=>{
  if(!elements.has(id))elements.set(id,{hidden:true,textContent:'',value:'',files:[],focus(){}});
  return elements.get(id);
 };
 let retries=0,validated=[],used=[],downloads=[];
 const unchanged='{"synthetic":true}';
 const panel=bindStartupRecovery($,(en)=>en,{
  // startGame() hides/invalidate Recovery synchronously before starting async load.
  retry:()=>{retries++;panel.hide();},
  readRaw:()=>unchanged,
  parseBackup:raw=>{validated.push(raw);return {raw,book:[[1]]};},
  download:raw=>downloads.push(raw),
  useSession:backup=>used.push(backup.raw),
 });
 function select(file){const input=$('startupRecoveryFile');input.files=[file];return input.onchange();}
 panel.show(true);
 return {panel,$,validated,used,downloads,unchanged,select,retries:()=>retries};
}
function deferredFile(){
 let resolve;
 const data=new Promise(done=>{resolve=done;});
 return {file:{size:9,text:()=>data},resolve};
}

test('Retry invalidates a pending backup even if career Recovery reopens before the read resolves',async()=>{
 const f=fixture(),old=deferredFile();
 const pending=f.select(old.file);
 f.$('startupRetry').onclick();
 f.panel.show(true);
 old.resolve('old-valid');
 await pending;
 assert.equal(f.retries(),1);
 assert.equal(f.$('startupRecoveryUseSession').hidden,true);
 f.$('startupRecoveryUseSession').onclick();
 assert.deepEqual(f.validated,[]);
 assert.deepEqual(f.used,[]);
 assert.deepEqual(f.downloads,[]);
});

test('Older reads cannot replace a newer validated preview; session use commits exactly once',async()=>{
 const f=fixture(),old=deferredFile();
 const pending=f.select(old.file);
 await f.select({size:9,text:async()=>'new-valid'});
 old.resolve('old-valid');
 await pending;
 assert.equal(f.$('startupRecoveryUseSession').hidden,false);
 f.$('startupRecoveryUseSession').onclick();
 f.$('startupRecoveryUseSession').onclick();
 assert.deepEqual(f.validated,['new-valid']);
 assert.deepEqual(f.used,['new-valid']);
 f.$('startupRecoveryCopy').onclick();
 assert.deepEqual(f.downloads,[f.unchanged]);
});

test('A stalled preview cannot authorize session play after newer input is rejected',async()=>{
 const f=fixture(),old=deferredFile();
 const pending=f.select(old.file);
 await f.select({size:8*1024*1024+1,text:()=>assert.fail('oversize payload should not be read')});
 old.resolve('old-valid');
 await pending;
 assert.equal(f.$('startupRecoveryUseSession').hidden,true);
 f.$('startupRecoveryUseSession').onclick();
 assert.deepEqual(f.used,[]);
 assert.deepEqual(f.validated,[]);
});
