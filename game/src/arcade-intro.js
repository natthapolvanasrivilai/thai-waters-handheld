// Pocket Reel title choreography. Visual-only; no game clock or save writes.
const arcadeIntro=(()=>{
 const revealMs=840, launchMs=1000;
 const ease=t=>t*t*(3-2*t);
 const clamp=t=>Math.max(0,Math.min(1,t));
 function createClock(){
  let phase='reveal',age=0,scene=0;
  const go=p=>{phase=p;age=0;return p;};
  return {
   get phase(){return phase;}, get age(){return age;}, get scene(){return scene;},
   reset(reduced=false){scene=0;return go(reduced?'title':'reveal');},
   start(reduced){if(phase!=='reveal'&&phase!=='title')return null;return go(reduced?'modes':'launch');},
   skip(){return phase==='launch'?go('modes'):null;},
   step(dt){
    if(!Number.isFinite(dt)||dt<=0)return null;
    age+=dt;scene=(scene+dt)%112000;
    if(phase==='reveal'&&age>=revealMs)return go('title');
    if(phase==='launch'&&age>=launchMs)return go('modes');
    return null;
   }
  };
 }
 function motion(ms,reduced){
  const t=reduced?0:ms;
  const ripples=Array.from({length:14},(_,i)=>{
   const y=170+i*10;
   const cluster=Math.sin(i*4.71)*122+225;
   return {x:cluster+Math.sin(t/(830+i*94)+i*.64)*(10+i*1.7),y,
    width:10+i*2.5+Math.sin(t/(1120+i*97)+i)*7,
    alpha:.18+.11*Math.sin(t/(740+i*98)+i*.9)};
  });
  const passing=t%28000-2600, birds=[];
  if(!reduced&&passing>=0&&passing<6900){
   for(let i=0;i<3;i++)birds.push({x:552-passing*.086+i*23,
     y:39+i*8+Math.sin(passing/495+i*.7)*5,
     flap:1+Math.abs(Math.sin(passing/110+i*.93))*3});
  }
  const reeds=Array.from({length:12},(_,i)=>({x:i<6?3+5*i:448+5*(i-6),
   height:26+(i*37)%40,bend:(i<6?-1:1)*(3+(i*3)%9)+Math.sin(t/740+i*.64)*3}));
  return {ripples,birds,reeds};
 }
 function paint(context,background,clock,reduced){
  const {phase,age,scene}=clock, {ripples,birds,reeds}=motion(scene,reduced);
  const reveal=phase==='reveal'?ease(clamp(age/revealMs)):1;
  const lift=phase==='launch'?ease(clamp(age/launchMs)):0;
  const overscan=(1-reveal)*8+lift*12;
  context.save();context.imageSmoothingEnabled=false;
  context.drawImage(background,-overscan,0,480+overscan*2,320+overscan);
  const wash=context.createLinearGradient(0,0,0,320);
  wash.addColorStop(0,'rgba(5,27,44,.43)');
  wash.addColorStop(.48,phase==='modes'?'rgba(2,28,44,.68)':'rgba(4,28,40,.28)');
  wash.addColorStop(1,'rgba(3,22,41,.86)');
  context.fillStyle=wash;context.fillRect(0,0,480,320);
  for(const {x,y,width,alpha} of ripples){
   context.globalAlpha=alpha;
   context.fillStyle='#a9f2ce';
   context.fillRect(Math.round(x),y,Math.round(width),1);
   context.fillRect(Math.round(x+width*.42),y+2,Math.round(width*.43),1);
   context.fillStyle='#467bab';
   context.fillRect(Math.round(x-width*.22),y+4,Math.round(width*.74),1);
  }
  context.globalAlpha=1;
  context.strokeStyle='#102836';context.lineWidth=1.65;context.lineCap='round';
  for(const {x,y,flap} of birds){
   context.beginPath();context.moveTo(x-5,y-flap);context.quadraticCurveTo(x-3,y-flap-1,x,y);
   context.quadraticCurveTo(x+2,y-flap-1,x+5,y-flap);context.stroke();
  }
  context.strokeStyle='#0b2e32';context.lineWidth=2;
  for(const {x,height,bend} of reeds){
   context.beginPath();context.moveTo(x,320);context.quadraticCurveTo(x-bend*.22,320-height*.54,x+bend,320-height);context.stroke();
  }
  if(phase==='reveal'){
   context.fillStyle='rgba(3,14,27,'+(.92*(1-reveal))+')';context.fillRect(0,0,480,320);
  }else if(phase==='launch'){
   const y=140+lift*114;
   const light=context.createRadialGradient(240,y,0,240,y,252);
   light.addColorStop(0,'rgba(190,255,227,'+(.13*Math.sin(Math.PI*lift))+')');
   light.addColorStop(1,'rgba(5,22,37,'+(.36*lift)+')');
   context.fillStyle=light;context.fillRect(0,0,480,320);
   context.strokeStyle='rgba(151,233,235,'+(.46*(1-lift))+')';context.lineWidth=1.3;
   for(let i=0;i<3;i++){const rx=20+(129+i*34)*lift+i*12;
    context.beginPath();context.ellipse(240,y,rx,rx*.18,0,0,Math.PI*2);context.stroke();}
  }
  context.restore();
 }
 return Object.freeze({createClock,motion,paint});
})();
