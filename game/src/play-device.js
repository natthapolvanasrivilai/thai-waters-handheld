import * as T from 'three';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';

async function makeDevice(host, data, io){
 const renderer=new T.WebGLRenderer({antialias:true,alpha:true,powerPreference:'low-power'});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.65));renderer.setClearColor(0x000000,0);
 renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
 const surface=renderer.domElement;surface.setAttribute('aria-label','Rev E handheld. Drag the right-side reel to wind. Tap the screen to cast or lift.');
 surface.tabIndex=0;host.prepend(surface);
 const world=new T.Scene(),cam=new T.OrthographicCamera(-80,80,48,-48,.1,900);
 const eye=new T.Vector3(125,-54,230);cam.up.set(0,1,0);const center=new T.Vector3(7,0,12);cam.position.copy(center).add(eye);cam.lookAt(center);
 const env=new RoomEnvironment(),generator=new T.PMREMGenerator(renderer),envMap=generator.fromScene(env,.04);world.environment=envMap.texture;env.dispose();generator.dispose();
 const sky=new T.HemisphereLight(0xfff7df,0x68756b,1.0);world.add(sky);
 const key=new T.DirectionalLight(0xffefcb,2.2);key.position.set(-75,130,170);world.add(key);
 const bounce=new T.DirectionalLight(0xcde5e2,1.4);bounce.position.set(116,-44,68);world.add(bounce);
 const obj=new T.Group();world.add(obj);
 const parts=[],turning=new Set(['Rotor','Folding stem','Grip','Grip retainer','Hinge screw','Magnet']),folding=new Set(['Folding stem','Grip','Grip retainer']);
 const materials={
  'Revised housing':[0x819787,.62,0],Bezel:[0x253834,.51,.04],Rotor:[0x30594f,.47,.12],
  'Folding stem':[0xa86a39,.47,.14],Grip:[0xcb8b51,.57,.02],Collar:[0x465f57,.44,.2],
  'Hinge screw':[0x9ea3a1,.22,.92],'Grip retainer':[0xb9b4a1,.26,.85],Magnet:[0x979da1,.26,.9],
  'Display assembly':[0x17221f,.27,.06],'USB-C socket':[0xa8afb1,.22,.86]};
 function coating(name,config){
  const m=new T.MeshStandardMaterial({color:config[0],roughness:config[1],metalness:config[2],envMapIntensity:.70});
  if(config[2]>.7||name==='Display assembly')return m;
  m.onBeforeCompile=shader=>{
   shader.vertexShader='varying vec3 hwPosition;\n'+shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nhwPosition=position;');
   shader.fragmentShader='varying vec3 hwPosition;\n'+shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
    vec3 cell=floor(hwPosition*8.0);
    float speck=fract(sin(dot(cell,vec3(13.71,67.97,41.13)))*43758.5453)-.5;
    float band=sin(hwPosition.z*26.0);
    float fade=1.0-smoothstep(.15,.75,fwidth(hwPosition.z));
    diffuseColor.rgb *= 1.0 + .085*speck + .04*band*fade;`);
  };return m;
 }
 async function inflate(text,Type){
  const bytes=Uint8Array.from(atob(text),c=>c.charCodeAt(0));
  return new Type(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate'))).arrayBuffer());
 }
 for(const r of data){
  const [v,i]=await Promise.all([inflate(r.p,Int16Array),inflate(r.t,Uint32Array)]);
  const geom=new T.BufferGeometry();geom.setAttribute('position',new T.BufferAttribute(Float32Array.from(v,x=>x*.01),3));geom.setIndex(new T.BufferAttribute(i,1));geom.computeVertexNormals();
  const mesh=new T.Mesh(geom,coating(r.n,materials[r.n]));mesh.name=r.n;mesh.matrixAutoUpdate=false;parts.push(mesh);obj.add(mesh);
 }
 const lcd=document.createElement('canvas');lcd.width=480;lcd.height=320;const ctx=lcd.getContext('2d');
 const tex=new T.CanvasTexture(lcd);tex.colorSpace=T.SRGBColorSpace;tex.magFilter=T.NearestFilter;tex.minFilter=T.LinearFilter;tex.generateMipmaps=false;
 const glass=new T.Mesh(new T.PlaneGeometry(73.44,48.96),new T.MeshBasicMaterial({map:tex,toneMapped:false}));glass.position.set(0,0,28.53);obj.add(glass);
 const shadowCanvas=document.createElement('canvas');shadowCanvas.width=shadowCanvas.height=128;const sc=shadowCanvas.getContext('2d'),gr=sc.createRadialGradient(64,64,0,64,64,64);
 gr.addColorStop(0,'rgba(24,38,29,.54)');gr.addColorStop(.68,'rgba(30,40,29,.29)');gr.addColorStop(1,'rgba(28,46,32,0)');sc.fillStyle=gr;sc.fillRect(0,0,128,128);
 const shadow=new T.Mesh(new T.PlaneGeometry(155,96),new T.MeshBasicMaterial({map:new T.CanvasTexture(shadowCanvas),transparent:true,depthWrite:false,toneMapped:false}));shadow.position.set(5,-2,-1);world.add(shadow);
 const pivot=new T.Vector3(58.5,0,14.8),hinge=new T.Vector3(53.6,7.8,14.8);
 const about=(p,R)=>new T.Matrix4().makeTranslation(p.x,p.y,p.z).multiply(R).multiply(new T.Matrix4().makeTranslation(-p.x,-p.y,-p.z));
 let deployed=true,opening=Math.PI/2,spin=.9,previousInput=io.wheel(),drag=null,lastFrame=0,visible=false;
 function pose(){
  const turn=about(pivot,new T.Matrix4().makeRotationX(spin)),fold=about(hinge,new T.Matrix4().makeRotationZ(opening));
  for(const p of parts){if(!turning.has(p.name))continue;p.matrix.copy(turn);if(folding.has(p.name))p.matrix.multiply(fold);p.matrixWorldNeedsUpdate=true;}
  obj.updateMatrixWorld(true);
 }
 const ray=new T.Raycaster(),mouse=new T.Vector2(),point=new T.Vector3(),projectPlane=new T.Plane(new T.Vector3(1,0,0),-65);
 function pointerRay(e){const b=surface.getBoundingClientRect();mouse.set(2*(e.clientX-b.left)/b.width-1,1-2*(e.clientY-b.top)/b.height);ray.setFromCamera(mouse,cam);return ray;}
 function rotation(e){if(!pointerRay(e).ray.intersectPlane(projectPlane,point))return null;return Math.atan2(point.z-pivot.z,point.y-pivot.y);}
 function zone(e){
  const r=pointerRay(e);const hit=r.intersectObjects([...parts,glass],false)[0];
  if(hit?.object===glass)return {kind:'lcd',x:hit.uv.x,y:1-hit.uv.y};
  if(hit&&turning.has(hit.object.name))return {kind:'reel'};
  if(!hit&&r.ray.intersectPlane(projectPlane,point)&&Math.hypot(point.y-pivot.y,point.z-pivot.z)<16.8)return {kind:'reel'};
  return {kind:'case'};
 }
 surface.onpointerdown=e=>{
  if(e.button!==0)return;const target=zone(e);
  if(target.kind==='lcd'){io.screen(target.x,target.y);return;}
  if(target.kind!=='reel'||!deployed)return;
  const a=rotation(e);if(a===null)return;e.preventDefault();surface.setPointerCapture(e.pointerId);surface.classList.add('winding');drag={id:e.pointerId,a};io.beginWheel(a);
 };
 surface.onpointermove=e=>{
  if(!drag){surface.style.cursor=zone(e).kind==='reel'&&deployed?'grab':zone(e).kind==='lcd'?'pointer':'default';return;}
  if(drag.id!==e.pointerId)return;const next=rotation(e);if(next===null)return;
  const delta=Math.atan2(Math.sin(next-drag.a),Math.cos(next-drag.a));drag.a=next;io.wind(next,delta);surface.style.cursor='grabbing';
 };
 function end(){drag=null;surface.classList.remove('winding');}
 surface.onpointerup=surface.onpointercancel=surface.onlostpointercapture=end;
 function fit(){
  const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;
  const aspect=w/h,half=Math.max(41,67/aspect);cam.left=-half*aspect;cam.right=half*aspect;cam.top=half;cam.bottom=-half;cam.updateProjectionMatrix();renderer.setSize(w,h,false);
 }
 new ResizeObserver(fit).observe(host);pose();fit();
 const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;});observer.observe(host);
 function render(now){requestAnimationFrame(render);if(!visible||host.hidden||document.hidden||now-lastFrame<40)return;lastFrame=now;
  const current=io.wheel();spin+=current-previousInput;previousInput=current;
  opening+=((deployed?Math.PI/2:0)-opening)*.25;pose();
  io.paint(ctx);tex.needsUpdate=true;renderer.render(world,cam);
 }
 requestAnimationFrame(render);
 return {fold(){end();deployed=!deployed;return deployed;},resize:fit};
}
window.makeThaiHandheld=makeDevice;

