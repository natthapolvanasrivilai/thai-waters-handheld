// The five-species pilot is opt-in. The 96×50 bank is always the fallback.
const detailArt=@@HQ_WEBP@@;
const detailImages=new Map();
const showDetailArt=new URLSearchParams(location.search).get('fishArt')==='hq';
function loadDetailArt(id){
 if(!showDetailArt||!Number.isInteger(id)||!Object.hasOwn(detailArt,id))return null;
 const entry=detailArt[id];
 if(originalAtlas.fish[id]?.name!==entry.scientific)return null;
 if(!detailImages.has(id)){
  const img=new Image(),state={img,ready:false,done:null};
  state.done=new Promise(resolve=>{
   img.onload=()=>{state.ready=img.naturalWidth===288&&img.naturalHeight===150;resolve(state.ready);};
   img.onerror=()=>resolve(false);
  });
  detailImages.set(id,state);
  img.src='data:image/webp;base64,'+entry.webp;
 }
 return detailImages.get(id);
}
function drawLandedPortrait(c,id,x,y,w,h){
 const p=loadDetailArt(id);
 if(!p?.ready)return drawSpecimen(c,id,x,y,w,h);
 c.save();c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high';c.drawImage(p.img,x,y,w,h);c.restore();
}
function enhanceCollectedPortrait(icon,id){
 const p=loadDetailArt(id);if(!p)return;
 p.done.then(()=>{
  if(!p.ready||!icon.isConnected||!g.caught(id))return;
  icon.width=288;icon.height=150;icon.style.imageRendering='auto';icon.dataset.fishArt='hq';
  icon.getContext('2d').drawImage(p.img,0,0);
 });
}
