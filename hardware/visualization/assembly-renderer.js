import * as T from 'three';
import {lightStudio,materialFor} from './studio.js';
import screenImage from './lcd.png';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';

const by=id=>document.getElementById(id);
const data=JSON.parse(by('geometry').textContent), checks=JSON.parse(by('checks').textContent);
const lookup=new Map(data.map(row=>[row.id,row])),meshes=new Map();
const stages=[
 ['Assembly sequence','Use the arrows to build the assembly one station at a time.'],
 ['1 · Prepare the housing','Install H8 and its keeper inside the housing before closing the device.'],
 ['2 · Fit reel and encoder','Install rotor, magnet, shims and knob. Seat and center the encoder; check the shaft through a full turn.'],
 ['3 · Fit the top power key','Place the cap, slide PCB1 into its rails, and install its crossbar and H6. Check open and pressed contacts.'],
 ['4 · Secure the floor components','Gauge the cell, dress the speaker, and bond the optional driver and motor. Check the pouch pressure and flange.'],
 ['5 · Connect and seat the controller','Check every conductor and polarity with the cell disconnected. Make the final monitored connection, then seat the controller without trapping a lead.'],
 ['6 · Close and test','Install the four H1 screws and bezel. Measure power-key travel, edge touch, full reel travel and USB engagement.'],
 ['7 · Fit the rod accessory','Insert the keyed handle from the bottom into the hard stop. Secure its captive M3 screw to the trapped nut.']
];
let mode='exploded',station=0,selected=null,isolation=null,axis=56,renderer,cam,orbit,plane;
let studio,lcdFace;
const scene=new T.Scene(),host=by('stage');
const gaze={assembled:[135,72,185],exploded:[150,50,117],interior:[24,-64,198],wiring:[-48,75,-198],grip:[80,-60,-170]};
gaze.usb=[-180,16,26];gaze.speaker=[-67,-95,90];
const nameFor={speaker:'Mini oval speaker',usb:'USB-C and status lights',assembled:'Assembled product',exploded:'Exploded assembly',interior:'Internal assembly',wiring:'Wire routing',grip:'Slide-lock interface'};
if(checks.variants){
 gaze.battery=[32,-76,185];nameFor.battery='Battery bay';
 stages[3][1]='Use the west-side key keeper with the original top-left cap and carrier.';
 stages[4][1]='Install the inert gauge from above, dress both leads outward into the return tunnel, then fit the lift-out bridge and seat the PH adapter.';
}
const borderClass=new Set(['Housing','Bezel','A1-touch','A1-backing','A1-carrier']);
function options(r){
 if(r.productEligible===false && !by('allowances').checked)return false;
 if(r.batteryVariant)return (by('allowances').checked?by('cell').value:'alt')===r.batteryVariant;
 if(['alt','drawing'].includes(r.option))return by('cell').value===r.option;
 if(['pack0','pack1'].includes(r.id)&&by('cell').value!=='catalog')return false;
 if(r.id==='Cell')return by('cell').value==='catalog';
 if(r.option==='haptic')return by('haptic').checked;
 if(r.option==='rod')return by('rod').checked;
 if(r.option==='usb')return by('usb').checked;
 return true;
}
function allowed(r,skipIsolation=false){
 if(!options(r))return false;
 if(!skipIsolation&&isolation)return isolation.id?r.id===isolation.id:r.group===isolation.group;
 if(station)return r.stage<=station;
 if(mode==='speaker')return r.ref==='SP1' && r.productEligible!==false;
 if(mode==='battery')return r.id==='Housing'||r.id==='bridge'||r.id.startsWith('tieS')||r.id==='Retainer'||r.ref==='B1'||['ph','packplug','batt0','batt1','shrink0','shrink1','j7plug','A1-J7'].includes(r.id);
 if(mode==='interior')return r.ref!=='A1'&&r.id!=='Bezel'&&r.id!=='Removable rod grip'&&r.option!=='rod';
 if(mode==='wiring')return r.group==='Wiring'||['A1-J7','A1-J8','A1-J9','A1-k3','A2-pcb','Speaker','Cell','cellAlt','cellDrawing','drvBoard','motor','Key PCB'].includes(r.id);
 if(mode==='grip')return r.group==='Rod handle'||r.id==='Housing';
 return true;
}
const portTab=document.createElement('button');portTab.dataset.view='usb';portTab.textContent='USB-C port';
 const speakerTab=document.createElement('button');speakerTab.dataset.view='speaker';speakerTab.textContent='Speaker';document.querySelector('.tabs').append(portTab,speakerTab);
 by('cell').value='alt';
 const source=document.createElement('a');source.id='modelSource';source.hidden=true;source.target='_blank';source.rel='noopener noreferrer';by('measure').after(source);
 const pending=document.createElement('label');pending.innerHTML='<input id="allowances" type="checkbox"> Show engineering allowances';by('scope').append(pending);
 const controls=document.createElement('fieldset');controls.id='portSignals';controls.hidden=true;
 controls.innerHTML='<legend>Status light test</legend><label><input id="railOn" type="checkbox" checked> System power</label> <label>USB supply <select id="usbSource"><option value="off">Unplugged</option><option value="idle">Connected, idle</option><option value="charging">Charging</option></select></label><p id="lightText" aria-live="polite"></p>';
 by('selected').parentElement.before(controls);
 function statusState(){
   const source=by('usbSource').value;
   return {power:by('railOn').checked,usb:source!=='off',charge:source==='charging'};
 }
 function lightReadout(){const s=statusState();by('lightText').textContent=[s.power&&'Red · system powered',s.charge&&'Green · charging',s.usb&&'Blue · USB present'].filter(Boolean).join(' / ')||'Off · no USB power';}
 by('railOn').onchange=by('usbSource').onchange=()=>{lightReadout();sync();};lightReadout();
 const groups=[...new Set(data.map(r=>r.group))];
