import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {eventResponse} from './event.mjs';

const db = new DatabaseSync(':memory:');
db.exec(readFileSync(new URL('./drizzle/0000_event_players.sql', import.meta.url), 'utf8'));
const binding = {
  prepare(sql) {return {bind(...params){return {sql, params}}}},
  batch(statements) {return statements.map(({sql,params})=>({results:db.prepare(sql).all(...params)}));}
};
const start = 1800000000000;
async function pulse(spot, round, score, cookie='', offset=0) {
  const response = await eventResponse(new Request('https://example.test/event', {
    method:'POST', headers:{'content-type':'application/json',cookie}, body:JSON.stringify({spot,round,score}),
  }), binding, 117, start+offset);
  return {status:response.status, cookie:response.headers.get('set-cookie')?.split(';')[0], ...await response.json()};
}
const a=await pulse(13,0,0), b=await pulse(13,0,0);
assert.equal(b.players,2);
assert.equal(b.round,a.round);
assert.notEqual(b.cookie,a.cookie);
await pulse(13,a.round,2,a.cookie);
assert.equal((await pulse(13,b.round,6,b.cookie)).total,8);
assert.equal((await pulse(13,b.round,1,b.cookie)).total,8);
assert.equal((await pulse(14,b.round,0,b.cookie)).total,0);
assert.equal((await pulse(13,a.round,2,a.cookie,6001)).players,1);
const next=await pulse(13,a.round,2,a.cookie,180001);
assert.notEqual(next.round,a.round);
assert.equal(next.total,0);
assert.equal((await pulse(117,0,0)).status,400);
console.log('PASS two phone sessions, separate spots, idempotent catches, expiry and round rollover.');
