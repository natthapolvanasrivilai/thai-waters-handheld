// The game fills the available safe area even where native fullscreen isn't available.
(()=>{
 const root=document.documentElement,button=$('fullscreen'),mobileButton=$('mobileFullscreen');
 const motion=$('motionShortcut'),note=$('displayModeNote'),help=$('displayHelp');
 const coarse=matchMedia('(pointer: coarse)'),landscape=matchMedia('(orientation: landscape)');
 const standalone=matchMedia('(display-mode: standalone)');
 const edits='input,textarea,select,option,a[href],[contenteditable]:not([contenteditable="false"]),#displayHelp';
 const shop=document.querySelector('main');
 let manual=false,stayWindowed=false,declined=false,pending=false,backFocus=null;
 const isPhone=()=>navigator.maxTouchPoints>0||coarse.matches;
 const isIOS=()=>/iPhone|iPad|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
 const isStandalone=()=>standalone.matches||navigator.standalone===true;
 const nativeActive=()=>!!(document.fullscreenElement||document.webkitFullscreenElement);
 const request=()=>document.fullscreenEnabled===true&&typeof root.requestFullscreen==='function'
   ?root.requestFullscreen:document.webkitFullscreenEnabled===true&&typeof root.webkitRequestFullscreen==='function'
   ?root.webkitRequestFullscreen:null;
 const exit=()=>document.exitFullscreen||document.webkitExitFullscreen;
 const bilingual=(en,th)=>root.lang==='th'?th:en;
 const iOSHelp=()=>isIOS()&&!isStandalone()&&(!request()||declined);
 const updateLayout=()=>requestAnimationFrame(()=>{fitFlat();if(!product.hidden)physicalView?.resize();});
 // A physical reel gesture is handled by its own pointer target. Do not install a page-level
 // touchmove blocker: scrollable sheets, pinch gestures and editable input retain native handling.
 function guard(event){
  if(event.target.closest?.(edits))return;
  if(event.type==='selectstart'){
   if(root.classList.contains('immersive'))event.preventDefault();
  }else if(event.button===2||event.pointerType==='touch'||event.pointerType==='pen'||event.sourceCapabilities?.firesTouchEvents){
   event.preventDefault();
  }
 }
 shop.addEventListener('contextmenu',guard);
 shop.addEventListener('selectstart',guard);
 function update(){
  const phone=isPhone(),native=nativeActive(),home=isStandalone();
  const fill=native||manual||(!stayWindowed&&(phone||home));
  const canNative=!!request()&&!declined;
  const needsHelp=iOSHelp();
  root.toggleAttribute('data-mobile',phone);
  root.classList.toggle('immersive',fill);
  root.dataset.displayMode=native?'native':fill?(home?'standalone':'fit'):'window';
  const label=native?L('Exit fullscreen'):needsHelp?bilingual('Full-screen help','วิธีเปิดเต็มหน้าจอ'):
   canNative?L('Enter fullscreen'):fill?bilingual('Exit screen fill','ออกจากโหมดเต็มพื้นที่'):bilingual('Fill screen','เต็มพื้นที่หน้าจอ');
  button.title=label;button.setAttribute('aria-label',label);
  for(const control of [button,mobileButton]){
   if(needsHelp){control.setAttribute('aria-haspopup','dialog');control.setAttribute('aria-controls','displayHelp');control.removeAttribute('aria-pressed');}
   else{control.removeAttribute('aria-haspopup');control.removeAttribute('aria-controls');control.setAttribute('aria-pressed',String(native||(!canNative&&fill)));}
  }
  mobileButton.textContent=label;
  note.hidden=!(declined&&!isIOS()&&fill);
  if(!note.hidden){
   const text=bilingual('Screen fit is on. Browser bars may remain.','เปิดโหมดเต็มพื้นที่แล้ว แถบเบราว์เซอร์อาจยังแสดงอยู่');
   if(note.textContent!==text)note.textContent=text;
  }
  $('displayHelpTitle').textContent=bilingual('Play from your Home Screen','เล่นจากหน้าจอโฮม');
  $('displayHelpText').textContent=bilingual(
   'Safari can fill the game area but may keep its own bars. In Safari, tap Share → Add to Home Screen. If shown, turn on Open as Web App, then tap Add. Start the game from the new icon.',
   'Safari ขยายเกมได้เต็มพื้นที่ แต่แถบเบราว์เซอร์อาจยังแสดงอยู่ ใน Safari แตะ แชร์ → เพิ่มไปยังหน้าจอโฮม ถ้ามีตัวเลือก เปิดเป็นเว็บแอป ให้เปิดก่อนแตะ เพิ่ม จากนั้นแตะไอคอนเกมบนหน้าจอโฮม');
  $('displayHelpClose').textContent=bilingual('Back to game','กลับไปที่เกม');
  $('displayHelpWindow').textContent=fill?bilingual('Use windowed layout','ใช้แบบหน้าต่าง'):bilingual('Fill screen','เต็มพื้นที่หน้าจอ');
  updateLayout();
 }
 function toggleFit(){
  const fill=root.classList.contains('immersive');
  stayWindowed=fill;manual=!fill;
 }
 function openHelp(el){
  if(help.open)return;
  backFocus=el;
  help.showModal();
 }
 async function toggle(event){
  if(pending)return;
  const trigger=event.currentTarget;
  if(nativeActive()){
   stayWindowed=true;manual=false;
   const end=exit();
   if(end)try{await end.call(document)}catch{}
  }else if(iOSHelp()){
   openHelp(trigger);
  }else if(!declined&&request()&&event.isTrusted){
   stayWindowed=false;manual=true;pending=true;
   // Initiate from the click itself, before any async boundary.
   try{await request().call(root)}catch{declined=true}
   finally{pending=false}
   if(declined&&iOSHelp())openHelp(trigger);
  }else if(!request()||declined){
   toggleFit();
  }
  update();
 }
 button.onclick=mobileButton.onclick=toggle;
 $('displayHelpClose').onclick=()=>help.close();
 $('displayHelpWindow').onclick=()=>{toggleFit();update();help.close();};
 help.addEventListener('close',()=>{if(backFocus?.isConnected)backFocus.focus({preventScroll:true});backFocus=null;});
 help.addEventListener('keydown',e=>e.stopPropagation());
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
 for(const query of [coarse,landscape,standalone]){
  if(query.addEventListener)query.addEventListener('change',update);
  else query.addListener(update);
 }
 window.visualViewport?.addEventListener('resize',updateLayout,{passive:true});
 update();
})();
