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
function showDevice(wanted){
 wantsDevice=wanted;const on=!!physicalView&&wanted;product.hidden=!on;flat.hidden=on;foldButton.hidden=!on;
 vm.textContent=on?'Screen only':'Device view';vm.setAttribute('aria-pressed',String(on));
 $('viewHint').textContent=on?'Drag the amber grip around the right-side axle to reel.':'Drag the knob or hold R to reel.';
 if(on)physicalView.resize();
}
vm.onclick=()=>showDevice(!wantsDevice);
foldButton.onclick=()=>{const open=physicalView.fold();foldButton.textContent=open?'Fold reel':'Open reel';$('viewHint').textContent=open?'Drag the amber grip around the right-side axle to reel.':'Reel stowed. Open it to wind with the grip.';};
function paintLCD(c){
 c.imageSmoothingEnabled=false;c.drawImage(canvas,0,0);
 c.fillStyle='#1b332c';c.fillRect(0,0,480,28);c.fillRect(0,258,480,62);
 c.fillStyle='#f6f0d6';c.font='bold 13px monospace';c.fillText(atlas.locations[placeId].name,10,19,250);
 c.fillStyle='#c6d4bc';c.font='12px monospace';c.fillText(times[currentSlot]+' '+$('song').textContent.split(' · ').pop(),268,18,140);
 c.fillStyle='#ffc68c';c.fillText('MENU',436,18);
 c.fillStyle='#fff1ca';c.font='bold 15px monospace';c.fillText($('message').textContent,11,280,412);
 c.fillStyle='#c7d5ba';c.font='11px monospace';c.fillText($('metrics').textContent||$('sub').textContent,11,299,450);
 if(g?.state()===5){c.font='9px monospace';c.fillText($('origin').textContent,11,313,458);}
 if(g?.state()===4){c.fillStyle='#476252';c.fillRect(12,308,200,4);c.fillStyle='#efb078';c.fillRect(12,308,200*g.tension(),4);}
}
vm.disabled=true;
makeThaiHandheld(product,JSON.parse($('deviceParts').textContent),{
 wheel:()=>dialAngle*Math.PI/180,paint:paintLCD,
 screen:(x,y)=>{if(x>.82&&y<.16)$('openMenu').click();else if(!menu.open)tap();},
 beginWheel:a=>{unlock();if(!g)return;startPointerWheel(a);},
 wind:(a,d)=>{if(!g||menu.open)return;dialAngle+=d*180/Math.PI;turns+=samplePointerWheel(a);}
}).then(v=>{physicalView=v;vm.disabled=false;showDevice(true);document.documentElement.dataset.device='ready';}).catch(()=>{showDevice(false);vm.hidden=true;$('viewHint').textContent='Screen mode · 3D rendering is unavailable in this browser.';document.documentElement.dataset.device='fallback';});


