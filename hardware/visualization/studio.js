import * as T from 'three';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import {EffectComposer} from 'three/examples/jsm/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/examples/jsm/postprocessing/RenderPass.js';
import {GTAOPass} from 'three/examples/jsm/postprocessing/GTAOPass.js';
import {OutputPass} from 'three/examples/jsm/postprocessing/OutputPass.js';
import {ShaderPass} from 'three/examples/jsm/postprocessing/ShaderPass.js';
import {FXAAShader} from 'three/examples/jsm/shaders/FXAAShader.js';

const finishes={
 petg:[.57,.02], rubber:[.83,.02], steel:[.28,.88], foil:[.37,.86],
 copper:[.33,.70], soldermask:[.48,.13], fabric:[.91,.01],
 glass:[.16,.14], epoxy:[.44,.03], painted:[.62,.04]
};
function finishOf(r){
 if(r.finish&&finishes[r.finish])return r.finish;
 if(/cloth|acoustic fabric/i.test(r.name))return 'fabric';
 if(/escutcheonlip|usbsurround/i.test(r.id))return 'rubber';
 if(/Housing|Bezel|Key cap|Retainer|Stem|^Grip$|Rotor|^Collar|rod grip|keeper|bridge|usbSurround/i.test(r.id))return 'petg';
 if(/screw|washer|magnet|terminal|USB-C socket|steel|nickel|nut|retaining ring/i.test(r.name))return 'steel';
 if(/cell|pouch/i.test(r.name)&&!r.option?.includes('drawing'))return 'foil';
 if(/wire|shrink|rubber|seal|gasket/i.test(r.name))return 'rubber';
 if(/pcb|board|substrate/i.test(r.name))return 'soldermask';
 if(/lens|guide|screen|display stack|glass/i.test(r.name))return 'glass';
 return 'painted';
}
export function materialFor(r){
 const finish=finishOf(r),[roughness,metalness]=finishes[finish];
 const m=new T.MeshStandardMaterial({color:r.color,roughness,metalness,side:T.DoubleSide});
 // Millimetre-scale finish is applied in part space, including exploded views.
 const types={petg:1,steel:2,foil:3,rubber:4,soldermask:5,fabric:6};
 const type=types[finish]||0;
 if(!type)return m;
 m.customProgramCacheKey=()=> 'finish-'+type;
 m.onBeforeCompile=s=>{
   s.vertexShader='varying vec3 partMM;\n'+s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\npartMM=position;');
   const defs='varying vec3 partMM;\nfloat surfaceNoise(vec3 p){return fract(sin(dot(p,vec3(12.9898,78.233,39.425)))*43758.5453);}\n';
   s.fragmentShader=defs+s.fragmentShader.replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
      float fleck=surfaceNoise(floor(partMM*5.));
      float ridge=sin(partMM.z*31.416);
      float visibleBand=1.-smoothstep(.10,.44,fwidth(partMM.z));
      float finishBump=0.;
      #if ${type} == 1
       finishBump=.013*ridge*visibleBand; roughnessFactor+=.065*ridge*visibleBand;
       diffuseColor.rgb*=.982+.025*fleck+.019*ridge*visibleBand;
      #elif ${type} == 2
       roughnessFactor+=.065*(fleck-.5);finishBump=.002*sin(partMM.y*77.)*(1.-smoothstep(.03,.21,fwidth(partMM.y)));
      #elif ${type} == 3
       finishBump=.045*sin(partMM.x*1.36+sin(partMM.y*.68))+.012*sin(partMM.y*3.7);roughnessFactor+=.09*(fleck-.5);
      #elif ${type} == 6
       finishBump=.014*sin(partMM.x*34.)*sin(partMM.y*34.)*visibleBand;
      #else
       roughnessFactor+=.09*(fleck-.5);diffuseColor.rgb*=.98+.034*fleck;
      #endif`).replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
       normal=normalize(normal-vec3(dFdx(finishBump),dFdy(finishBump),0.));`);
 };
 return m;
}
export function lightStudio(renderer,scene,cam){
 renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=.97;
 scene.background=new T.Color('#e4e2d9');
 const studio=new RoomEnvironment(),pmrem=new T.PMREMGenerator(renderer);
 scene.environment=pmrem.fromScene(studio,.045).texture;
 scene.environmentIntensity=.68;studio.dispose();pmrem.dispose();
 scene.add(new T.HemisphereLight(0xfff6de,0x6d9294,.42));
 for(const [x,y,z,power,color] of [[-80,120,130,2.1,0xffeedb],[120,45,-110,1.55,0xd8ebff]]){
   const lamp=new T.DirectionalLight(color,power);lamp.position.set(x,y,z);scene.add(lamp);
 }
 const composer=new EffectComposer(renderer);
 composer.addPass(new RenderPass(scene,cam));
 let ao;
 if(renderer.extensions.has('EXT_color_buffer_float')){
   ao=new GTAOPass(scene,cam,1,1);
   ao.updateGtaoMaterial({radius:3.1,thickness:1.8,samples:12,distanceExponent:1.4});
   ao.blendIntensity=.86;composer.addPass(ao);
 }
 composer.addPass(new OutputPass());
 const aa=new ShaderPass(FXAAShader);composer.addPass(aa);
 return {
   resize(w,h){composer.setSize(w,h);const d=renderer.getPixelRatio();aa.material.uniforms.resolution.value.set(1/(w*d),1/(h*d));},
   render(clip){
     // Keep the section plane open when the AO depth prepass cannot clip it.
     if(ao)ao.enabled=!clip;
     composer.render();
   },
   effects:ao?'GTAO + FXAA':'FXAA'
 };
}
