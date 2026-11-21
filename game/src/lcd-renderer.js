// Draw the interface onto the same 480 × 320 framebuffer as the scene.
// The browser still owns layout, hit testing, inputs, focus, and scrolling.
// Collection names can wrap within a long scientific word. Keep the
// existing word-oriented rendering for every other LCD surface.
function* lcdPaintSegments(text, softWrap) {
 if(!softWrap){yield* layoutSegments(text);return;}
 if(thaiChars){
  for(const s of thaiChars.segment(text))if(s.segment.trim())yield {0:s.segment,index:s.index};
 }else yield* text.matchAll(/\S\p{Mark}*/gu);
}
const paintLcdInterface = (() => {
 const layer = document.createElement('canvas');
 layer.width = 480;
 layer.height = 320;
 const pen = layer.getContext('2d');
 const ui = $('lcdUI');
 let dirty = true, previousState = '', origin;

 const invalidate = () => { dirty = true; };
 const menuChanges=new MutationObserver(invalidate);
 menuChanges.observe(menu, {attributes:true, childList:true, characterData:true, subtree:true});
 for (const event of ['scroll','focusin','focusout','pointerover','pointerout','input','change','select','keyup','pointerup'])
  ui.addEventListener(event, invalidate, true);
 document.fonts.ready.then(invalidate);
 document.fonts.addEventListener?.('loadingdone', invalidate);
 const px = value => parseFloat(value) || 0;

 function roundedBox(x,y,w,h,r,fill) {
  pen.beginPath();
  pen.roundRect(x,y,w,h,Math.min(r,w/2,h/2));
  pen.fillStyle = fill;
  pen.fill();
 }
 function box(rect) {
  return {x:rect.left-origin.left,y:rect.top-origin.top,w:rect.width,h:rect.height};
 }
 function background(el,style,b) {
  const {x,y,w,h} = b, radius = px(style.borderTopLeftRadius);
  if (style.backgroundColor !== 'rgba(0, 0, 0, 0)') roundedBox(x,y,w,h,radius,style.backgroundColor);
  if (style.borderTopWidth === style.borderRightWidth && style.borderTopWidth === style.borderBottomWidth &&
      style.borderTopWidth === style.borderLeftWidth && px(style.borderTopWidth)) {
   const line = px(style.borderTopWidth);
   pen.beginPath();
   pen.roundRect(x+line/2,y+line/2,w-line,h-line,Math.max(0,radius-line/2));
   pen.lineWidth=line; pen.strokeStyle=style.borderTopColor; pen.stroke();
  } else {
   for (const side of ['Top','Bottom','Left','Right']) {
    const line=px(style['border'+side+'Width']);
    if (!line) continue;
    pen.fillStyle=style['border'+side+'Color'];
    if (side==='Top' || side==='Bottom') pen.fillRect(x,y+(side==='Top'?0:h-line),w,line);
    else pen.fillRect(x+(side==='Left'?0:w-line),y,line,h);
   }
  }
  if (el.matches(':focus-visible') && !el.matches('h2')) {
   pen.strokeStyle='#ffc67a'; pen.lineWidth=2;
   pen.strokeRect(x+1,y+1,w-2,h-2);
  }
 }
 function face(style) {
  pen.font=style.fontStyle+' '+style.fontWeight+' '+style.fontSize+' '+style.fontFamily;
  pen.fillStyle=style.color;
  pen.textAlign='left';
  pen.textBaseline='alphabetic';
 }
 function lettering(text,x,y,outline=false) {
  if (outline) {
   pen.strokeStyle='#16332c'; pen.lineWidth=2.8; pen.lineJoin='round'; pen.strokeText(text,x,y);
  }
  pen.fillText(text,x,y);
 }
 function baseline(rect) {
  const metrics=pen.measureText('Ag');
  return rect.top-origin.top+(rect.height+metrics.fontBoundingBoxAscent-metrics.fontBoundingBoxDescent)/2;
 }
 function textNode(node,style,outline) {
  // Range geometry retains the browser's word wrapping, floats and inline layout.
  const range=document.createRange(), content=node.textContent;
  face(style);
  let lineStart=-1,lineEnd=0,lineTop;
  function flush() {
   if (lineStart<0) return;
   range.setStart(node,lineStart); range.setEnd(node,lineEnd);
   const rect=range.getBoundingClientRect();
   lettering(content.slice(lineStart,lineEnd).replace(/\s+/g,' '),rect.left-origin.left,baseline(rect),outline);
  }
  const softWrap=node.parentElement?.matches('#records .record > b');
  for (const match of lcdPaintSegments(content,softWrap)) {
   range.setStart(node,match.index);range.setEnd(node,match.index+match[0].length);
   const top=range.getBoundingClientRect().top;
   if (lineStart<0 || Math.abs(top-lineTop)>1) {
    flush(); lineStart=match.index; lineTop=top;
   }
   lineEnd=match.index+match[0].length;
  }
  flush();
 }
 function centered(text,b,color,size,outline=false) {
  pen.fillStyle=color; pen.font='650 '+size+'px "Atkinson Hyperlegible Next", sans-serif';
  pen.textAlign='center'; pen.textBaseline='middle';
  lettering(text,b.x+b.w/2,b.y+b.h/2,outline);
 }
 function battery(b) {
  const value=$('simBattery').value, level=parseInt(value,10);
  const x=Math.round(b.x+3),y=Math.round(b.y+2);
  const color=level<=15?'#ff925e':'#f6f5d8';
  roundedBox(x-1,y-1,26,14,4,'#193a31');
  roundedBox(x,y,24,12,3,color);
  roundedBox(x+2,y+2,20,8,1,'#274137');
  pen.fillStyle=color;pen.fillRect(x+25,y+4,2,4);
  if (Number.isFinite(level)) {
   for (let i=0;i<4;i++) {
    pen.fillStyle=i<Math.ceil(level/25)?color:'#587064';
    pen.fillRect(x+3+5*i,y+3,4,6);
   }
   if(value.endsWith('+')) {
    pen.beginPath();pen.moveTo(x+14,y);pen.lineTo(x+8,y+7);pen.lineTo(x+12,y+7);
    pen.lineTo(x+10,y+12);pen.lineTo(x+17,y+5);pen.lineTo(x+13,y+5);pen.closePath();
    pen.strokeStyle='#20382e';pen.lineWidth=1.5;pen.stroke();pen.fillStyle='#ffe29c';pen.fill();
   }
  } else centered(value==='USB'?'USB':'?',{x,y,w:24,h:12},color,8);
 }
 function fullscreenIcon(b) {
  const x=Math.round(b.x+(b.w-16)/2),y=Math.round(b.y+(b.h-13)/2);
  for (const [color,width] of [['#193a31',4],['#faf2d7',2]]) {
   pen.beginPath();
   for (const [cx,cy,dx,dy] of [[x,y,1,1],[x+16,y,-1,1],[x,y+13,1,-1],[x+16,y+13,-1,-1]]) {
    pen.moveTo(cx+5*dx,cy);pen.lineTo(cx,cy);pen.lineTo(cx,cy+5*dy);
   }
   pen.lineWidth=width;pen.strokeStyle=color;pen.stroke();
  }
 }
 function input(el,b,style) {
  if (el.type==='checkbox') {
   roundedBox(b.x,b.y,b.w,b.h,3,el.checked?'#86ce9e':'#617d6d');
   if(el.checked) centered('✓',b,'#153528',12);
  } else if (el.type==='range') {
   const ratio=(el.valueAsNumber-Number(el.min))/(Number(el.max)-Number(el.min));
   roundedBox(b.x,b.y+b.h/2-2,b.w,4,2,'#698d7b');
   roundedBox(b.x+(b.w-12)*ratio,b.y+b.h/2-6,12,12,6,'#f1c485');
  } else {
   face(style);
   const x=b.x+px(style.paddingLeft)+1,y=b.y+b.h/2;
   pen.textBaseline='middle';
   pen.save();pen.beginPath();pen.rect(x,b.y,b.w-2*px(style.paddingLeft),b.h);pen.clip();
   const left=x-el.scrollLeft;
   if(el===document.activeElement) {
    const a=pen.measureText(el.value.slice(0,el.selectionStart)).width;
    const z=pen.measureText(el.value.slice(0,el.selectionEnd)).width;
    pen.fillStyle=z>a?'#526f60':'#fff0c7';pen.fillRect(left+a,y-7,Math.max(1,z-a),14);
    pen.fillStyle=style.color;
   }
   if(!el.value)pen.fillStyle='#bccdbe';
   pen.fillText(el.value||el.placeholder||'',left,y);pen.restore();
  }
 }
 function scrollbar(el,b) {
  if (el.scrollHeight<=el.clientHeight+1) return;
  const available=b.h-6,thumb=Math.max(12,available*el.clientHeight/el.scrollHeight);
  const top=(available-thumb)*el.scrollTop/(el.scrollHeight-el.clientHeight);
  roundedBox(b.x+b.w-4,b.y+3+top,2,thumb,1,'#8a9e8d');
 }
 function paintElement(el,clip,outline=false) {
  if(el.hidden || el.tagName==='SELECT' || el.classList.contains('sr-only')) return;
  const b=box(el.getBoundingClientRect());
  if(!b.w||!b.h||b.y>=clip.bottom||b.y+b.h<=clip.top) return;
  const style=getComputedStyle(el);
  if(style.visibility!=='visible') return;
  pen.save();pen.globalAlpha*=Number(style.opacity);
  if(el.id==='act')background(el,style,{x:b.x+3,y:b.y+6,w:b.w-6,h:b.h-12});
  else background(el,style,b);
  const scroll=style.overflowY==='auto'||style.overflowY==='scroll';
  if(scroll || style.overflow==='hidden') {
   pen.beginPath();pen.roundRect(b.x,b.y,b.w,b.h,px(style.borderTopLeftRadius));pen.clip();
   clip={top:Math.max(b.y,clip.top),bottom:Math.min(b.y+b.h,clip.bottom)};
  }
  if(el.id==='lcdPower') battery(b);
  else if(el.id==='fullscreen') fullscreenIcon(b);
  else if(el.id==='resume') centered('×',b,'#f5ca8a',24);
  else if(el.tagName==='INPUT') input(el,b,style);
  else if(el.tagName==='CANVAS') {pen.imageSmoothingEnabled=false;pen.drawImage(el,b.x,b.y,b.w,b.h);}
  else if(el.localName==='svg') {
   pen.translate(b.x,b.y);pen.scale(b.w/24,b.h/24);pen.strokeStyle=style.color;
   pen.lineWidth=Number(el.getAttribute('stroke-width'))||1.65;pen.lineCap='round';pen.lineJoin='round';
   for(const path of el.querySelectorAll('path'))pen.stroke(new Path2D(path.getAttribute('d')));
  } else {
   for(const child of el.childNodes) {
    if(child.nodeType===Node.TEXT_NODE && child.textContent.trim()) textNode(child,style,outline);
    else if(child.nodeType===Node.ELEMENT_NODE)paintElement(child,clip,outline);
   }
   const marker=el.matches('.routes button')?'›':el.matches('.lcd-select-wrap > button')?'▾':el.matches('[role=option][aria-selected=true]')?'✓':'';
   if(marker)centered(marker,{x:b.x+b.w-18,y:b.y,w:13,h:b.h},'#decaab',14);
   if(scroll)scrollbar(el,b);
  }
  pen.restore();
 }
 return function(context) {
  const state=[language,menu.open,$('rigHud').dataset.kit,ui.hasAttribute('data-casting-water'),$('act').hidden,$('spot').textContent,$('pondClock').textContent,$('simBattery').value,
   $('act').textContent,$('act').disabled,$('catchContinue').hidden,$('startSound').hidden,$('liveCrew').textContent].join('|');
  if(menuChanges.takeRecords().length || dirty || state!==previousState) {
   // Measure in native LCD coordinates even when the hit surface is projected
   // onto the angled 3D model. Restore its transform before the browser paints.
   const projection=ui.style.transform;
   try {
    ui.style.transform='none';origin=ui.getBoundingClientRect();
    pen.clearRect(0,0,480,320);
    const clip={top:0,bottom:320};
    paintElement(ui.querySelector('.lcd-hud'),clip,true);
    if(menu.open)paintElement(menu,clip);
    else {if(!ui.hasAttribute('data-casting-water'))paintElement(ui.querySelector('.lcd-actions'),clip);for(const el of [$('startSound'),$('liveCrew')])paintElement(el,clip);}
    previousState=state;dirty=false;
   } finally {ui.style.transform=projection;}
  }
  context.drawImage(layer,0,0);
 };
})();
