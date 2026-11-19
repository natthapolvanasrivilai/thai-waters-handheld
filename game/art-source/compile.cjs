// Compile the original transparent artwork into one LCD atlas and packed, per-sprite RGB565 palettes.
const fs=require('node:fs'),path=require('node:path');
const {PNG}=require(require.resolve('pngjs',{paths:[path.resolve(__dirname,'../lan')]}));
const w=96,h=50,columns=10,count=60;
const colors=['fffbe5','102c33','173e42','284848','385a55','536c62','758172','9aa38b','c0c4a8','e3dec2',
 '123b44','175158','256764','41827b','60a394','8ebaa5','bbd9bb','34475a','4e6271','788e93','a9b9b3','d8e1cd',
 '342e29','514335','71573d','937043','ba9159','dbb66c','ecd994','653d38','97503d','bb6848','dc8a55',
 '3a4741','5b6144','768052','a2a866','583d52','805c70','a98386','324d63','48768b','6292a2','294c68','99773d'
].map(hex=>[0,2,4].map(k=>parseInt(hex.slice(k,k+2),16)));
const dist=(a,b)=>2*(a[0]-b[0])**2+3*(a[1]-b[1])**2+(a[2]-b[2])**2;
const nearest=(c,ids)=>ids.reduce((a,b)=>dist(c,colors[a])<dist(c,colors[b])?a:b);
function extract(p,cols,row,col,rows=2){
 const x0=Math.floor(col*p.width/cols),x1=Math.floor((col+1)*p.width/cols),y0=Math.floor(row*p.height/rows),y1=Math.floor((row+1)*p.height/rows);
 const sw=x1-x0,sh=y1-y0,mask=new Uint8Array(sw*sh),queue=new Int32Array(sw*sh);
 for(let y=0;y<sh;y++)for(let x=0;x<sw;x++)mask[y*sw+x]=p.data[4*((y+y0)*p.width+x+x0)+3]>=128?1:0;
 let bounds=null,best=0;
 for(let j=0;j<mask.length;j++)if(mask[j]===1){
  let n=1,loX=sw,hiX=0,loY=sh,hiY=0;mask[j]=2;queue[0]=j;
  for(let i=0;i<n;i++){const q=queue[i],x=q%sw,y=Math.floor(q/sw);
   loX=Math.min(loX,x);hiX=Math.max(hiX,x);loY=Math.min(loY,y);hiY=Math.max(hiY,y);
   for(const [dx,dy] of [[0,1],[0,-1],[1,0],[-1,0]]){const xx=x+dx,yy=y+dy,k=yy*sw+xx;if(xx>=0&&xx<sw&&yy>=0&&yy<sh&&mask[k]===1){mask[k]=2;queue[n++]=k;}}
  }
  if(n>best){best=n;bounds=[loX+x0,loY+y0,hiX+x0+1,hiY+y0+1];}
 }
 if(best<sw*sh*.035)throw Error('Empty fish at '+[row,col]);
 const [left,top,right,bottom]=bounds,scale=Math.min((w-4)/(right-left),(h-4)/(bottom-top));
 const dw=Math.max(1,Math.round((right-left)*scale)),dh=Math.max(1,Math.round((bottom-top)*scale)),ox=(w-dw)>>1,oy=(h-dh)>>1;
 const raw=Array(w*h).fill(null),hist=colors.map(()=>0),ids=colors.map((_,i)=>i);
 for(let y=0;y<dh;y++)for(let x=0;x<dw;x++){
  const acc=[0,0,0];let alpha=0;
  for(let sy=0;sy<4;sy++)for(let sx=0;sx<4;sx++){
   const px=left+Math.floor((x+(sx+.5)/4)*(right-left)/dw),py=top+Math.floor((y+(sy+.5)/4)*(bottom-top)/dh);
   const k=(py*p.width+px)*4,a=p.data[k+3]/255;alpha+=a;for(let c=0;c<3;c++)acc[c]+=a*p.data[k+c];
  }
  if(alpha>=8){const rgb=acc.map(v=>v/alpha);const j=(oy+y)*w+ox+x;raw[j]=rgb;hist[nearest(rgb,ids)]++;}
 }
 const pal=[0,1];while(pal.length<15){let index=-1,score=-1;
  for(const id of ids){if(pal.includes(id))continue;const value=hist[id]*Math.min(...pal.map(a=>dist(colors[id],colors[a])));if(value>score){score=value;index=id;}}
  pal.push(index);
 }
 const indices=raw.map((rgb,j)=>{
  if(rgb)return pal.indexOf(nearest(rgb,pal))+1;
  return [j-1,j+1,j-w,j+w].some(k=>raw[k])?1:0;
 });
 return {indices,palette:[0,...pal.map(id=>{const [r,g,b]=colors[id];return ((r>>3)<<11)|((g>>2)<<5)|(b>>3);})]};
}
module.exports={extract};
if(require.main===module){
const sheet=new PNG({width:columns*w,height:Math.ceil(count/columns)*h}),inks=[],pixels=[];
for(let plate=0,id=0;id<count;plate++){
 const p=PNG.sync.read(fs.readFileSync(path.join(__dirname,'plate-'+plate+'.png'))),cols=plate===6?2:4;
 for(let n=0;n<cols*2;n++,id++){
  const {indices,palette}=extract(p,cols,Math.floor(n/cols),n%cols);
  const packed=[];
  for(let j=0;j<w*h;j++){const c=indices[j],v=palette[c],k=4*((Math.floor(id/10)*h+Math.floor(j/w))*sheet.width+(id%10)*w+j%w);
   sheet.data[k]=Math.round(((v>>11)&31)*255/31);sheet.data[k+1]=Math.round(((v>>5)&63)*255/63);sheet.data[k+2]=Math.round((v&31)*255/31);sheet.data[k+3]=c?255:0;
   if(j%2===0)packed.push((c<<4)|indices[j+1]);
  }
  inks.push('{'+palette+'}');pixels.push('{'+packed+'}');
 }
}
fs.writeFileSync(path.join(__dirname,'../assets/fish.png'),PNG.sync.write(sheet));
fs.writeFileSync(path.join(__dirname,'../../firmware/WillowCreek/FishArt.h'),'#pragma once\n#include <stdint.h>\nconstexpr uint16_t fishInk[][16]={'+inks.join(',\n')+'};\nconstexpr uint8_t fishArt[][2400]={'+pixels.join(',\n')+'};\n');
console.log(count+' sprites, 96 x 50, 4-bit artwork, 16 RGB565 palette entries each');
}
