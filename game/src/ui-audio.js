const menuAudio=(()=>{
 const shapes={tap:[288,570,.031],menu:[432,440,.045],scroll:[192,780,.021]},levels=[0,.42,.68,1];
 const selector='#menu section:not([hidden]),#lcdPicker:not([hidden]) .choice-list';
 const keys=new Set(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End']);
 const excluded='#startSound,#testSound,[data-pulse],#testPhoneMotor';
 let cache=new Map(),context=null,lastScroll=-Infinity,intent=null,serial=0;
 const ready=()=>powered&&g&&!document.hidden&&levels[$('fx').selectedIndex]>0;
 function clip(ctx,kind){
  if(ctx!==context){context=ctx;cache=new Map();}
  if(cache.has(kind))return cache.get(kind);
  const [length,freq,peak]=shapes[kind],buf=ctx.createBuffer(1,length,16000),pcm=buf.getChannelData(0);
  let seed=31,low=0;
  for(let i=0;i<length;i++){
   seed=(Math.imul(seed,1664525)+1013904223)>>>0;
   low=.72*low+.28*(seed/2147483648-1);
   const x=i/(length-1),env=Math.min(1,i/18)*(1-x)**3;
   pcm[i]=peak*env*(.69*Math.sin(2*Math.PI*freq*i/16000)*Math.exp(-2*x)+.31*low);
  }
  cache.set(kind,buf);return buf;
 }
 function play(kind,activate=false){
  if(!ready())return;
  const token=++serial,started=performance.now();
  function fire(){
   if(token!==serial||!ready()||audio?.state!=='running'||performance.now()-started>220)return;
   const source=audio.createBufferSource(),gain=audio.createGain();
   source.buffer=clip(audio,kind);gain.gain.value=levels[$('fx').selectedIndex];
   source.connect(gain);gain.connect(audio.destination);
   source.onended=()=>{source.disconnect();gain.disconnect();};source.start();
  }
  if(audio?.state==='running')fire();
  else if(activate){unlock();void resumeAudio?.then(fire);}
 }
 function target(e){return e.target instanceof Element?e.target:null;}
 function area(e){return target(e)?.closest(selector);}
 function arm(el){intent={el,top:el.scrollTop,until:performance.now()+240};}
 function clear(){intent=null;}
 document.addEventListener('click',e=>{
  if(!e.isTrusted)return;
  clear();
  const el=target(e),button=el?.closest('button,summary');
  if(el?.closest(excluded)||button?.disabled||button?.closest('[inert],[aria-disabled="true"]'))return;
  if(button?.matches('#act')){if(!menu.open)play('tap',true);}
  else if(menu.open&&button?.matches('#sheetPrev,#sheetNext,#bookPrev,#bookNext'))play('scroll',true);
  else if(button?.matches('#openMenu,#rigHud,#catchContinue')||button&&menu.open&&menu.contains(button))play('menu',true);
 },true);
 document.addEventListener('change',e=>{
  if(!e.isTrusted)return;
  clear();
  if(menu.open&&target(e)?.matches('#menu select:not(:disabled),#menu input[type="checkbox"]:not(:disabled)'))play('menu',true);
 },true);
 document.addEventListener('wheel',e=>{const el=area(e);if(e.isTrusted&&el&&e.deltaY&&menu.open)arm(el);},{capture:true,passive:true});
 document.addEventListener('touchmove',e=>{const el=area(e);if(e.isTrusted&&el&&e.touches.length===1&&menu.open)arm(el);},{capture:true,passive:true});
 document.addEventListener('touchcancel',clear,true);
 document.addEventListener('keydown',e=>{
  const el=area(e);
  if(e.isTrusted&&el&&menu.open&&keys.has(e.key)&&!target(e)?.closest('select,input,textarea,[contenteditable]'))arm(el);
 },true);
 document.addEventListener('scroll',e=>{
  const el=target(e),now=performance.now();
  if(!e.isTrusted||!menu.open||!el||el!==intent?.el||!el.matches(selector)||now>intent.until)return;
  if(Math.abs(el.scrollTop-intent.top)<1)return;
  clear();
  if(now-lastScroll<110||!ready()||audio?.state!=='running')return;
  lastScroll=now;play('scroll');
 },true);
 document.addEventListener('visibilitychange',()=>{if(document.hidden){clear();++serial;}});
 return {tap:()=>play('tap',true)};
})();
