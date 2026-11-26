const stages=[
  ['Housing Speaker Motor Diffuser',[55,-100,125],[0,0,5],'Lay the empty housing open side up. Lower the diffuser 22 mm inboard, then slide it toward USB until its shoulder seats. Fit the speaker and motor gauges and check the lead exits.'],
  ['Shelf',[-68,-64,87],[-34,5,12],'Start with the shelf 14 mm inboard and 24 mm above its seat. Keep the speaker in place. Lower the shelf vertically to the landing height.'],
  ['',[-63,-61,78],[-38,4,12],'At landing height, slide the shelf 14 mm toward the USB wall. The short rails face up.'],
  ['ShelfScrew RGBcarrier',[-48,-62,98],[-42,8,11],'Seat the shelf on both posts. Hand-start one M2 × 6 screw in the prepared pilot. With the shelf fixed, lower the lamp 18 mm toward the service end from its seat. Slide it back along the USB wall, LED facing the light guide.'],
  ['A2 A3 A3J1plug Combined', [58,-93,130],[5,0,10],'Check the sensor against the reel wall. Install either A3 gauge on the floor rails. The plug shown is the seated alternative. Set the combined board package side down on its three housing supports.'],
  ['cellAlt bridge Keycap KEY Retainer',[-61,-88,123],[0,4,10],'Fit the keyed cap from inside before seating the switch board and retainer. Trial one battery gauge at a time. Use loose dummy leads to check the bridge and clear the screw paths.'],
  ['A1 serviceCover Rotor Stem Grip Collar Removablerodgrip',[71,-101,117],[0,0,13],'Lower the A1 gauge screen side up. Check for rocking and wire pressure. Try a 4.04 mm diameter witness or the intended screw and driver through each rear controller access with the rod grip in place.'],
  ['Bezel Closure0 Closure1',[38,-85,132],[0,0,16],'Hold the bezel level and slightly toward the reel. Lower almost to the rim, slide it toward USB to engage the two hidden hooks, then seat it flat. From the rear, fit two M2 × 6 screws into the blind pilots. Check the front is smooth, the glass stays free and the diffuser stays captive.']
];
new GLTFLoader().parse(data.buffer,'',gltf=>{
  const finishes={
    Housing:0x899c89, Shelf:0x899c89, Removablerodgrip:0x899c89, Bezel:0x303938, Rotor:0x303938,
    Diffuser:0xe4eeee, Stem:0xd99a4e, Grip:0xd99a4e, Keycap:0xd99a4e, serviceCover:0x202221
  };
  gltf.scene.traverse(o=>{
    if(o.isMesh && !o.geometry.attributes.normal)o.geometry.computeVertexNormals();
    if(o.isMesh&&Object.hasOwn(finishes,o.name))o.material=new THREE.MeshStandardMaterial({
      color:finishes[o.name],roughness:o.name==='Diffuser'?.38:.76,metalness:0,flatShading:true
    });
  });
  scene.add(gltf.scene);
  function show(i){
    const names=new Set(stages.slice(0,i+1).flatMap(row=>row[0].split(' ')));
    gltf.scene.traverse(o=>{if(!o.isMesh)return;
      o.visible=names.has(o.name)||(o.name.startsWith('LED')&&names.has('RGBcarrier'));
      if(o.name==='Shelf'){o.position.x=(i===1||i===2)?14:0;o.position.z=i===1?24:0;}
    });
    camera.position.set(...stages[i][1]);orbit.target.set(...stages[i][2]);orbit.update();
    info.textContent=stages[i][3];document.querySelectorAll('[data-step]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.step===i)));render();
  }
  document.getElementById('inspect-light').onclick=()=>{
    show(7);
    camera.position.set(-85,-8,19);orbit.target.set(-49,0,15);orbit.update();render();
    info.textContent='USB-C sits above one clear status window. One RGB emitter serves power, charging and USB. This view shows the unpowered diffuser.';
  };
  document.querySelectorAll('[data-step]').forEach(b=>b.onclick=()=>show(+b.dataset.step));show(0);
},error=>{info.textContent='The fit guide could not load.';console.error(error);});
