import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {softwareRenderer} from './software.js';

const {scene: geometry,steps} = JSON.parse(document.getElementById('assemblyData').textContent);
const el = id => document.getElementById(id);
const stage=el('stage'), canvas=el('model');
const scene=new THREE.Scene(), camera=new THREE.OrthographicCamera(-60,60,42,-42,.1,1200);
camera.up.set(0,0,1);
let renderer;
try {
  renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power'});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.setClearColor(0x000000,0);
} catch {
  // A fresh canvas can obtain a 2D context even if a WebGL allocation failed.
  const replacement=canvas.cloneNode(false);
  canvas.replaceWith(replacement);
  renderer=softwareRenderer(replacement);
}
const surface=renderer.domElement,controls=new OrbitControls(camera,surface);
controls.minZoom=.25;controls.maxZoom=16;
controls.enableDamping=false;controls.rotateSpeed=.65;controls.zoomSpeed=.8;
scene.add(new THREE.HemisphereLight(0xfffbec,0x75887b,1.75));
for (const [position,intensity] of [[[40,-60,105],2.1],[[-80,28,50],1.05],[[20,25,-75],.9]]) {
  const lamp=new THREE.DirectionalLight(0xfff9e9,intensity);
  lamp.position.set(...position);scene.add(lamp);
}
const colors={housing:0x76978b,bezel:0x314a40,pkcell:0xb09d70,adafruit:0xb09d70,carrier:0x749283,floor:0x778a83,
  bridge:0x84968a,A1:0x536d67,KEY:0x47877e,cap:0x54665f,keeper:0x78958a};
