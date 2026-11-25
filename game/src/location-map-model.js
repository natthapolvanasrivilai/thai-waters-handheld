// Pure state for a representative map. No engine, DOM, clock, or save access.
const waterbodyMapModel=(()=>{
 function create(rows,width,height){
  let x=0,y=0,selected=null,active=null,pending=[];
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
  function targets(px,py){
   if(px<0||py<0||px>width||py>height)return [];
   const close=[];
   for(const row of rows){
    const [a,b]=point(row);
    if(a>=0&&b>=0&&a<=width&&b<=height&&Math.hypot(a-px,b-py)<=6)close.push(row[0]);
   }
   if(close.length)return close;
   const nearest=pick(px,py);return nearest===null?[]:[nearest];
  }
  function cancelChoice(){const had=pending.length>0;pending=[];return had;}
  function choose(id){if(id!==null&&!ids.has(id))return false;cancelChoice();selected=id;return true;}
  function resolve(id){return pending.includes(id)&&choose(id);}
  function panTo(a,b){cancelChoice();x=limit(a,44);y=limit(b,26);}
  function start(id,p){
   if(active)return false;
   active={id,p,x,y,at:targets(p.x,p.y),drag:false};return true;
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
   if(prev.drag||distance(p,prev.p)>=7)return false;
   const now=targets(p.x,p.y);
   if(!now.length||now.length!==prev.at.length||!now.every((id,i)=>id===prev.at[i]))return false;
   if(now.length===1)return choose(now[0]);
   pending=now;return true;
  }
  return {project,pick,choose,start,move,cancel,end,resolve,cancelChoice,pending:()=>pending.slice(),pan:()=>[x,y],resetPan:()=>panTo(0,0),
   panBy:(a,b)=>panTo(x+a,y+b),selected:()=>selected,
   position:id=>point(rows.find(r=>r[0]===id)),
   confirm:(allowed,go)=>allowed&&!pending.length&&selected!==null?go(selected):false};
 }
 // A browser can omit the compatibility click for the first touch after a pan.
 // Compare native event facts only; do not synthesize clicks or touch global state.
 function createTouchActivation(){
  const radius=12, maxAge=500;
  let contact=null,completed=null;
  const close=(e,start)=>Math.hypot(e.clientX-start.x,e.clientY-start.y)<=radius;
  const primaryTouch=e=>e.isTrusted&&e.pointerType==='touch'&&e.isPrimary;
  const at=e=>({id:e.pointerId,x:e.clientX,y:e.clientY});
  function down(e,scope){
   if(e.isTrusted&&e.isPrimary)completed=null;
   const wasActive=contact!==null;contact=null;
   if(wasActive||scope===null||!primaryTouch(e)||e.button!==0)return false;
   contact={...at(e),scope};return true;
  }
  function move(e){if(contact?.id===e.pointerId&&!close(e,contact))contact=null;}
  function cancel(e){if(contact?.id===e.pointerId)contact=null;}
  function up(e,scope,activate){
   const start=contact;
   if(start?.id!==e.pointerId)return false;
   contact=null;
   if(!primaryTouch(e)||scope===null||scope!==start.scope||!close(e,start)||!activate(scope))return false;
   completed={...at(e),until:e.timeStamp+maxAge};return true;
  }
  function consume(e){
   const end=completed;
   if(!end||!e.isTrusted||!e.detail||e.timeStamp>end.until||!close(e,end))return false;
   if(e.pointerType==='touch'){
    if(e.pointerId!==end.id)return false;
   }else if(!e.sourceCapabilities?.firesTouchEvents&&e.pointerType)return false;
   completed=null;return true;
  }
  return {down,move,cancel,up,consume};
 }
 return {create,createTouchActivation};
})();
