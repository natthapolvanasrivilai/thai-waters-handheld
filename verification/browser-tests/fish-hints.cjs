const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const wasm=fs.readFileSync(process.env.ATLAS_WASM||path.join(__dirname,'../../game/assets/atlas.wasm'));
const mod=new WebAssembly.Module(wasm);
let g;
const env={
 memset(p,v,n){new Uint8Array(g.memory.buffer,p,n).fill(v);return p;},
 sinf:Math.sin,acosf:Math.acos,atan2f:Math.atan2,
 lroundf:x=>Math.sign(x)*Math.round(Math.abs(x))
};
g=new WebAssembly.Instance(mod,{env}).exports;
assert.equal(g.fishHintSpecies,undefined,'never export the unrevealed species');
const found=new Set();
for(let p=0;p<117;p++){
 g.initialize(817+p);g.place(p,0);g.fishHintsEnabled(1);
 g.advance(40000,0,0,0);assert.equal(g.sampleFishHint(),0);
 let kind,x,y;
 for(let t=40000;t<72000;t+=100){
   g.advance(100,0,0,0);kind=g.sampleFishHint();
   if(kind){x=g.fishHintX();y=g.fishHintY();break;}
 }
 if(!kind)continue;
 found.add(kind);
 assert(x>=.12&&x<=.88&&y>=.59&&y<=.82);
 assert.equal(g.featureAt(x,y),0);
 g.fishHintsEnabled(0);assert.equal(g.sampleFishHint(),0,'Cup gate clears immediately');
 g.fishHintsEnabled(1);assert.equal(g.sampleFishHint(),0,'old hint cannot reappear');
 if(found.size===2)break;
}
assert.deepEqual([...found].sort(),[1,2]);
console.log('PASS actual WASM has both silhouette sizes, clear water band, Cup disable/restore, and no leaked species ID');

// Both competitive modes gate the actual packaged renderer and cast path.
const html=fs.readFileSync(path.join(__dirname,'../../game/Thai-Waters-play.html'),'utf8');
const guard=html.match(/^function fishHintsAllowed\(\)\{[^\n]+\}$/m);
assert(guard,'Missing shared competitive guard in packaged HTML');
const hintsAllowed=new Function('crewOn','cupIsJoined',guard[0]+'\nreturn fishHintsAllowed();');
assert(hintsAllowed(false,()=>false));
for(const [crew,cup] of [[true,false],[false,true],[true,true]])assert(!hintsAllowed(crew,()=>cup));
assert.match(html,/function paintFishHint\(\)\{\s+if\(menu.open\|\|!fishHintsAllowed\(\)\)return;/);
assert.match(html,/g\.fishHintsEnabled\(fishHintsAllowed\(\)\);g\.advance\(/);
console.log('PASS both Daily Cup and Crew challenge disable the browser cue and cast bonus');
