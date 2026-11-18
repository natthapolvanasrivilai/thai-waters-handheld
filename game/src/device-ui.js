let wheelInputAngle=0,wheelInputTime=0,wheelSampleTime=0;
function startPointerWheel(a){
 if(!g)return;wheelInputAngle=a;wheelInputTime=performance.now();wheelSampleTime=0;g.dialReset();g.dialSample(as5600(a),0);
}
function samplePointerWheel(a){
 const now=performance.now(),dt=Math.max(8,Math.min(500,Math.round(now-wheelInputTime)));
 const diff=Math.atan2(Math.sin(a-wheelInputAngle),Math.cos(a-wheelInputAngle)),steps=Math.ceil(dt/40);
 let movement=0;
 for(let i=1;i<=steps;i++)movement+=g.dialSample(as5600(wheelInputAngle+diff*i/steps),wheelSampleTime+Math.round(dt*i/steps));
 wheelSampleTime+=dt;wheelInputTime=now;wheelInputAngle=a;return movement;
}
const product=$('product'),flat=$('flatStage'),vm=$('viewMode'),foldButton=$('foldButton');
let physicalView=null,wantsDevice=true;
function setPower(on){
 if(!g)return;
 powered=on;release();gestureCast=gestureLift=false;g.resetGesture();prev=performance.now();
 for(const id of ['act','dial','openMenu','catchBook'])$(id).disabled=!on;
 $('simPower').textContent=on?'Power off':'Power on';
 $('powerPin').setAttribute('aria-label','Turn simulator power '+(on?'off':'on')+' at the lower-edge PWR switch');
 if(on){lastLabel='';draw();unlock();}
 else{
  save();audio?.suspend().catch(()=>{});ctx.fillStyle='#0e1715';ctx.fillRect(0,0,480,320);
  $('message').textContent='Power off';$('sub').textContent='Use PWR to wake the simulator.';
  for(const id of ['metrics','origin'])$(id).textContent='';$('catchBook').hidden=true;$('tension').hidden=true;
 }
}
$('simPower').onclick=$('powerPin').onclick=()=>setPower(!powered);
function showDevice(wanted){
 wantsDevice=wanted;const on=!!physicalView&&wanted;product.hidden=!on;flat.hidden=on;foldButton.hidden=!on;
 vm.textContent=on?'Screen only':'Device view';vm.setAttribute('aria-pressed',String(on));
 $('viewHint').textContent=on?'Turn the amber grip clockwise, looking at the right side, to reel in.':'Drag the knob or hold R to reel.';
 if(on)physicalView.resize();
}
vm.onclick=()=>physicalView ? showDevice(!wantsDevice) : loadDevice();
foldButton.onclick=()=>{const open=physicalView.fold();foldButton.textContent=open?'Fold reel':'Open reel';$('viewHint').textContent=open?'Turn the amber grip clockwise, looking at the right side, to reel in.':'Reel stowed. Open it to wind with the grip.';};
function paintLCD(c){
 c.imageSmoothingEnabled=false;c.drawImage(canvas,0,0);if(!powered)return;
 c.fillStyle='#1b332c';c.fillRect(0,0,480,24);
 c.fillStyle='#f6f0d6';c.font='bold 13px monospace';c.fillText(atlas.locations[placeId].name,9,18,189);
 c.fillStyle='#c6d4bc';c.font='12px monospace';c.fillText(times[currentSlot]+' '+$('song').textContent.split(' · ').pop(),204,18,122);
 batteryBadge(c,334,2);c.fillStyle='#ffc68c';c.fillText('MENU',436,18);

}
function loadDevice(){
vm.disabled=true;
makeThaiHandheld(product,JSON.parse($('deviceParts').textContent),{
 wheel:()=>dialAngle*Math.PI/180,paint:paintLCD,
 screen:(x,y)=>{if(!powered)return;if(g?.state()===5&&x>=.8625&&y>=.125&&y<=.254)openCatchRecord();else if(x>.82&&y<.125)$('openMenu').click();else if(!menu.open)tap();},
 beginWheel:a=>{if(!powered)return;unlock();if(!g)return;startPointerWheel(a);},
 power:()=>setPower(!powered),
 wind:(a,d)=>{if(!powered||!g||menu.open)return;dialAngle+=d*180/Math.PI;turns+=samplePointerWheel(a);}
}).then(v=>{physicalView=v;vm.disabled=false;showDevice(true);document.documentElement.dataset.device='ready';}).catch(()=>{showDevice(false);vm.hidden=true;$('viewHint').textContent='Screen mode · 3D rendering is unavailable in this browser.';document.documentElement.dataset.device='fallback';});
}
if(matchMedia('(pointer: coarse) and (max-width: 1000px)').matches){
  showDevice(false);vm.disabled=false;document.documentElement.dataset.device='deferred';
}else loadDevice();


