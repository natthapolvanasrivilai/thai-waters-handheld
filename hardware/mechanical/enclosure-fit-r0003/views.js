const stages=[
  ['Housing Speaker Motor',[55,-100,125],[0,0,5],'Lay the housing open side up. Fit the oval speaker gauge over its grille and the round motor gauge into its seat. Check both lead exits.'],
  ['Shelf',[-68,-64,87],[-34,5,12],'Start with the shelf 14 mm inboard and 24 mm above its seat. Keep the speaker in place. Lower the shelf vertically to the landing height.'],
  ['',[-63,-61,78],[-38,4,12],'At landing height, slide the shelf 14 mm toward the USB wall. The short rails face up.'],
  ['ShelfScrew',[-48,-62,98],[-42,8,11],'Seat the shelf on both posts. Hand-start one M2 × 6 screw in the prepared pilot. With the shelf fixed, lower the lamp 18 mm toward the service end from its seat. Slide it back along the USB wall, LED facing the light guide.'],
  ['A2 A3 A3J1plug Combined USBPCB1 USBPCB2', [58,-93,130],[5,0,10],'Check the sensor against the reel wall. Install either A3 gauge on the floor rails. The plug shown is the seated alternative. Set the combined board package side down on its three housing supports.'],
  ['cellAlt bridge Keycap KEY Retainer statusUsbGuide statusChgGuide statusPwrGuide',[-61,-88,123],[0,4,10],'Fit the keyed cap from inside before seating the switch board and retainer. Trial one battery gauge at a time. Use loose dummy leads to check the bridge and clear the screw paths.'],
  ['A1 serviceCover Rotor Stem Grip Collar Removablerodgrip',[71,-101,117],[0,0,13],'Lower the A1 gauge screen side up. Check for rocking and wire pressure. Try a 4.04 mm diameter witness or the intended screw and driver through each rear controller access with the rod grip in place.'],
  ['Bezel Closure0 Closure1 Closure2 Closure3',[38,-85,132],[0,0,16],'Seat the bezel by hand before starting four M2 × 6 screws. Check the heads sit below the face and the glass gauge stays free. Remove and refit to inspect the bosses.']
];
new GLTFLoader().parse(data.buffer,'',gltf=>{
  scene.add(gltf.scene);
  function show(i){
    const names=new Set(stages.slice(0,i+1).flatMap(row=>row[0].split(' ')));
    gltf.scene.traverse(o=>{if(!o.isMesh)return;
      o.visible=names.has(o.name);
      if(o.name==='Shelf'){o.position.x=(i===1||i===2)?14:0;o.position.z=i===1?24:0;}
    });
    camera.position.set(...stages[i][1]);orbit.target.set(...stages[i][2]);orbit.update();
    info.textContent=stages[i][3];document.querySelectorAll('[data-step]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.step===i)));render();
  }
  document.querySelectorAll('[data-step]').forEach(b=>b.onclick=()=>show(+b.dataset.step));show(0);
},error=>{info.textContent='The fit guide could not load.';console.error(error);});
