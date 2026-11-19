const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const bytes = fs.readFileSync(path.join(__dirname, '../../game/assets/atlas.wasm'));
const moduleUnderTest = new WebAssembly.Module(bytes);
let g;
const env = {
  memset(p, value, size) { new Uint8Array(g.memory.buffer, p, size).fill(value); return p; },
  sinf: Math.sin, acosf: Math.acos, atan2f: Math.atan2,
  lroundf: x => Math.sign(x) * Math.round(Math.abs(x))
};
g = new WebAssembly.Instance(moduleUnderTest, { env }).exports;
const fixture = (seed, kind, coords) => {
  g.initialize(seed); g.place(0, 0);
  const [x, y] = coords || [g.zoneX(kind), g.zoneY(kind)];
  assert.equal(g.featureAt(x, y), kind);
  g.setAim(x, y); g.advance(16, 1, 0, 0);
  assert.equal(g.state(), 1);
  g.advance(650, 0, 0, 0);
};
for (const name of ['state','caught','advance','samples','rodLoad','rumbleEvent','setAim','aimX','aimY','zoneX','zoneY','zoneRX','zoneRY','featureAt','contact','junkId','releaseProgress','abandonCast']) {
  assert.equal(typeof g[name], 'function', name);
}
assert(Object.keys(g).length >= 67);
fixture(1, 1);
assert.equal(g.state(), 7); assert.equal(g.contact(), 1);
assert.equal(g.rumbleEvent(670, 1), 5);
g.advance(510, 0, 0, 0); assert.equal(g.releaseProgress(), 1);
g.advance(16, 0, 1, 0); assert.equal(g.state(), 2);
assert.equal(g.rumbleEvent(1200, 1), 1); assert.equal(g.rumbleEvent(1216, 1), 0);
fixture(1, 2); g.restPose(0, 0, 1); assert.equal(g.liftPose(0, .8660254, .5), 1);
g.gesture(0, 10); g.gesture(80, 100); assert.equal(g.rodUp(), 1);
g.advance(250, 0, 0, -.2); assert.equal(g.releaseProgress(), 0);
g.gesture(0, 400); assert.equal(g.rodUp(), 0);
g.dialReset(); g.dialSample(2000, 400);
for (let i=1;i<=4;i++) {
  const turns = g.dialSample(2000-325*i, 400+40*i);
  assert(turns < 0); g.advance(40, 0, 0, turns);
}
assert.equal(g.state(), 2);
fixture(1, 2); g.abandonCast(); assert.equal(g.state(), 0);
fixture(1, 2); g.advance(500, 0, 0, 1);
assert.equal(g.state(), 6); assert.equal(g.reason(), 3);
for (const [seed, id] of [[9,0],[11,1],[19,2],[2,3]]) {
  fixture(seed, 3); assert.equal(g.state(), 8); assert.equal(g.junkId(), id);
  assert.equal(g.rumbleEvent(666,1), 3);
  g.restoreEntry(0, 2, 21); assert.equal(g.caught(0),2); const book = [g.caught(0),g.best(0),g.pts(),g.catches()];
  for(let i=0;i<24 && g.state()===8;i++) g.advance(100, 0, 0, .08);
  assert.equal(g.state(), 9); assert.equal(g.releaseProgress(), 1); assert.equal(g.rumbleEvent(3100,1), 1);
  assert.deepEqual([g.caught(0),g.best(0),g.pts(),g.catches()], book);
  assert.equal(g.fresh(), 0);assert.equal(g.award(),0);
  g.setAim(.50,.67);g.advance(15,1,0,0);g.advance(650,0,0,0);assert.equal(g.state(),2);
}
fixture(1, 3); assert.equal(g.state(), 2);  // A miss even in the debris core.
fixture(36, 0, [.88,.85]); assert.equal(g.state(), 8); // Accidental open-water pickup.
for(let seed=1;seed<=300;seed++) {fixture(seed,0);assert.equal(g.state(),2);}
fixture(1,1);g.place(16,1);assert.equal(g.state(),0);assert.equal(g.contact(),0);
console.log('PASS atlas.wasm, '+Object.keys(g).length+' exports, seed fixtures, phone gesture, signed encoder, release, retry, rumble and protected journal.');

