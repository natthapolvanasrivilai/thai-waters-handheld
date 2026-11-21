'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const {traceDocumentStart}=require('./reload-document-start.cjs');

function observe(type, initial={}, blocked=false){
 const data=new Map(Object.entries(initial));
 const context={window:{},performance:{getEntriesByType:()=>type?[{type}]:[]},localStorage:{
  getItem(k){if(blocked&&k==='thai-atlas-v2')throw new Error('blocked');return data.get(k)??null;},
  setItem(k,v){data.set(k,v);}
 }};
 vm.runInNewContext('('+traceDocumentStart.toString()+')({expectedPlace:16})',context);
 return {trace:JSON.parse(JSON.stringify(context.window.__pr62docStart)),data};
}
test('initial navigation seeds independent canary and preserves the original English fixture',()=>{
 const {trace,data}=observe('navigate');
 assert.deepEqual(trace,{navigation:'navigate',storage:'missing',schema:null,matched:null,canary:'present'});
 assert.equal(data.get('thai-waters-language'),'en');
});
test('reload does not replace a vanished canary or rewrite the career save',()=>{
 const {trace,data}=observe('reload');
 assert.deepEqual(trace,{navigation:'reload',storage:'missing',schema:null,matched:null,canary:'missing'});
 assert(!data.has('pocket-reel-62-arrival-canary')&&!data.has('thai-atlas-v2'));
});
test('only redacted flags survive, including accepted input shape, denied access and unknown navigation',()=>{
 const raw=JSON.stringify({schema:4,place:16,book:{private:'never-log'}});
 const input={'pocket-reel-62-arrival-canary':'fixture-v1','thai-atlas-v2':raw};
 const {trace,data}=observe('reload',input);
 assert.deepEqual(trace,{navigation:'reload',storage:'present',schema:4,matched:true,canary:'present'});
 assert.equal(data.get('thai-atlas-v2'),raw);
 assert.equal(observe('reload',input,true).trace.storage,'blocked');
 assert.equal(observe(undefined).trace.canary,'missing');
 assert(!JSON.stringify(trace).includes('never-log'));
});
