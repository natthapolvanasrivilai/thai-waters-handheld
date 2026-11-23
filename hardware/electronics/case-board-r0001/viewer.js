import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const container = document.getElementById('viewport');
const info = document.getElementById('info');
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
container.append(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe8eee5);
const camera = new THREE.PerspectiveCamera(38,1,.1,650);
camera.up.set(0,0,1);
const orbit = new OrbitControls(camera,renderer.domElement);
orbit.minDistance=18; orbit.maxDistance=260;
scene.add(new THREE.HemisphereLight(0xfffdf1,0x899b94,2.4));
const light = new THREE.DirectionalLight(0xfff2d6,2.4);
light.position.set(-68,-65,140);scene.add(light);
function render(){renderer.render(scene,camera)}
orbit.addEventListener('change',render);
new ResizeObserver(()=>{renderer.setSize(container.clientWidth,container.clientHeight);camera.aspect=container.clientWidth/container.clientHeight;camera.updateProjectionMatrix();render()}).observe(container);
const data=Uint8Array.from(atob(document.getElementById('model').textContent),c=>c.charCodeAt(0));
const views={
 seats:[[9,-56,116],[16,2,8],'The two bosses with pilot holes take the screws. The third rest supports the board edge. All three print with the rear shell.'],
 board:[[56,-30,-42],[23,2,18],'Component side faces the floor. The two unequal mounting ears locate the board. Turn the case over in this view to inspect the packages.'],
 mounted:[[54,-90,137],[4,3,12],'With the housing open, lower the empty outline gauge onto all three supports. The screw heads sit on the face toward the screen. Check for rocking before fitting the display.'],
 wires:[[-44,-47,105],[3,7,13],'Red and black show the revised USB power, ground and indicator branches. Their far ends stay at the registered display and lamp locations.']
};
new GLTFLoader().parse(data.buffer,'',gltf=>{
  gltf.scene.traverse(obj=>{if(obj.isMesh){obj.material.metalness=obj.name.startsWith("Screw")?.25:0;obj.material.roughness=.76;}});
  scene.add(gltf.scene);
  function activate(name){
    const [position,target,text]=views[name];
    gltf.scene.traverse(obj=>{
      if(!obj.isMesh)return;
      const isBoard=/^PCB|^Package/.test(obj.name);
      const isScrew=obj.name.startsWith('Screw');
      if(obj.name==='Housing')obj.visible=name!=='board';
      else if(isBoard)obj.visible=name!=='seats';
      else if(isScrew)obj.visible=name==='mounted'||name==='wires';
      else obj.visible=name==='wires';
    });
    camera.position.set(...position);orbit.target.set(...target);orbit.update();
    info.textContent=text;
    for(const button of document.querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.mode===name));
    render();
  }
  for(const button of document.querySelectorAll('button'))button.onclick=()=>activate(button.dataset.mode);
  activate('mounted');
},e=>{info.textContent='The model could not be opened.';console.error(e)});