const labels={A1:'A1 · Display',A2:'A2 · Reel sensor',A3:'A3 · Haptics',A4:'A4 · Integration',A5:'A5 · USB power',KEY:'Power switch',USB1:'USB indicator',USB2:'Lamp resistor',housing:'Housing',bezel:'Bezel',carrier:'R20 carrier',floor:'R20 floor sample',bridge:'Battery bridge',cap:'Power cap',keeper:'Switch retainer',pkcell:'PKCELL gauge',adafruit:'Adafruit gauge'};
function label(id){
  if(labels[id])return labels[id];
  const shim=/^(A[2-5])s(\d)$/.exec(id);
  return shim?shim[1]+(shim[1]==='A2'?' shim ':' spacer ')+shim[2]:id;
}
const vec=a=>new THREE.Vector3(...a), meshMap=new Map();
const shellParts=new Set(['housing','bezel']);
const warm=0xd98c39;
function bytes(s){return Uint8Array.from(atob(s),c=>c.charCodeAt(0));}
for(const [id,p] of Object.entries(geometry.parts)){
  const g=new THREE.BufferGeometry();
  const xyz=new Int32Array(bytes(p.v).buffer);
  g.setAttribute('position',new THREE.BufferAttribute(Float32Array.from(xyz,n=>n*geometry.scale),3));
  g.setIndex(new THREE.BufferAttribute(new Uint32Array(bytes(p.f).buffer),1));
  g.computeVertexNormals();g.computeBoundingBox();
  const color=colors[id]??(/s\d$/.test(id)?0x78a3b5:0x589181);
  const material=new THREE.MeshStandardMaterial({color,roughness:.83,metalness:.03,flatShading:true,side:THREE.DoubleSide});
  const mesh=new THREE.Mesh(g,material);
  mesh.userData={id,color,center:g.boundingBox.getCenter(new THREE.Vector3())};
  scene.add(mesh);meshMap.set(id,mesh);
}
let current=0,ghost=false,frameWidth=100,guides=[],scheduled=false;
const marked=new Set();
const selected=()=>steps[current];
const partId=id=>id==='pkcell'?el('pack').value:id;
const activeIds=()=>selected().active.map(partId);
const movedIds=()=> (selected().moving??selected().active).map(partId);
function render(){
  scheduled=false;
  renderer.render(scene,camera);
  const tag=el('tag'),id=activeIds()[0],mesh=meshMap.get(id);
  if(!mesh){tag.hidden=true;return;}
  const p=mesh.userData.center.clone().add(mesh.position).project(camera);
  tag.textContent=label(id)+(activeIds().length>1?' +'+(activeIds().length-1):'');
  tag.hidden=Math.abs(p.x)>1 || Math.abs(p.y)>1 || p.z < -1 || p.z>1;
  if(!tag.hidden){
    const x=(p.x+1)*stage.clientWidth/2,y=(1-p.y)*stage.clientHeight/2;
    // Keep the tiny USB boards visible beneath their labels.
    tag.style.transform='translate('+Math.max(3,Math.min(x+9,stage.clientWidth-tag.offsetWidth-3))+'px,'+Math.max(3,Math.min(y-tag.offsetHeight-9,stage.clientHeight-tag.offsetHeight-34))+'px)';
  }
}
function invalidate(){if(!scheduled){scheduled=true;requestAnimationFrame(render);}}
function resize(){
  const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h)return;
  renderer.setSize(w,h,false);
  // A step's nominal camera frame fits a 4:3 inspection window at any viewport aspect.
  const width=Math.max(frameWidth,frameWidth*.72*w/h);
  camera.left=-width/2;camera.right=width/2;camera.top=width*h/w/2;camera.bottom=-camera.top;
  camera.updateProjectionMatrix();invalidate();
}
function pose(target,eye,width){
  frameWidth=width;camera.zoom=1;controls.target.copy(target);
  camera.position.copy(target).add(eye.normalize().multiplyScalar(290));
  camera.lookAt(target);camera.updateProjectionMatrix();controls.update();resize();
}
function reset(){
  const s=selected();pose(vec(s.target),vec(s.eye),s.width);
}
function overview(){
  const bounds=new THREE.Box3();
  for(const m of meshMap.values()){
    if(m.visible)bounds.union(m.geometry.boundingBox.clone().translate(m.position));
  }
  const eye=camera.position.clone().sub(controls.target);
  pose(bounds.getCenter(new THREE.Vector3()),eye,Math.max(9,bounds.getSize(new THREE.Vector3()).length()*1.12));
}
function focus(){
  const bounds=new THREE.Box3();
  for (const id of activeIds()){
    const m=meshMap.get(id);bounds.union(m.geometry.boundingBox.clone().translate(m.position));
  }
  if(bounds.isEmpty())return;
  const eye=camera.position.clone().sub(controls.target);
  pose(bounds.getCenter(new THREE.Vector3()),eye,Math.max(9,bounds.getSize(new THREE.Vector3()).length()*1.28));
}
function setLook(){
  const s=selected(),visible=new Set(s.visible.map(partId)),active=new Set(activeIds());
  for (const [id,m] of meshMap){
    m.visible=visible.has(id);
    const translucent=ghost&&shellParts.has(id)&&!active.has(id);
    m.material.color.setHex(active.has(id)?warm:m.userData.color);
    m.material.transparent=translucent;m.material.opacity=translucent?.13:1;m.material.depthWrite=!translucent;
    m.renderOrder=translucent?2:0;
  }
  el('focus').disabled=active.size===0;
  stage.querySelector('.legend').hidden=active.size===0;
  el('ghost').setAttribute('aria-pressed',String(ghost));
  el('ghost').disabled=![...visible].some(id=>shellParts.has(id)&&!active.has(id));
  invalidate();
}
function removeGuides(){
  for(const line of guides){scene.remove(line);line.geometry.dispose();line.material.dispose();}
  guides=[];
}
function placement(){
  const s=selected(),t=Number(el('position').value)/100,moving=new Set(movedIds()),offset=vec(s.offset);
  const adjustable=offset.lengthSq()>0&&moving.size>0;
  for(const [id,m] of meshMap)m.position.copy(offset).multiplyScalar(moving.has(id)?t:0);
  removeGuides();
  if(t>.03&&adjustable){
    for(const id of activeIds().filter(id=>moving.has(id))){
      const m=meshMap.get(id),end=m.userData.center.clone().add(m.position),start=m.userData.center;
      const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([start,end]),new THREE.LineDashedMaterial({color:0x93642c,dashSize:.7,gapSize:.5,depthTest:false}));
      line.computeLineDistances();line.renderOrder=3;scene.add(line);guides.push(line);
    }
  }
  el('position').disabled=!adjustable;el('position').closest('.slideRow').hidden=!adjustable;
  el('positionText').textContent=t===0?'Seated':t===1?'Lifted clear':Math.round(offset.length()*t*10)/10+' mm offset';
  el('position').setAttribute('aria-valuetext',el('positionText').textContent);
  invalidate();
}
function step(index){
  current=Math.max(0,Math.min(index,steps.length-1));const s=selected();
  el('group').textContent=s.group;el('title').textContent=s.title;el('counter').textContent='Step '+(current+1)+' of '+steps.length;
  for(const name of ['instruction','facing','check'])el(name).textContent=s[name];
  el('prev').disabled=current===0;el('next').disabled=current===steps.length-1;
  el('steps').value=String(current);el('packs').hidden=!s.visible.includes('pkcell');
  el('checks').hidden=!s.checklist?.length;el('checkItems').replaceChildren();
  for(const text of s.checklist??[]){
    const key=el('pack').value+' '+text;
    const row=document.createElement('label'),input=document.createElement('input');
    input.type='checkbox';input.checked=marked.has(key);
    input.addEventListener('change',()=>input.checked?marked.add(key):marked.delete(key));
    row.append(input,document.createTextNode(text));el('checkItems').append(row);
  }
  ghost=false;
  el('position').value=String(s.start??(vec(s.offset).lengthSq()>0?65:0));
  setLook();placement();reset();
}
steps.forEach((s,i)=>el('steps').add(new Option((i+1)+'. '+s.title,i)));
el('steps').onchange=()=>step(Number(el('steps').value));
el('prev').onclick=()=>step(current-1);el('next').onclick=()=>step(current+1);
el('position').oninput=placement;el('focus').onclick=focus;el('overview').onclick=overview;el('reset').onclick=reset;
el('ghost').onclick=()=>{ghost=!ghost;setLook();};
el('pack').onchange=()=>step(current);
surface.onkeydown=event=>{
  if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','Home'].includes(event.key))return;
  event.preventDefault(); if(event.key==='Home'){reset();return;}
  if(['+','=','-'].includes(event.key)){camera.zoom=THREE.MathUtils.clamp(camera.zoom*(event.key==='-'?.83:1.2),.25,16);camera.updateProjectionMatrix();}
  else{
    const offset=camera.position.clone().sub(controls.target);
    const angle=['ArrowRight','ArrowDown'].includes(event.key)?.14:-.14;
    const axis=['ArrowRight','ArrowLeft'].includes(event.key)?camera.up:new THREE.Vector3(1,0,0).applyQuaternion(camera.quaternion);
    camera.position.copy(controls.target).add(offset.applyAxisAngle(axis,angle));controls.update();
  }
  invalidate();
};
controls.addEventListener('change',invalidate);
new ResizeObserver(resize).observe(stage);step(0);
