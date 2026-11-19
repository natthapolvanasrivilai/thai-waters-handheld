import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import {dailyCup,tournament} from './cup.mjs';
const read=name=>JSON.parse(readFileSync(new URL(name,import.meta.url)));
const stock=read('./cup-stock.json');
// Running from either the product checkout or its game-only Site export.
const spots=read(existsSync(new URL('./locations.json',import.meta.url))?'./locations.json':'../locations.json');
const catalogFile=new URL('../content/catalog.json',import.meta.url);
if(existsSync(catalogFile)){
 const source=read('../content/catalog.json').fish;
 assert.deepEqual(stock,source.map(({name,site,low,high},id)=>({id,name,site,low,high})));
}
const db=new DatabaseSync(':memory:');
db.exec(readFileSync(new URL('./drizzle/0001_angler_cup.sql',import.meta.url),'utf8'));
const binding={prepare(sql){return {bind(...args){return {sql,args}}}},batch(rows){return rows.map(({sql,args})=>({results:db.prepare(sql).all(...args)}));}};
const start=Date.UTC(2026,10,18,16,59,30);
const goal=dailyCup(start,spots,stock),{day,spot,species,minimum}=goal;
const play=(id,report,now=start)=>tournament(binding,id,report,spots,stock,now);
const entry={action:'file',day,spot,species,cm:minimum};
assert.equal((await play('outsider',entry)).accepted,false);
for(const id of ['a','b','c'])await play(id,{action:'join',day});
for(const bad of [{cm:minimum-1},{species:species+1},{spot:spot+1},{cm:goal.maximum+1},{day:day-1}])
 assert.equal((await play('a',{...entry,...bad})).accepted,false);
for(const id of ['a','b'])assert.equal((await play(id,entry)).rank,1);
const winner=await play('c',{...entry,cm:minimum+1});
assert.deepEqual(winner.leaders.map(r=>r.rank),[1,2,2]);
assert.equal((await play('c',entry)).best,minimum+1);
assert.equal((await play('b',{action:'view'})).rank,2);
const tomorrow=await play('a',entry,start+30000);
assert.equal(tomorrow.accepted,false);assert.equal(tomorrow.joined,false);
assert.equal(tomorrow.goal.day,day+1);assert.equal(tomorrow.leaders.length,0);
assert.equal(new Set(Array.from({length:117},(_,i)=>dailyCup(start+i*86400000,spots,stock).spot)).size,117);
console.log('PASS Bangkok rollover, 117 host waters, entry validation, ties, retry and personal rank for three competitors.');
