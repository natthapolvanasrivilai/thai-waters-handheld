// Compare the production WebAssembly pixels to the handheld's C++ scanline raster.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
(async()=>{
 const {instance:{exports:scene}}=await WebAssembly.instantiate(fs.readFileSync(path.join(root,'game/assets/landscape.wasm')));
 const spots=JSON.parse(fs.readFileSync(path.join(root,'game/locations.json')));
 const references=fs.readFileSync(process.argv[2],'utf8').trim().split(/\r?\n/);
 assert.equal(references.length,spots.length*4);
 for(const line of references){
   const [site,age,expected]=line.trim().split(/\s+/).map(Number);
   const at=scene.arrivalPixels(site,spots[site].pool,age);
   const data=new Uint8Array(scene.memory.buffer,at,240*160);
   let hash=2166136261>>>0;
   for(let i=0;i<data.length;i++)if(data[i]!==255){
     assert(data[i]<64);
     hash=Math.imul(hash^(i*64+data[i]),16777619)>>>0;
   }
   assert.equal(hash,expected,'arrival pixels at '+spots[site].name+' '+age+'ms');
 }
 console.log('PASS '+references.length+' handheld-source and browser arrival layers match pixel for pixel across all four approaches.');
})().catch(e=>{console.error(e);process.exitCode=1;});