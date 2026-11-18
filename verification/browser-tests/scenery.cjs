const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {readFileSync} = require('node:fs');
const path = require('node:path');

const game = path.resolve(__dirname, '../../game');
const locations = JSON.parse(readFileSync(path.join(game, 'locations.json')));
const wasm = readFileSync(path.join(game, 'assets/landscape.wasm'));
const digest = pixels => createHash('sha256').update(pixels).digest('hex');

async function verify() {
  const {instance: {exports: scene}} = await WebAssembly.instantiate(wasm);
  const seen = new Set();
  for (let period = 0; period < 4; ++period) {
    const silhouettes = new Set();
    for (const [index, place] of locations.entries()) {
      assert.equal(place.id, index, 'scenic recipes use stable catalog IDs');
      const address = scene.paintPlace(place.id, period);
      const indices = new Uint8Array(scene.memory.buffer, address, 240 * 160);
      const palette = new Uint32Array(scene.memory.buffer, scene.placePalette(), 64);
      const rgb = Buffer.alloc(240 * 160 * 3);
      for (const [i, ink] of indices.entries()) {
        assert.ok(ink < palette.length);
        rgb.writeUIntBE(palette[ink], i * 3, 3);
      }
      const rendered = digest(rgb);
      assert.ok(!seen.has(rendered), place.name + ' repeats an existing frame');
      seen.add(rendered);
      // Strip all hues and fine details. Only counts of land / structures in
      // each 10x10 block survive, so tiny color changes cannot pass this check.
      const mass = Buffer.alloc(24 * 16);
      for (let x = 0; x < 240; ++x) for (let y = 0; y < 160; ++y) {
        const ink = indices[x * 160 + 159 - y];
        if (ink >= 26 && ink <= 47 && ink !== 39)
          mass[Math.floor(y / 10) * 24 + Math.floor(x / 10)]++;
      }
      const shape = digest(mass);
      assert.ok(!silhouettes.has(shape), place.name + ' repeats a structural composition');
      silhouettes.add(shape);
    }
  }
  console.log(seen.size + ' unique scenes. Each time period has ' + locations.length +
    ' distinct paint layouts after stripping color and downsampling to 24 x 16.');
}
verify().catch(error => {console.error(error);process.exitCode = 1;});
