const {PNG}=require(require.resolve('pngjs',{paths:[require('node:path').resolve(__dirname,'../lan')]}));
// Segment the whole sheet before assigning cells. A long barbel or fin can
// cross a nominal grid boundary while still belonging to the same specimen.
function individuals(p,rows,file,cols=4){
 const w=p.width,h=p.height,labels=new Int32Array(w*h),queue=new Int32Array(w*h),parts=[];
 const corners=[0,w-1,(h-1)*w,w*h-1].map(i=>p.data[4*i+3]).sort((a,b)=>a-b);
 const cutoff=200;
 if(corners[2]>90){
  // Some transparent originals retain a light paper matte. Remove only paper
  // connected to the outside, preserving enclosed white scales and eyes.
  let written=0;
  function paper(k){
   const i=4*k;if(labels[k]||Math.min(p.data[i],p.data[i+1],p.data[i+2])<228)return;
   labels[k]=-1;queue[written++]=k;
  }
  for(let x=0;x<w;x++){paper(x);paper((h-1)*w+x);}
  for(let y=0;y<h;y++){paper(y*w);paper(y*w+w-1);}
  for(let i=0;i<written;i++){const j=queue[i],x=j%w;if(x)paper(j-1);if(x+1<w)paper(j+1);if(j>=w)paper(j-w);if(j+w<w*h)paper(j+w);}
 }
 let label=0;
 for(let start=0;start<labels.length;start++){
  if(labels[start]||p.data[4*start+3]<cutoff)continue;
  label++;let size=1,left=w,right=0,top=h,bottom=0;labels[start]=label;queue[0]=start;
  for(let i=0;i<size;i++){
   const j=queue[i],x=j%w,y=Math.floor(j/w);
   left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
   for(const k of [x>0?j-1:-1,x+1<w?j+1:-1,y>0?j-w:-1,y+1<h?j+w:-1]){
    if(k>=0&&!labels[k]&&p.data[4*k+3]>=cutoff){labels[k]=label;queue[size++]=k;}
   }
  }
  if(size>w*h/(rows*cols)*.025)parts.push({label,left,right,top,bottom,size});
 }
 const expected=rows*cols;parts.sort((a,b)=>b.size-a.size);
 if(parts.length<expected||parts[expected]?.size>parts[expected-1].size*.6)throw Error(file+' needs a cell review: '+parts.length+' components for '+expected+' species');
 const chosen=parts.slice(0,expected).sort((a,b)=>(a.top+a.bottom)-(b.top+b.bottom)),out=[];
 for(let i=0;i<expected;i+=cols){
  const row=chosen.slice(i,i+cols).sort((a,b)=>(a.left+a.right)-(b.left+b.right));
  for(const part of row){
   const crop=new PNG({width:part.right-part.left+1,height:part.bottom-part.top+1});
   for(let y=0;y<crop.height;y++)for(let x=0;x<crop.width;x++){
    const k=(y+part.top)*w+x+part.left;if(labels[k]!==part.label)continue;
    p.data.copy(crop.data,4*(y*crop.width+x),4*k,4*k+4);
   }
   out.push(crop);
  }
 }
 return out;
}
module.exports={individuals};
