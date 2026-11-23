let wheelInputAngle=0,wheelInputTime=0,wheelSampleTime=0;
function startPointerWheel(a){
 if(!g)return;wheelInputAngle=a;wheelInputTime=performance.now();wheelSampleTime=0;g.dialReset();g.dialSample(as5600(a),0);
}
function samplePointerWheel(a){
 const now=performance.now(),diff=Math.atan2(Math.sin(a-wheelInputAngle),Math.cos(a-wheelInputAngle));
 // Browsers can deliver several touch samples together. Reconstruct the
 // angular path below the AS5600 bench's physical spike-rejection speed.
 const dt=Math.max(8,Math.ceil(Math.abs(diff)*1000/(2*Math.PI*4.5)),Math.min(500,Math.round(now-wheelInputTime)));
 const steps=Math.ceil(dt/40);
 let movement=0;
 for(let i=1;i<=steps;i++)movement+=g.dialSample(as5600(wheelInputAngle+diff*i/steps),wheelSampleTime+Math.round(dt*i/steps));
 wheelSampleTime+=dt;wheelInputTime=now;wheelInputAngle=a;return movement;
}
const product=$('product'),flat=$('flatStage'),vm=$('viewMode'),foldButton=$('foldButton');
let physicalView=null,wantsDevice=false;
const lcdUI=$('lcdUI');
function lcdMatrix(a,b,c,d,x,y){
 lcdUI.style.transform='matrix('+[a,b,c,d,x,y].join(',')+')';
}
function fitFlat(){
 if(lcdUI.parentElement===flat&&canvas.clientWidth){
  lcdMatrix(canvas.clientWidth/480,0,0,canvas.clientHeight/320,canvas.offsetLeft,canvas.offsetTop);
 }
}
new ResizeObserver(fitFlat).observe(canvas);
function setPower(on){
 if(!g){toggleStartupPower();return;}
 const atBootHome=bootHome;
 if(!on&&menu.open)closeMenu(true);
 if(!on&&arrivalSince!==null)stopArrival();
 powered=on;lcdUI.hidden=!on;release();gestureCast=gestureLift=false;g.resetGesture();prev=performance.now();
 for(const id of ['act','dial','openMenu','catchContinue'])$(id).disabled=!on;
 setUi($('simPower'),on?'Power off':'Power on');
 $('powerPin').setAttribute('aria-label',L('Turn simulator power '+(on?'off':'on')+' at the top-left PWR key'));
 if(on){lastLabel='';openBootHome();draw();}
 else{
  if(!atBootHome)save();
  if(arcadeContext&&arcadeContext!==audio)arcadeContext.suspend().catch(()=>{});
  audio?.suspend().catch(()=>{});ctx.fillStyle='#0e1715';ctx.fillRect(0,0,480,320);
  setUi($('message'),'Power off');setUi($('sub'),'Use PWR to wake the simulator.');
  for(const id of ['metrics','origin'])setUi($(id),'');$('catchContinue').hidden=true;$('tension').hidden=true;
 }
}
$('simPower').onclick=$('powerPin').onclick=()=>setPower(!powered);
function showDevice(wanted){
 wantsDevice=wanted;const on=!!physicalView&&wanted;product.hidden=!on;flat.hidden=on;foldButton.hidden=!on;
 $('gripButton').hidden=!on;
 const surface=on?product:flat;
 if(lcdUI.parentElement!==surface)surface.append(lcdUI);
 document.documentElement.dataset.view=on?'device':'screen';
 setUi(vm,on?'Screen only':'Device view');vm.setAttribute('aria-pressed',String(on));
 setUi($('viewHint'),on?'Turn the amber grip clockwise, looking at the right side, to reel in.':'Drag the knob or hold R to reel.');
 if(on)physicalView.resize();else fitFlat();
}
vm.onclick=()=>physicalView ? showDevice(!wantsDevice) : loadDevice();
$('gripButton').onclick=()=>{const attached=physicalView.toggleGrip();setUi($('gripButton'),attached?'Remove rod grip':'Attach rod grip');$('gripButton').setAttribute('aria-pressed',String(attached));};
foldButton.onclick=()=>{const open=physicalView.fold();setUi(foldButton,open?'Fold reel':'Open reel');setUi($('viewHint'),open?'Turn the amber grip clockwise, looking at the right side, to reel in.':'Reel stowed. Open it to wind with the grip.');};
function paintLCD(c){
 c.imageSmoothingEnabled=false;c.drawImage(canvas,0,0);
}
function loadDevice(){
vm.disabled=true;
makeThaiHandheld(product,JSON.parse($('deviceParts').textContent),{
 wheel:()=>shownWheel*Math.PI/180,paint:paintLCD,
 lcdTransform:(...m)=>{if(lcdUI.parentElement===product)lcdMatrix(...m);},
 screen:(x,y)=>{if(!powered)return;if(arrivalSince!==null){stopArrival();return;}if(g?.state()===5)scenePress(x,y);else if(x>.82&&y<.125)$('openMenu').click();else if(!menu.open)scenePress(x,y);},
 beginWheel:a=>{if(!powered||bootHome||arrivalSince!==null)return;unlock();if(!g)return;startPointerWheel(a);},
 power:()=>setPower(!powered),
 wind:(a,d)=>{if(!powered||!g||menu.open||arrivalSince!==null)return;dialAngle+=d*180/Math.PI;turns+=samplePointerWheel(a);}
}).then(v=>{physicalView=v;vm.disabled=false;showDevice(true);document.documentElement.dataset.device='ready';}).catch(()=>{showDevice(false);vm.hidden=true;setUi($('viewHint'),'Screen mode · 3D rendering is unavailable in this browser.');document.documentElement.dataset.device='fallback';});
}
// Flat LCD is the readable default. Keep 3D available as an explicit opt-in.
showDevice(false);vm.disabled=false;document.documentElement.dataset.device='deferred';


