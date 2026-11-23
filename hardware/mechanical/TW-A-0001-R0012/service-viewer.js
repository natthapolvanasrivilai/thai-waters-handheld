import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const $=id=>document.getElementById(id);
const data=JSON.parse($('data').textContent);
const qa=data.qa;
const stage=$('stage');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
renderer.setClearColor(0,0);
stage.append(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.OrthographicCamera(-20,20,20,-20,.1,500);
camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=false;
const draw=()=>renderer.render(scene,camera);
controls.addEventListener('change',draw);
scene.add(new THREE.HemisphereLight(0xfffff3,0x7b8077,2.0));
for(const [v,intensity] of [[[20,-32,58],2.1],[[-28,20,28],1.0]]){
 const light=new THREE.DirectionalLight(0xfff9e9,intensity);
 light.position.set(...v);scene.add(light);
}
const meshes=new Map();
const leadMeshes=new Map();
const state={u:0,d:0,clip:false,zoom:false};
const pivot=new THREE.Vector3(...qa.rocker_pivot_xyz_mm);
const xAxis=new THREE.Vector3(1,0,0);
function cameraPose(close){
 state.zoom=close;
 const target=close?new THREE.Vector3(21,-7,12.5):new THREE.Vector3(22,3.5,10.0);
 controls.target.copy(target);
 camera.position.copy(target).add(new THREE.Vector3(close?-41:-46,close?12:27,close?25:42));
 camera.lookAt(target);
 camera.zoom=1;
 resize();
 controls.update();
}
function resize(){
 const w=stage.clientWidth,h=stage.clientHeight,aspect=w/h;
 const half=state.zoom?Math.max(7.5,11/aspect):Math.max(17,24/aspect);
 camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;
 camera.updateProjectionMatrix();renderer.setSize(w,h,false);draw();
}
new ResizeObserver(resize).observe(stage);
function makeMaterial(color){return new THREE.MeshStandardMaterial({color,roughness:.78,metalness:.025,side:THREE.DoubleSide})}
async function decode(s,Type){
 const bytes=Uint8Array.from(atob(s),c=>c.charCodeAt(0));
 const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate'));
 return new Type(await new Response(stream).arrayBuffer());
}
function svgPath(rows,transform){
 return rows.map(points=>points.map((point,i)=>{
  const [y,z]=transform(...point);
  return (i?'L':'M')+(13.4*(y+17.4)).toFixed(2)+' '+(123-(z-7.1)*10.2).toFixed(2);
 }).join(' ')+' Z').join(' ');
}
function spine(points){
 const p=points.map(v=>new THREE.Vector3(...v));
 return new THREE.CatmullRomCurve3(p,false,'centripetal');
}
function plot(){
 const rows=data.path.filter(r=>r.phase==='withdraw');
 const max=Math.ceil(Math.max(...rows.map(r=>+r.rigid_W1_native_mm))+0.1);
 const px=d=>37+(+d/8.25)*288;
 const py=g=>92-(+g/max)*75;
 $('plot').innerHTML='<path class="axis" fill="none" d="M37 12V92H325"/><text x="5" y="22" font-size="10">'+max+' mm</text><text x="19" y="95" font-size="10">0</text><text x="35" y="110" font-size="10">0</text><text x="256" y="110" font-size="10">8.25 mm travel</text><path class="cv" d="'+rows.map((r,i)=>(i?'L':'M')+px(r.travel_mm)+','+py(r.rigid_W1_native_mm)).join(' ')+'"/><path fill="none" stroke="#ab7448" stroke-width="2.4" d="'+rows.map((r,i)=>(i?'L':'M')+px(r.travel_mm)+','+py(r.W4_W1_mesh_mm)).join(' ')+'"/><circle id="marker" r="4" fill="#b66e36"/>';
 return {px,py};
}
const axes=plot();
function update(value){
 const m=value/1000;
 state.u=Math.min(1,m/.26);state.d=data.stroke*Math.max(0,(m-.26)/.74);
 const {u,d}=state,theta=THREE.MathUtils.degToRad(qa.rocker_angle_deg*u);
 for(const [k,o] of meshes){
  const motion=data.items[k].motion;
  if(motion==='rigid')o.position.y=d;
  if(motion==='rocker'){
   o.rotation.x=theta;
   o.position.copy(pivot).sub(pivot.clone().applyAxisAngle(xAxis,theta));o.position.y+=d;
  }
  if(motion==='context')o.visible=$('context').checked;
  if(motion==='display')o.visible=$('display').checked;
 }
 const frame=d/.125,lo=Math.floor(frame+1e-8),hi=Math.min(66,lo+1),frac=Math.max(0,frame-lo);
 for(const [net,frames] of Object.entries(data.leads)){
  const p=frames[lo].map((v,i)=>v.map((n,j)=>n+frac*(frames[hi][i][j]-n)));
  const g=new THREE.TubeGeometry(spine(p),72,.71,14,false);
  const o=leadMeshes.get(net);
  if(o){o.geometry.dispose();o.geometry=g;}else{
   const mesh=new THREE.Mesh(g,makeMaterial({VCC:'#b76e47',GND:'#6b6156',SDA:'#bd946a',SCL:'#a78b50'}[net]));
   leadMeshes.set(net,mesh);scene.add(mesh);
  }
 }
 const thetaCS=Math.cos(theta),thetaSN=Math.sin(theta),py=pivot.y,pz=pivot.z;
 const drawSection=(k,col,tr)=>'<path fill="'+col+'" fill-opacity=".60" stroke="'+col+'" stroke-width="1.2" fill-rule="evenodd" d="'+svgPath(data.section[k],tr)+'"/>';
 $('polys').innerHTML=drawSection('h','#437f73',(y,z)=>[y,z])+drawSection('p','#aa946e',(y,z)=>[y+d,z])+drawSection('l','#bf662f',(y,z)=>[py+(y-py)*thetaCS-(z-pz)*thetaSN+d,pz+(y-py)*thetaSN+(z-pz)*thetaCS]);
 const row=d>0?data.path[9+Math.min(66,Math.round(frame))]:data.path[Math.round(u*8)];
 const gap=+row.rigid_W1_native_mm;
 $('gap').textContent=gap.toFixed(2)+' mm';
 $('marker').setAttribute('cx',axes.px(d));$('marker').setAttribute('cy',axes.py(gap));
 $('dist').textContent=d.toFixed(2)+' mm';
 $('state').textContent=m===0?'Seated':m<.26?'Pressing the rocker':m===.26?'Rocker held':m===1?'Fully withdrawn':'Withdrawing';
 const closed=$('display').checked;
 const val=closed?row.installed_W4_mesh_mm:row.W4_mesh_mm;
 $('w4').textContent=(closed?'Display boards seated. ':'Display assembly lifted. ')+'Closest sampled W4 clearance '+Number(val).toFixed(2)+' mm, '+(closed?row.installed_W4_net:row.W4_net)+' to '+(closed?row.installed_W4_part:row.W4_part)+'.';
 document.documentElement.dataset.motion=String(value);
 draw();
}
let animation=0;
function stop(){cancelAnimationFrame(animation);animation=0;$('play').textContent='Play motion'}
$('play').onclick=()=>{
 if(animation){stop();return}
 const start=+$('motion').value>=1000?0:+$('motion').value;
 const epoch=performance.now()-start*7;
 function tick(t){
  const v=Math.min(1000,Math.round((t-epoch)/7));$('motion').value=v;update(v);
  if(v<1000)animation=requestAnimationFrame(tick);else stop();
 }
 $('play').textContent='Pause';animation=requestAnimationFrame(tick);
};
$('motion').oninput=()=>{stop();update(+$('motion').value)};
for(const b of document.querySelectorAll('[data-at]'))b.onclick=()=>{stop();$('motion').value=b.dataset.at;update(+b.dataset.at)};
$('fit').onclick=()=>cameraPose(false);
$('closeup').onclick=()=>cameraPose(true);
$('context').oninput=$('display').oninput=()=>update(+$('motion').value);
async function main(){
 await Promise.all(Object.entries(data.items).map(async([k,r])=>{
  const [verts,indices]=await Promise.all([decode(r.v,Int16Array),decode(r.t,Uint32Array)]);
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(Float32Array.from(verts,n=>.01*n),3));
  g.setIndex(new THREE.BufferAttribute(indices,1));g.computeVertexNormals();
  const o=new THREE.Mesh(g,makeMaterial(r.color));if(r.motion==='display'){o.material.transparent=true;o.material.opacity=.22;o.material.depthWrite=false;o.renderOrder=4;}o.name=k;meshes.set(k,o);scene.add(o);
 }));
 const min=qa.rigid_W1_minimum_sample;
 $('minimum').textContent='Lowest sampled gap '+min.gap_mm.toFixed(3)+' mm at '+min.travel_mm.toFixed(3)+' mm ('+min.part+'). Continuous nominal lower bound '+qa.continuous_rigid_W1_lower_bound_mm.toFixed(3)+' mm.';
 const flex=qa.minimum_W4_mesh;
 $('flexmin').textContent='Minimum with the display lifted '+Number(flex.W4_mesh_mm).toFixed(3)+' mm at '+Number(flex.travel_mm).toFixed(3)+' mm. Constraint with the display seated: '+qa.minimum_installed_W4_mesh.installed_W4_part+'.';
 const overlap=qa.unmodified_seated_plastics_intersections.reduce((s,c)=>s+c.volume_mm3,0);
 $('limits').textContent='Seated plastic overlap '+overlap.toFixed(3)+' mm³. The casting omits the catch recess and internal socket detail. TPA seating and the 0.916 mm SDA bend at full travel need a physical trial.';
 cameraPose(false);update(0);$('loading').hidden=true;document.documentElement.dataset.ready='true';
}
main().catch(e=>{$('loading').textContent='3D view could not initialize. '+e.message;document.documentElement.dataset.ready='error';console.error(e)});

