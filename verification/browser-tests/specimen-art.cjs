const assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright-core');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{const p=await browser.newPage();await p.goto(pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href);await p.waitForFunction(()=>g&&!$('act').disabled);
 const result=await p.evaluate(async()=>{
  const seen=new Map(),shapes=new Set(),dupes=[],missing=[];
  const c=document.createElement('canvas');c.width=96;c.height=50;const ctx=c.getContext('2d',{willReadFrequently:true});
  const digest=async data=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data))).join('.');
  for(let id=0;id<atlas.fish.length;id++){
   if(!g.hasPortrait(id)){missing.push(id);continue;}
   if((atlas.fish[id].art??id)!==id)throw Error('Shared art ID '+id);
   ctx.clearRect(0,0,96,50);drawSpecimen(ctx,id,0,0,96,50);
   const rgba=ctx.getImageData(0,0,96,50).data,mask=new Uint8Array(4800);for(let i=0;i<4800;i++)mask[i]=rgba[i*4+3]?1:0;
   if(mask.some((on,i)=>on&&(i<96||i>=4704||i%96===0||i%96===95)))throw Error('Missing transparent margin on '+id);
   const area=mask.reduce((a,b)=>a+b,0);if(area<60)throw Error('Empty image '+id);
   let left=96,right=0,top=50,bottom=0;for(let i=0;i<mask.length;i++)if(mask[i]){const x=i%96,y=Math.floor(i/96);left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);}
   if(area>(right-left+1)*(bottom-top+1)*.94)throw Error('Opaque rectangular backing on '+id);
   const h=await digest(rgba);if(seen.has(h))dupes.push([id,seen.get(h)]);seen.set(h,id);shapes.add(await digest(mask));
  }
  const ids=Array.from({length:16},(_,i)=>2301+i);
  const plate=document.createElement('canvas');plate.width=720;plate.height=464;const ink=plate.getContext('2d');ink.imageSmoothingEnabled=false;ink.fillStyle='#203c34';ink.fillRect(0,0,plate.width,plate.height);
  ids.forEach((id,i)=>{const x=i%4*180,y=Math.floor(i/4)*116;drawSpecimen(ink,id,x+4,y+4,172,89);ink.fillStyle='#f0e7cf';ink.font='italic 12px Georgia';ink.fillText(atlas.fish[id].name,x+6,y+105,168);});
  return {count:seen.size,shapes:shapes.size,dupes,missing,sheet:plate.toDataURL()};
 });assert.deepEqual(result.dupes,[]);assert(result.missing.every(id=>id<2168),"Every addition from the Thai field-record import needs an individual illustration");const manifest=require('../../game/art-source/field/plates.json');assert.equal(result.count,60+manifest.reduce((a,p)=>a+p.ids.length,0));assert(result.shapes>result.count*.96);
 if(process.env.ART_PREVIEW)fs.writeFileSync(process.env.ART_PREVIEW,Buffer.from(result.sheet.split(',')[1],'base64'));
 console.log(result.count+' unique full-color portraits, '+result.shapes+' distinct alpha silhouettes; '+result.missing.length+' awaiting an illustration');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});