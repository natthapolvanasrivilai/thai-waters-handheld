// Phone viewport fill does not depend on the browser Fullscreen API.
// Request native fullscreen only from the player's explicit fullscreen button.
(()=>{
 const root=document.documentElement,button=$('fullscreen'),mobileButton=$('mobileFullscreen');
 const motion=$('motionShortcut'),note=$('displayModeNote');
 // Suppress pointer menus in the game shell, not native editing or keyboard menus.
 document.querySelector('main').addEventListener('contextmenu',event=>{
  if(event.target.closest?.('input,textarea,select,[contenteditable]:not([contenteditable="false"])'))return;
  if(event.button===2||event.pointerType==='touch'||event.pointerType==='pen'||event.sourceCapabilities?.firesTouchEvents)event.preventDefault();
 });
 const coarse=matchMedia('(pointer: coarse)'),landscape=matchMedia('(orientation: landscape)');
 let manual=false,stayWindowed=false,declined=false,pending=false;
 const isPhone=()=>navigator.maxTouchPoints>0||coarse.matches;
 const nativeActive=()=>!!(document.fullscreenElement||document.webkitFullscreenElement);
 const request=root.requestFullscreen||root.webkitRequestFullscreen;
 const exit=document.exitFullscreen||document.webkitExitFullscreen;
 const allowed=()=>!!request&&(document.fullscreenEnabled??document.webkitFullscreenEnabled??true);
 const bilingual=(en,th)=>root.lang==='th'?th:en;
 function update(){
  const phone=isPhone(),native=nativeActive(),fill=native||manual||(!stayWindowed&&phone);
  const cssFallback=!allowed()||declined;
  root.toggleAttribute('data-mobile',phone);
  root.classList.toggle('immersive',fill);
  const label=native?L('Exit fullscreen'):!cssFallback?L('Enter fullscreen'):
   fill?bilingual('Exit screen fill','ออกจากโหมดเต็มพื้นที่'):bilingual('Fill screen','เต็มพื้นที่หน้าจอ');
  button.title=label;button.setAttribute('aria-label',label);
  for(const control of [button,mobileButton])control.setAttribute('aria-pressed',String(native||(cssFallback&&fill)));
  mobileButton.textContent=label;
  note.hidden=!(cssFallback&&(phone||manual||declined));
  note.textContent=bilingual('Browser bars may remain visible.','แถบเบราว์เซอร์อาจยังแสดงอยู่');
  requestAnimationFrame(()=>{fitFlat();if(!product.hidden)physicalView?.resize();});
 }
 async function toggle(){
  if(pending)return;
  if(nativeActive()){
   stayWindowed=true;manual=false;
   if(exit)try{await exit.call(document)}catch{}
  }else if(allowed()&&!declined){
   stayWindowed=false;manual=true;pending=true;
   try{await request.call(root)}catch{declined=true}
   finally{pending=false}
  }else{
   const fill=root.classList.contains('immersive');
   stayWindowed=fill;manual=!fill;
  }
  update();
 }
 button.onclick=mobileButton.onclick=toggle;
 motion.onclick=()=>{
  if(!menu.open)$('openMenu').click();
  if(menu.open){section('sensors');$('enableMotion').focus({preventScroll:true});}
 };
 let wasNative=nativeActive();
 function changed(){
  const active=nativeActive();
  if(wasNative&&!active){manual=false;stayWindowed=true;}
  wasNative=active;update();
 }
 document.addEventListener('fullscreenchange',changed);
 document.addEventListener('webkitfullscreenchange',changed);
 document.addEventListener('game-language',update);
 for(const query of [coarse,landscape]){
  if(query.addEventListener)query.addEventListener('change',update);
  else query.addListener(update);
 }
 update();
})();
