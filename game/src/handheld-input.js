/* The handheld pairs with the operating system as a BLE HID keyboard. A fresh
   heartbeat arms the opted-in receiver. Pitch reports describe posture only.
   Cast and hook are separate, already-debounced physical gesture edges. */
const handheldInput=(()=>{
 const settings=document.querySelector('[data-section="sensors"]');
 const panel=document.createElement('fieldset'),heading=document.createElement('legend');
 const label=document.createElement('label'),toggle=document.createElement('input'),labelText=document.createElement('span');
 const help=document.createElement('p'),status=document.createElement('p');
 toggle.type='checkbox';toggle.id='handheldEnable';help.id='handheldHelp';status.id='handheldStatus';
 toggle.setAttribute('aria-describedby',help.id);status.setAttribute('role','status');
 label.append(toggle,' ',labelText);panel.append(heading,label,help,status);settings.append(panel);
 const preference='thai-waters-handheld-hid-v1';
 try{toggle.checked=localStorage.getItem(preference)==='on';}catch{}
 const detents={KeyJ:1,KeyU:2,KeyI:4,KeyO:8,KeyK:-1,KeyN:-2,KeyM:-4,KeyP:-8};
 let lastBeat=-Infinity,timer=0,focused=!document.hidden,high=false,usingPose=false,wheelPosition=0;
 const fresh=()=>toggle.checked && focused && !document.hidden && performance.now()-lastBeat<3000;
 const tr=(en,th)=>language==='th'?th:en;
 function render(){
  heading.textContent=tr('Handheld controller','ใช้เครื่องตกปลาเป็นจอย');
  labelText.textContent=tr('Use paired rod','ใช้คันเบ็ดที่จับคู่ไว้');
  help.textContent=tr('Pair Thai Waters Rod in your device’s Bluetooth settings. Enable the rod here, then resume fishing. While the rod is sending input, switch it off to type normally in menus.','จับคู่ Thai Waters Rod ในการตั้งค่าบลูทูธของอุปกรณ์ เปิดใช้คันเบ็ดที่นี่แล้วกลับไปตกปลา หากต้องการพิมพ์ในเมนู ให้ปิดโหมดจอยที่คันเบ็ดก่อน');
  status.textContent=!toggle.checked?tr('Rod input off','ปิดการรับสัญญาณจากคันเบ็ด'):fresh()?tr('Receiving rod input','กำลังรับสัญญาณจากคันเบ็ด'):tr('Waiting for rod signal','กำลังรอสัญญาณจากคันเบ็ด');
 }
 function neutral(){
  if(usingPose){rodAngle=0;g?.handheldRodHigh(0);}
  high=false;usingPose=false;wheelPosition=0;
 }
 function lost(){
  clearTimeout(timer);lastBeat=-Infinity;neutral();render();
 }
 function beat(){
  const wasLive=fresh();
  lastBeat=performance.now();clearTimeout(timer);timer=setTimeout(lost,3000);
  if(!wasLive)render();
 }
 function receive(e){
  if(!toggle.checked || !focused || document.hidden || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey || e.isComposing || e.keyCode===229)return;
  const code=e.code,pitch=/^Digit[1-9]$/.test(code);
  if(code!=='KeyV' && code!=='KeyC' && code!=='KeyH' && !pitch && !Object.hasOwn(detents,code))return;
  if(code!=='KeyV' && !fresh())return;
  // OS keyboard reports also reach focused search fields. Suppress the rod
  // packet before browser text input or game shortcuts can claim it.
  e.preventDefault();e.stopImmediatePropagation();
  if(e.repeat)return;
  if(code==='KeyV'){beat();return;}
  if(!g || !powered || menu.open || arrivalSince!==null || e.target?.closest?.('input,textarea,select,[contenteditable="true"]'))return;
  if(pitch){
   const level=Number(code.slice(-1))-1;
   rodAngle=28*level/8;usingPose=true;
   if(level/8>=.70)high=true;
   else if(level/8<.27)high=false;
   g.handheldRodHigh(high?1:0);
  }else if(code==='KeyC'){
   unlock();gestureCast=true;
  }else if(code==='KeyH'){
   unlock();gestureLift=true;
  }else{
   unlock();
   const angle=wheelPosition*Math.PI/12;
   const delta=detents[code]*Math.PI/12;
   startPointerWheel(angle);
   turns+=samplePointerWheel(angle+delta);
   dialAngle+=detents[code]*15;
   wheelPosition=(wheelPosition+detents[code]+24)%24;
  }
 }
 toggle.onchange=()=>{
  if(!sessionOnly)try{localStorage.setItem(preference,toggle.checked?'on':'off');}catch{}
  lost();
 };
 window.addEventListener('keydown',receive,true);
 window.addEventListener('blur',()=>{focused=false;lost();});
 window.addEventListener('focus',()=>{focused=true;});
 document.addEventListener('visibilitychange',()=>{focused=!document.hidden;if(!focused)lost();});
 document.addEventListener('game-language',render);
 render();
 return {ownsRod:fresh,neutral};
})();