for(const g of groups)by('group').add(new Option(g,g));
by('evidence').textContent='R0009 USB and speaker fit results are linked in the print kit. Select a part to see its source. Enable engineering allowances to inspect gauges and outstanding model positions.';
function partList(){
 const search=by('find').value.toLowerCase().trim(),group=by('group').value;
 const entries=data.filter(r=>(r.productEligible!==false||by('allowances').checked)&&(group==='All groups'||r.group===group)&&[r.id,r.name,r.ref,r.kind].join(' ').toLowerCase().includes(search));
 by('list').replaceChildren();
 for(const r of entries){
  const btn=document.createElement('button');btn.className='part';btn.dataset.id=r.id;btn.setAttribute('aria-pressed',String(r.id===selected));
  const dot=document.createElement('i');dot.style.setProperty('--sw',r.color);
  const label=document.createElement('span');label.textContent=r.name;const ref=document.createElement('small');ref.textContent=r.ref;
  btn.append(dot,label,ref);btn.onclick=()=>select(r.id,true);by('list').append(btn);
 }
 by('groupOnly').disabled=group==='All groups';by('listed').textContent=entries.length+' of '+data.length+' register entries · '+data.filter(r=>allowed(r)).length+' shown';
}
function select(id,fromRegister=false){
 const r=lookup.get(id);if(!r)return;
 if(fromRegister&&!allowed(r)){
  if(r.batteryVariant)by('cell').value=r.batteryVariant;
  if(r.id==='Cell'||['alt','drawing'].includes(r.option))by('cell').value=r.option||'catalog';
  if(r.option==='haptic')by('haptic').checked=true;if(r.option==='rod')by('rod').checked=true;if(r.option==='usb')by('usb').checked=true;
  isolation=null;station=0;mode='exploded';
 }
 selected=id;sync();
}
function panel(){
 const held=data.filter(r=>r.productEligible===false&&r.ref!=='USB1'&&!r.batteryVariant);
 by('cellResult').textContent=held.length?held.length+' reference entries outside the as-fitted view. Check the component register before ordering or closing the case.':'Check physical fit and the power and charge lights on the first article.';
 const r=lookup.get(selected);
 by('selected').textContent=r?r.name:nameFor[mode];
 by('ref').textContent=r?r.ref:'Rev '+(checks.revision||'F');
 by('basis').textContent=r?r.kind:(station?'Assembly sequence':'Mechanical review');
 by('details').textContent=r?r.note:({speaker:'Adafruit 3923. Rotate the assembly to inspect the diaphragm, basket, magnet, contact pads and factory lead exits.',usb:'Seat the plug at the end of the recessed surround. Use the light controls to check the three independent indicators.',battery:'View the open bay, outboard PH saddle, bridge and routed leads for the selected pack.',exploded:'Select a part in the model or register to inspect its BOM reference and geometry source.',assembled:'The right-side reel is folded. The rear shoe remains on the case when the handle is removed.',interior:'Display board removed to expose the components installed in the case.',wiring:'Connector bodies, switch leads, reel bus, battery, speaker and optional motor wiring in their seated reference poses.',grip:'The 35 mm rear dovetail locates the handle. The captive screw locks into the installed M3 nut.'})[mode];
 const anchor=by('modelSource');
 anchor.hidden=!r?.modelUrl; if(r?.modelUrl){anchor.href=r.modelUrl;anchor.textContent=(r.mpn?r.mpn+' · ':'')+'Source 3D model';}
 by('measure').textContent=r?['X','Y','Z'].map((a,i)=>a+' '+(r.bounds_mm[i*2+1]-r.bounds_mm[i*2]).toFixed(1)).join('  ·  ')+' mm':'';
 by('isolate').disabled=!r||!!isolation;by('clear').disabled=!isolation&&!selected;
 by('stepTitle').textContent=stages[station][0];by('stepNote').textContent=stages[station][1];by('prev').disabled=station===0;by('next').disabled=station===7;
 for(const b of document.querySelectorAll('[data-view]'))b.setAttribute('aria-pressed',String(b.dataset.view===mode));
 by('percent').textContent=axis+'%';by('sectionRange').disabled=!by('section').checked;
}
let frame=0;
function render(){if(!studio||frame)return;frame=requestAnimationFrame(()=>{frame=0;studio.render(by('section').checked||mode==='wiring');});}
function sync(){
 if(selected&&!allowed(lookup.get(selected)))selected=null;
 const fraction=axis/100;
 for(const r of data){
  const m=meshes.get(r.id);if(!m)continue;
  m.visible=allowed(r);m.position.set(r.delta[0]*fraction,r.delta[1]*fraction,r.delta[2]*fraction);
  const hot=r.id===selected,em=hot?'#70552b':station&&r.stage===station?'#171f16':'#000000';
  m.material.emissive.set(em);m.material.emissiveIntensity=hot?.25:.5;
  const state=statusState();
  const channel={statusPwrGuide:'power',statusChgGuide:'charge',statusUsbGuide:'usb'}[r.id];
  if(channel){
    const tone=channel==='power'?0xd93425:channel==='charge'?0x28bb51:0x346df5;
    m.material.color.setHex(state[channel]?tone:0x495148);
    m.material.emissive.setHex(state[channel]?tone:0x000000);m.material.emissiveIntensity=state[channel]?1.25:0;
  }
  const guide=mode==='wiring'&&r.group!=='Wiring';
  m.material.transparent=guide&&!hot;m.material.opacity=m.material.transparent?.29:1;m.material.depthWrite=!m.material.transparent;
  m.material.clippingPlanes=by('section').checked?[plane]:[];m.renderOrder=m.material.transparent?3:0;
 }
 if(lcdFace){
   const touch=meshes.get('A1-touch');
   lcdFace.visible=!!touch?.visible&&!isolation&&!by('section').checked&&by('railOn').checked&&mode!=='wiring';
   if(touch)lcdFace.position.set(touch.position.x,touch.position.y,28.52+touch.position.z);
 }
 if(plane)plane.constant=+by('sectionRange').value;panel();partList();render();
}
function fit(direction){
 if(mode==='usb' && direction && !isolation){
   const group=['A1-usb','usbSurround','statusPwrGuide','statusChgGuide','statusUsbGuide'].map(id=>meshes.get(id)).filter(Boolean);
   if(group.length){
     const target=new T.Box3();for(const m of group)target.expandByObject(m);
     const point=target.getCenter(new T.Vector3()),d=new T.Vector3(...direction).normalize();
     orbit.target.copy(point);cam.position.copy(point).addScaledVector(d,275);cam.lookAt(point);
     const ratio=host.clientWidth/Math.max(1,host.clientHeight),h=Math.max(21,27/ratio);
     cam.left=-h*ratio;cam.right=h*ratio;cam.top=h;cam.bottom=-h;cam.zoom=1;cam.updateProjectionMatrix();orbit.update();render();return;
   }
 }
 if(!orbit)return;
 const points=[];
 for(const r of data){
  const m=meshes.get(r.id);if(!m?.visible)continue;
  const b=r.bounds_mm,d=m.position;
  for(const x of [b[0],b[1]])for(const y of [b[2],b[3]])for(const z of [b[4],b[5]])points.push(new T.Vector3(x+d.x,y+d.y,z+d.z));
 }
 if(!points.length)return;
 const center=new T.Box3().setFromPoints(points).getCenter(new T.Vector3());
 const look=direction?new T.Vector3(...direction).normalize():cam.position.clone().sub(orbit.target).normalize();
 cam.position.copy(center).addScaledVector(look,365);orbit.target.copy(center);cam.lookAt(center);cam.updateMatrixWorld();
 const w=host.clientWidth,h=host.clientHeight,ratio=w/h;let hx=0,hy=0;
 for(const p of points){p.applyMatrix4(cam.matrixWorldInverse);hx=Math.max(hx,Math.abs(p.x));hy=Math.max(hy,Math.abs(p.y));}
 const half=Math.max(8,hy*1.09,hx*1.09/ratio);
 cam.left=-half*ratio;cam.right=half*ratio;cam.top=half;cam.bottom=-half;cam.zoom=1;cam.updateProjectionMatrix();orbit.update();render();
}
function setMode(value){mode=value;by('portSignals').hidden=mode!=='usb';selected=null;isolation=null;station=0;axis=value==='exploded'?56:0;by('explode').value=axis;sync();fit(gaze[mode]);}
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>setMode(b.dataset.view);
by('explode').oninput=()=>{axis=+by('explode').value;sync();fit();};
by('fit').onclick=()=>fit();by('front').onclick=()=>fit([0,0,1]);by('rear').onclick=()=>fit([0,0,-1]);
by('cell').disabled=true;
for(const id of ['haptic','rod','usb','cell','allowances'])by(id).onchange=()=>{by('cell').disabled=!by('allowances').checked;if(by('cell').disabled)by('cell').value='alt';isolation=null;sync();fit();};
for(const id of ['section','sectionRange'])by(id).oninput=sync;
by('find').oninput=by('group').onchange=partList;
by('isolate').onclick=()=>{if(!selected)return;isolation={id:selected};sync();fit();};
by('groupOnly').onclick=()=>{isolation={group:by('group').value};selected=null;sync();fit();};
by('clear').onclick=()=>{isolation=null;selected=null;sync();fit();};
for(const [id,dir] of [['prev',-1],['next',1]])by(id).onclick=()=>{
 station=Math.max(0,Math.min(7,station+dir));mode='assembled';axis=0;by('explode').value=0;selected=null;isolation=null;
 sync();fit(station===7?gaze.grip:station<=2?gaze.assembled:gaze.interior);
};
async function unpack(encoded,type){
 const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));return new type(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate'))).arrayBuffer());
}
async function boot(){
 sync();
 renderer=new T.WebGLRenderer({antialias:true,alpha:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.setClearColor(0x000000,0);
 host.prepend(renderer.domElement);renderer.localClippingEnabled=true;
 cam=new T.OrthographicCamera(-70,70,55,-55,.1,1300);cam.up.set(0,1,0);cam.position.set(150,50,117);
 orbit=new OrbitControls(cam,renderer.domElement);orbit.addEventListener('change',render);orbit.minZoom=.25;orbit.maxZoom=9;
 plane=new T.Plane(new T.Vector3(-1,0,0),8);
 studio=lightStudio(renderer,scene,cam);document.documentElement.dataset.effects=studio.effects;
 for(const r of data){
  const [pv,ix]=await Promise.all([unpack(r.v,Int16Array),unpack(r.t,Uint32Array)]);
  const geom=new T.BufferGeometry();geom.setAttribute('position',new T.BufferAttribute(Float32Array.from(pv,v=>v*.01),3));geom.setIndex(new T.BufferAttribute(ix,1));geom.computeVertexNormals();
  const mat=materialFor(r);
  if(r.c){
    const colors=await unpack(r.c,Uint8Array),attr=new Float32Array(colors.length);
    const linear=Array.from({length:256},(_,x)=>{const s=x/255;return s<=.04045?s/12.92:((s+.055)/1.055)**2.4;});
    for(let i=0;i<colors.length;i++)attr[i]=linear[colors[i]];
    geom.setAttribute('color',new T.BufferAttribute(attr,3));mat.color.setHex(0xffffff);mat.vertexColors=true;
  }
  const mesh=new T.Mesh(geom,mat);mesh.name=r.id;meshes.set(r.id,mesh);scene.add(mesh);
 }
 const shot=new T.TextureLoader().load(screenImage,render);
 shot.colorSpace=T.SRGBColorSpace;shot.magFilter=T.NearestFilter;
 lcdFace=new T.Mesh(new T.PlaneGeometry(73.44,48.96),new T.MeshBasicMaterial({map:shot,toneMapped:false}));
 lcdFace.position.z=28.52;scene.add(lcdFace);
 let down;
 const surface=renderer.domElement;
 surface.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
 surface.addEventListener('pointerup',e=>{
  if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
  const box=surface.getBoundingClientRect(),ray=new T.Raycaster();
  ray.setFromCamera(new T.Vector2((e.clientX-box.left)*2/box.width-1,1-(e.clientY-box.top)*2/box.height),cam);
  const hit=ray.intersectObjects([...meshes.values()].filter(m=>m.visible),false).find(h=>(!by('section').checked||plane.distanceToPoint(h.point)>=0)&&!h.object.material.transparent);
  if(hit)select(hit.object.name);
 });
 const size=()=>{renderer.setSize(host.clientWidth,host.clientHeight,false);studio.resize(host.clientWidth,host.clientHeight);fit(mode==='usb'?gaze.usb:undefined);};
 new ResizeObserver(size).observe(host);size();setMode('assembled');
 const query=new URLSearchParams(location.hash.slice(1));if(gaze[query.get('view')])setMode(query.get('view'));
 if(lookup.has(query.get('part'))){select(query.get('part'),true);isolation={id:selected};sync();fit();}
 by('load').hidden=true;document.documentElement.dataset.ready='true';
}
boot().catch(err=>{by('load').textContent='3D drawing unavailable. The part register and fit results are below.';document.documentElement.dataset.ready='fallback';console.error(err);});
