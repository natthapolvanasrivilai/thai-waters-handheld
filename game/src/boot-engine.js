// Bind C imports inside one instantiation, never through the currently live
// browser engine. Overlapping prepares must not address each other's memory.
async function instantiateBootEngine(bytes,instantiate=WebAssembly.instantiate){
 let memory;
 const env={
  memset:(p,v,n)=>{
   if(!memory)throw Error('Game memory is not bound');
   new Uint8Array(memory.buffer,p,n).fill(v);return p;
  },
  acosf:Math.acos,atan2f:Math.atan2,sinf:Math.sin,lroundf:x=>Math.sign(x)*Math.round(Math.abs(x))
 };
 const result=await instantiate(bytes,{env});
 memory=result.instance.exports.memory;
 return result;
}
if(typeof module!=='undefined'&&module.exports)module.exports={instantiateBootEngine};
