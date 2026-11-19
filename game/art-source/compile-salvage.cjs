// Bake the recoverable-object plate for both 480 × 320 renderers.
const fs=require('node:fs'),path=require('node:path');
const {PNG}=require(require.resolve('pngjs',{paths:[path.resolve(__dirname,'../lan')]}));
const {extract}=require('./compile.cjs');
const items=require('../content/salvage.json');
const plate=PNG.sync.read(fs.readFileSync(path.join(__dirname,'recovered-items.png')));
const sheet=new PNG({width:4*96,height:3*50}),palettes=[],frames=[],seen=new Set();
const tags=['any','bank','landing','stony','flow','landingInland','still','maritime','rockyCoast','estuary'];
if(items.length!==12)throw Error('Expected 12 cells');
for(const [id,item] of items.entries()){
 const row=Math.floor(id/4),col=id%4,{indices,palette}=extract(plate,4,row,col,3);
 const key=indices.join('');if(seen.has(key)||indices.filter(Boolean).length<90)throw Error('Check portrait '+item.key);seen.add(key);
 const packed=[];
 for(let j=0;j<4800;j++){
  const c=indices[j],v=palette[c],k=4*((row*50+Math.floor(j/96))*sheet.width+col*96+j%96);
  sheet.data[k]=Math.round((v>>11)*255/31);sheet.data[k+1]=Math.round(((v>>5)&63)*255/63);sheet.data[k+2]=Math.round((v&31)*255/31);sheet.data[k+3]=c?255:0;
  if(!(j%2))packed.push((c<<4)|indices[j+1]);
 }
 palettes.push('{'+palette+'}');frames.push('{'+packed+'}');
}
const fw=path.resolve(__dirname,'../../firmware/WillowCreek');
fs.writeFileSync(path.join(__dirname,'../assets/salvage.png'),PNG.sync.write(sheet));
fs.writeFileSync(path.join(fw,'SalvageArt.h'),'#pragma once\n#include <cstdint>\nnamespace salvage {\nconstexpr uint16_t ink[][16]={'+palettes.join(',\n')+'};\nconstexpr uint8_t pixels[][2400]={'+frames.join(',\n')+'};\n}\n');
const rows=items.map(item=>{
 if(item.sites.some(t=>!tags.includes(t)))throw Error('Unknown habitat '+item.key);
 return '{'+[JSON.stringify(item.name),JSON.stringify(item.group),item.turns.toFixed(2)+'f',item.sites.join('|')].join(',')+'}';
});
fs.writeFileSync(path.join(fw,'SalvageCatalog.h'),'#pragma once\n#include <cstdint>\nnamespace salvage {\nenum Habitat : uint16_t {'+tags.map((t,i)=>t+'='+2**i).join(',')+'};\nstruct Item{const char* name;const char* group;float turns;uint16_t habitats;};\nconstexpr Item items[]={\n'+rows.join(',\n')+'\n};\nconstexpr int count=sizeof(items)/sizeof(items[0]);\n}\n');
