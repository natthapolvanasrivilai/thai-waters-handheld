// Pure state for a representative map. No engine, DOM, clock, or save access.
const waterbodyMapModel=(()=>{
 function create(rows,width,height){
  let x=0,y=0,selected=null,active=null;
  const ids=new Set(rows.map(row=>row[0])),limit=(v,n)=>Math.min(n,Math.max(-n,v));
  const project=([lon,lat])=>[width/2+(lon-101.1)*10.2,height/2+(13.1-lat)*10.6];
  function point(row){const [a,b]=project(row.slice(1));return [a+x,b+y];}
  function pick(px,py){
   if(px<0||py<0||px>width||py>height)return null;
   let best=14,choice=null;
   for(const row of rows){
    const [a,b]=point(row);
    if(a<0||b<0||a>width||b>height)continue;
    const d=Math.hypot(a-px,b-py);
    if(d<best){best=d;choice=row[0];}
   }
   return choice;
  }
  function choose(id){if(id!==null&&!ids.has(id))return false;selected=id;return true;}
  function panTo(a,b){x=limit(a,44);y=limit(b,26);}
  function start(id,p){
   if(active)return false;
   active={id,p,x,y,at:pick(p.x,p.y),drag:false};return true;
  }
  const distance=(p,q)=>Math.hypot(p.clientX-q.clientX,p.clientY-q.clientY);
  function move(id,p){
   if(!active||id!==active.id)return false;
   if(!active.drag&&distance(p,active.p)<7)return false;
   active.drag=true;panTo(active.x+p.x-active.p.x,active.y+p.y-active.p.y);return true;
  }
  function cancel(id){if(!active||id!==active.id)return false;active=null;return true;}
  function end(id,p){
   if(!active||id!==active.id)return false;
   const prev=active;active=null;
   return !prev.drag&&distance(p,prev.p)<7&&prev.at!==null&&pick(p.x,p.y)===prev.at&&choose(prev.at);
  }
  return {project,pick,choose,start,move,cancel,end,pan:()=>[x,y],resetPan:()=>panTo(0,0),
   panBy:(a,b)=>panTo(x+a,y+b),selected:()=>selected,
   position:id=>point(rows.find(r=>r[0]===id)),
   confirm:(allowed,go)=>allowed&&selected!==null?go(selected):false};
 }
 return {create};
})();
