// Home of optional map state. Actual travel still uses the game's guarded action.
const locationMap=(()=>{
 const data=@@MAP_BUNDLE@@;
 const canvas=$('waterbodyMap'),picker=$('mapWaterbody'),sheet=$('waterbodyMapSheet'),travel=$('mapTravel');
 const ctx=canvas.getContext('2d'),model=waterbodyMapModel.create(data.pins,canvas.width,canvas.height);
 const text=(en,th)=>language==='th'?th:en;
 let revision=0;
 function draw(){
  const w=canvas.width,h=canvas.height,[px,py]=model.pan();
  ctx.fillStyle='#183742';ctx.fillRect(0,0,w,h);
  ctx.strokeStyle='#2b4b52';ctx.lineWidth=.6;
  for(let x=14;x<w;x+=28){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
  for(let y=10;y<h;y+=28){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  ctx.save();ctx.translate(px,py);
  ctx.fillStyle='#5b8070';ctx.strokeStyle='#8db6a0';ctx.lineWidth=1;
  ctx.beginPath();
  for(const ring of data.outline){
   ring.forEach((q,i)=>{const [x,y]=model.project(q);if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);});
   ctx.closePath();
  }
  ctx.fill();ctx.stroke();ctx.restore();
  for(const [id] of data.pins){
   const [x,y]=model.position(id),chosen=id===model.selected();
   if(chosen){ctx.beginPath();ctx.arc(x,y,7,0,Math.PI*2);ctx.strokeStyle='#ffe5a9';ctx.lineWidth=1;ctx.stroke();}
   const r=chosen?4.7:3.5;
   ctx.beginPath();ctx.moveTo(x,y-r);ctx.lineTo(x+r,y);ctx.lineTo(x,y+r);ctx.lineTo(x-r,y);ctx.closePath();
   ctx.fillStyle=chosen?'#ffdf9a':'#99e5d8';ctx.strokeStyle='#163840';ctx.lineWidth=.9;ctx.fill();ctx.stroke();
  }
  if(document.activeElement===canvas){ctx.strokeStyle='#b2e9de';ctx.lineWidth=2;ctx.strokeRect(1,1,w-2,h-2);}
  // Native LCD painter listens for DOM mutations, not Canvas bitmap changes.
  canvas.dataset.mapFrame=String(++revision);
 }
 const allowed=()=>menu.open&&menuPage==='spots'&&!sheet.hidden&&spotTravelAllowed();
 function update(fromPicker=false){
  const id=model.selected(),v=id===null?'':String(id);
  if(!fromPicker&&picker.value!==v){
   picker.value=v;picker.dispatchEvent(new Event('change',{bubbles:true}));
  }
  travel.disabled=id===null||!allowed();
  $('mapStage').textContent=id===null?text(data.pins.length+' mapped waters','แหล่งน้ำบนแผนที่ '+data.pins.length+' แห่ง'):atlas.locations[id].name;
  $('mapAccessNote').textContent=data.label[language==='th'?'th':'en'];
  $('mapTravel').textContent=text('Travel','เดินทาง');
  $('mapReset').textContent=text('Reset map','ตั้งแผนที่ใหม่');
  $('mapToList').textContent=text('Full list','รายชื่อทั้งหมด');
  $('locationMapOpen').textContent=text('Map','แผนที่');
  canvas.setAttribute('aria-label',text('Thailand waterbody overview. Arrow keys pan; Home resets. Use the location list to choose.','แผนที่แหล่งน้ำในประเทศไทย ใช้ลูกศรเลื่อน กด Home เพื่อตั้งใหม่ เลือกแหล่งน้ำจากรายชื่อ'));
  $('mapBootNote').textContent=spotTravelAllowed()?'':text('Resume fishing to travel.','กลับสู่เกมก่อนเดินทาง');
  draw();
 }
 function labels(){
  const id=model.selected();
  picker.replaceChildren(new Option(text('Choose mapped water','เลือกแหล่งน้ำบนแผนที่'),''),...data.pins.map(([id])=>new Option(atlas.locations[id].name,id)));
  picker.value=id===null?'':String(id);update();
 }
 function at(e){
  const r=canvas.getBoundingClientRect();
  const w=canvas.clientWidth,h=canvas.clientHeight;
  return {x:Number.isFinite(e.offsetX)&&w>0?e.offsetX*canvas.width/w:(e.clientX-r.left)*canvas.width/r.width,
   y:Number.isFinite(e.offsetY)&&h>0?e.offsetY*canvas.height/h:(e.clientY-r.top)*canvas.height/r.height,
   clientX:e.clientX,clientY:e.clientY};
 }
 canvas.addEventListener('pointerdown',e=>{
  if(e.isPrimary&&e.button===0&&model.start(e.pointerId,at(e)))canvas.setPointerCapture(e.pointerId);
 });
 canvas.addEventListener('pointermove',e=>{
  if(model.move(e.pointerId,at(e))){canvas.dataset.dragging='';draw();}
 });
 canvas.addEventListener('pointerup',e=>{
  delete canvas.dataset.dragging;if(model.end(e.pointerId,at(e)))update();
 });
 for(const event of ['pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>{
  model.cancel(e.pointerId);delete canvas.dataset.dragging;
 });
 canvas.addEventListener('keydown',e=>{
  const move={ArrowUp:[0,-14],ArrowDown:[0,14],ArrowLeft:[-14,0],ArrowRight:[14,0]}[e.key];
  if(!move&&e.key!=='Home')return;
  e.preventDefault();e.stopPropagation();
  if(move)model.panBy(...move);else model.resetPan();draw();
 });
 for(const event of ['focus','blur'])canvas.addEventListener(event,draw);
 picker.onchange=()=>{model.choose(picker.value===''?null:Number(picker.value));update(true);};
 $('mapReset').onclick=()=>{model.resetPan();draw();canvas.focus({preventScroll:true});};
 travel.onclick=()=>model.confirm(allowed(),travelToSpot);
 $('mapToList').onclick=()=>{menuSheets.go('spots',0);$('locationMapOpen').focus({preventScroll:true});};
 function open(){
  if(menuSheets.go('spots',2)){labels();canvas.focus({preventScroll:true});}
 }
 $('locationMapOpen').onclick=open;
 document.addEventListener('game-language',labels);
 sheet.addEventListener('spots-map-visible',()=>update());
 labels();
 return {open,resetSelection(){model.choose(null);update();}};
})();
