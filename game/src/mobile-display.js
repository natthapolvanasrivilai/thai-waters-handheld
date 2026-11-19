// Phone landscape always fills the available viewport. Browser fullscreen
// additionally needs a user gesture on browsers that expose the API.
(()=>{
 const root=document.documentElement,button=$('fullscreen');
 const landscape=matchMedia('(orientation: landscape)');
 let autoEntered=false,manual=false,stayWindowed=false,declined=false,pending=false;
 const isPhone=()=>navigator.maxTouchPoints>0||matchMedia('(pointer: coarse)').matches;
 const nativeActive=()=>!!(document.fullscreenElement||document.webkitFullscreenElement);
 const request=root.requestFullscreen||root.webkitRequestFullscreen;
 const exit=document.exitFullscreen||document.webkitExitFullscreen;
 const allowed=()=>!!request && (document.fullscreenEnabled??document.webkitFullscreenEnabled??true);
 function update(){
  const fill=nativeActive()||manual||(!stayWindowed&&isPhone()&&landscape.matches);
  root.classList.toggle('immersive',fill);
  const leaving=nativeActive()||(fill&&(!allowed()||declined||manual));
  const label=leaving?'Exit fullscreen':'Enter fullscreen';
  button.title=label;button.setAttribute('aria-label',L(label));
  button.setAttribute('aria-pressed',String(fill));
  requestAnimationFrame(()=>{fitFlat();if(!product.hidden)physicalView?.resize();});
 }
 async function enterNative(){
  if(!allowed()||pending||nativeActive())return;
  pending=true;
  try{await request.call(root);}
  catch{declined=true;}
  finally{pending=false;update();}
 }
 button.onclick=async()=>{
  if(nativeActive() || (root.classList.contains('immersive') && (manual||!allowed()||declined))){
   stayWindowed=true;autoEntered=false;manual=false;
   if(nativeActive()&&exit){try{await exit.call(document);}catch{}}
  }else{
   stayWindowed=false;manual=true;declined=false;await enterNative();
  }
  update();
 };
 function rotated(){
  stayWindowed=false;declined=false;
  if(!landscape.matches&&autoEntered){
   autoEntered=false;if(nativeActive()&&exit)Promise.resolve(exit.call(document)).catch(()=>{});
  }
  update();
 }
 function automatic(e){
  if(!isPhone()||!landscape.matches||menu.open||stayWindowed||manual||declined||!allowed()||nativeActive())return;
  if(!e.target.closest('#flatStage,#product,#flatReel') || e.target.closest('#fullscreen,#openMenu,#powerPin'))return;
  autoEntered=true;enterNative();
 }
 document.addEventListener('pointerup',automatic);
 let wasNative=nativeActive();
 function changed(){
  const active=nativeActive();
  if(wasNative&&!active){manual=false;autoEntered=false;stayWindowed=true;}
  wasNative=active;update();
 }
 document.addEventListener('fullscreenchange',changed);
 document.addEventListener('webkitfullscreenchange',changed);
 if(landscape.addEventListener)landscape.addEventListener('change',rotated);
 else landscape.addListener(rotated);
 update();
})();
