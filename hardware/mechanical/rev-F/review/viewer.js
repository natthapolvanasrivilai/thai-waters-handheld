import * as T from 'three';
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
const scene=new T.Scene(),host=by('stage');
const gaze={assembled:[135,72,185],exploded:[150,50,117],interior:[120,85,-198],wiring:[-48,75,-198],grip:[80,-60,-170]};
const nameFor={assembled:'Assembled product',exploded:'Exploded assembly',interior:'Internal assembly',wiring:'Wire routing',grip:'Slide-lock interface'};
if(checks.revision==='G'){
 gaze.battery=[32,-76,185];nameFor.battery='Battery bay';
 stages[3][1]='Use the west-side key keeper with the original top-left cap and carrier.';
 stages[4][1]='Install the inert gauge from above, dress both leads outward into the return tunnel, then fit the lift-out bridge and seat the PH adapter.';
}
const borderClass=new Set(['Housing','Bezel','A1-touch','A1-backing','A1-carrier']);
function options(r){
 if(r.batteryVariant)return by('cell').value===r.batteryVariant;
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
 if(mode==='battery')return r.id==='Housing'||r.id==='bridge'||r.id.startsWith('tieS')||r.id==='Retainer'||r.ref==='B1'||['ph','packplug','batt0','batt1','shrink0','shrink1','j7plug','A1-J7'].includes(r.id);
 if(mode==='interior')return !borderClass.has(r.id)&&r.id!=='Removable rod grip'&&r.option!=='rod';
 if(mode==='wiring')return r.group==='Wiring'||['A1-J7','A1-J8','A1-J9','A1-k3','A2-pcb','Speaker','Cell','cellAlt','cellDrawing','drvBoard','motor','Key PCB'].includes(r.id);
 if(mode==='grip')return r.group==='Rod handle'||r.id==='Housing';
 return true;
}
const groups=[...new Set(data.map(r=>r.group))];
for(const g of groups)by('group').add(new Option(g,g));
by('evidence').textContent=checks.pair_tests+' dressed-part pairs checked. '+checks.intersections.filter(x=>x.status==='resolve').length+' unresolved nominal pairs at the '+checks.threshold_mm3+' mm³ threshold. Mating contacts are identified in the measurement ledger.';
const cellHit=checks.cell_tests?.[0].intersections.find(h=>h.part==='Housing');
if(cellHit)by('cellResult').textContent='Supplier cell CAD overlaps the centered housing by '+cellHit.mm3+' mm³. Measure the incoming pack and protective cap before approving the pocket.';
function partList(){
 const search=by('find').value.toLowerCase().trim(),group=by('group').value;
 const entries=data.filter(r=>(group==='All groups'||r.group===group)&&[r.id,r.name,r.ref,r.kind].join(' ').toLowerCase().includes(search));
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
 if(checks.revision==='G'){
  const v=by('cell').value,caseData=checks.variants[v];
  by('cellResult').textContent=caseData.pair_tests+' seated pairs checked for this pack. '+caseData.intersections.filter(x=>x.status==='resolve').length+' unresolved. Open-shell insertion overlap: 0 mm³. Gauge on the print before installing a cell.';
 }
 const r=lookup.get(selected);
 by('selected').textContent=r?r.name:nameFor[mode];
 by('ref').textContent=r?r.ref:'Rev '+(checks.revision||'F');
 by('basis').textContent=r?r.kind:(station?'Assembly sequence':'Mechanical review');
 by('details').textContent=r?r.note:({battery:'View the open bay, outboard PH saddle, bridge and routed leads for the selected pack.',exploded:'Select a part in the model or register to inspect its BOM reference and geometry source.',assembled:'The right-side reel is folded. The rear shoe remains on the case when the handle is removed.',interior:'Shell, glass and PCB substrate hidden to expose the mounted electronics.',wiring:'Connector bodies, switch leads, reel bus, battery, speaker and optional motor wiring in their seated reference poses.',grip:'The 35 mm rear dovetail locates the handle. The captive screw locks into the installed M3 nut.'})[mode];
 by('measure').textContent=r?['X','Y','Z'].map((a,i)=>a+' '+(r.bounds_mm[i*2+1]-r.bounds_mm[i*2]).toFixed(1)).join('  ·  ')+' mm':'';
 by('isolate').disabled=!r||!!isolation;by('clear').disabled=!isolation&&!selected;
 by('stepTitle').textContent=stages[station][0];by('stepNote').textContent=stages[station][1];by('prev').disabled=station===0;by('next').disabled=station===7;
 for(const b of document.querySelectorAll('[data-view]'))b.setAttribute('aria-pressed',String(b.dataset.view===mode));
 by('percent').textContent=axis+'%';by('sectionRange').disabled=!by('section').checked;
}
let frame=0;
function render(){if(!renderer||frame)return;frame=requestAnimationFrame(()=>{frame=0;renderer.render(scene,cam);});}
function sync(){
 if(selected&&!allowed(lookup.get(selected)))selected=null;
 const fraction=axis/100;
 for(const r of data){
  const m=meshes.get(r.id);if(!m)continue;
  m.visible=allowed(r);m.position.set(r.delta[0]*fraction,r.delta[1]*fraction,r.delta[2]*fraction);
  const hot=r.id===selected,em=hot?'#70552b':station&&r.stage===station?'#171f16':'#000000';
  m.material.emissive.set(em);m.material.emissiveIntensity=hot?.65:.7;
  const guide=mode==='wiring'&&r.group!=='Wiring';
  m.material.transparent=guide&&!hot;m.material.opacity=m.material.transparent?.29:1;m.material.depthWrite=!m.material.transparent;
  m.material.clippingPlanes=by('section').checked?[plane]:[];m.renderOrder=m.material.transparent?3:0;
 }
 if(plane)plane.constant=+by('sectionRange').value;panel();partList();render();
}
function fit(direction){
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
function setMode(value){mode=value;selected=null;isolation=null;station=0;axis=value==='exploded'?56:0;by('explode').value=axis;sync();fit(gaze[mode]);}
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>setMode(b.dataset.view);
by('explode').oninput=()=>{axis=+by('explode').value;sync();fit();};
by('fit').onclick=()=>fit();by('front').onclick=()=>fit([0,0,1]);by('rear').onclick=()=>fit([0,0,-1]);
for(const id of ['haptic','rod','usb','cell'])by(id).onchange=()=>{isolation=null;sync();fit();};
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
 scene.add(new T.HemisphereLight(0xfff7e8,0xacbba5,1.65));
 for(const [position,intensity] of [[[70,130,200],2.6],[[-150,-60,-80],1.7]]){
  const light=new T.DirectionalLight(0xfffaea,intensity);light.position.set(...position);scene.add(light);
 }
 for(const r of data){
  const [pv,ix]=await Promise.all([unpack(r.v,Int16Array),unpack(r.t,Uint32Array)]);
  const geom=new T.BufferGeometry();geom.setAttribute('position',new T.BufferAttribute(Float32Array.from(pv,v=>v*.01),3));geom.setIndex(new T.BufferAttribute(ix,1));geom.computeVertexNormals();
  const metal=/screw|washer|magnet|nut|USB-C|contacts/i.test(r.name);
  const mat=new T.MeshStandardMaterial({color:r.color,roughness:metal?.4:.71,metalness:metal?.25:.03,side:T.DoubleSide});
  const mesh=new T.Mesh(geom,mat);mesh.name=r.id;meshes.set(r.id,mesh);scene.add(mesh);
 }
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
 const size=()=>{renderer.setSize(host.clientWidth,host.clientHeight,false);fit();};
 new ResizeObserver(size).observe(host);size();setMode(checks.revision==='G'?'battery':'exploded');
 const query=new URLSearchParams(location.hash.slice(1));if(gaze[query.get('view')])setMode(query.get('view'));
 if(lookup.has(query.get('part'))){select(query.get('part'),true);isolation={id:selected};sync();fit();}
 by('load').hidden=true;document.documentElement.dataset.ready='true';
}
boot().catch(err=>{by('load').textContent='3D drawing unavailable. The part register and fit results are below.';document.documentElement.dataset.ready='fallback';console.error(err);});
