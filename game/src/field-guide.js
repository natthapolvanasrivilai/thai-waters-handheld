let bookOffset=0;
let bookSize=8;
function sizeBook(){
 const next=parseInt(getComputedStyle($('lcdUI')).getPropertyValue('--touch'))>=60?4:8;
 if(next!==bookSize){const first=bookOffset*bookSize;bookSize=next;bookOffset=Math.floor(first/next);}
}
window.addEventListener('resize',()=>{if(g)renderBook();});
function bookMatches(){
 const mode=$('bookFilter').selectedIndex,q=$('bookSearch').value.trim().toLowerCase(),matches=[];
 for(let i=0;i<atlas.fish.length;i++){
  const f=atlas.fish[i];
  if(mode===1 && !(i<52?f.site===locationId:f.spot===placeId))continue;
  if(mode===5&&f.site===4||mode===6&&f.site!==4)continue;
  if(mode===2&&!g.caught(i)||mode===3&&!f.fiction||mode===4&&f.tier!==5)continue;
  const identity=g.caught(i)?[f.name,originalAtlas.fish[i].name,f.family,...(f.thaiSearchAliases??[])]:[];
  if(q && ![...identity,f.spot!=null?atlas.locations[f.spot]?.name:'',atlas.ranks[f.tier]].some(v=>v&&v.toLowerCase().includes(q)))continue;
  matches.push(i);
 }
 return matches;
}
let bookSpecies=null,historyPage=0;
const tierFrames=['#849a96','#6abd91','#ad87ef','#e494d3','#f3a366','#f6ce56'];
const journalPanel=document.querySelector('[data-section="book"]');
const iconShapes={
 back:'M14.5 5L7 12l7.5 7',next:'M9 5l7.5 7L9 19',
 dawn:'M2 17h20M5 21h14M7 17a5 5 0 0 1 10 0M12 12V3m-3 3 3-3 3 3',day:'M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0M12 1v3m0 16v3M1 12h3m16 0h3M4 4l2 2m12 12 2 2M20 4l-2 2M6 18l-2 2',
 dusk:'M2 17h20M5 21h14M7 17a5 5 0 0 1 10 0M12 2v8m-3-3 3 3 3-3',
 night:'M19.5 15.7A8.7 8.7 0 0 1 8.4 4a9 9 0 1 0 11.1 11.7Z',
 clear:'M16 9a4 4 0 1 1-8 0 4 4 0 0 1 8 0M12 1v2M4 4l2 2m12-1 2-2M2 10h3m14 0h3M3 19h18',
 rain:'M5 14a4 4 0 0 1 0-8 6 6 0 0 1 11-1 4.5 4.5 0 0 1 1 9ZM8 17l-1 3m7-3-1 3',
 heavy:'M5 13a4 4 0 0 1 0-8 6 6 0 0 1 11-1 4.5 4.5 0 0 1 1 9ZM6 16l-2 5m8-5-2 5m8-5-2 5',
 storm:'M6 14a4 4 0 0 1 0-8 6 6 0 0 1 11-1 4.5 4.5 0 0 1 1 9M13 11l-5 7h5l-2 5',
 pin:'M12 21s7-7.4 7-13a7 7 0 0 0-14 0c0 6 7 13 7 13ZM14.3 8a2.3 2.3 0 1 1-4.6 0 2.3 2.3 0 0 1 4.6 0',
 depth:'M5 4q2-2 4 0t4 0 4 0 4 0M12 8v12m-4-4 4 4 4-4',
 length:'M3 8h18v9H3zM7 8v4m4-4v3m4-3v4',
 mass:'M5 9h14l2 11H3zM15 7a3 3 0 1 0-6 0',
 bait:'M8 3v12a4 4 0 0 0 8 0v-4l-3 3',
 date:'M3 5h18v16H3zM3 10h18M7 3v4m10-4v4'
};
function journalIcon(name,label){
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg'),path=document.createElementNS(ns,'path');
 svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('width','18');svg.setAttribute('height','18');svg.setAttribute('fill','none');svg.setAttribute('stroke','currentColor');svg.setAttribute('stroke-width','1.8');svg.setAttribute('stroke-linecap','round');svg.setAttribute('stroke-linejoin','round');
 if(label){svg.setAttribute('role','img');svg.setAttribute('aria-label',label);const title=document.createElementNS(ns,'title');title.textContent=label;svg.append(title);}else svg.setAttribute('aria-hidden','true');
 path.setAttribute('d',iconShapes[name]);svg.append(path);return svg;
}
function fishPortrait(id,width,height){
 const icon=document.createElement('canvas');
 icon.width=width;icon.height=height;icon.className='fish-thumb';icon.setAttribute('aria-hidden','true');
 const c=icon.getContext('2d');c.imageSmoothingEnabled=false;drawSpecimen(c,id,0,0,width,height);
 if(!g.caught(id)){c.globalCompositeOperation='source-in';c.fillStyle='#adc4b3';c.fillRect(0,0,width,height);}
 return icon;
}
function bookText(tag,txt){const el=document.createElement(tag);el.textContent=txt;return el;}
function iconInfo(parent,icon,label,value){
 const el=document.createElement('span');el.className='book-info';el.title=label+(value?' · '+value:'');
 el.append(journalIcon(icon,label));if(value)el.append(bookText('span',value));parent.append(el);
}
const periodIcons=['dawn','day','dusk','night'],weatherIcons=['clear','rain','heavy','storm'],weatherLabels=['Clear','Light rain','Heavy rain','Storm'];
function collectionTotal(found){const count=found.toLocaleString(language)+' / '+atlas.fish.length.toLocaleString(language);return (language==='th'?'ทั่วไทย':'Thailand')+' · '+count;}
function renderBook(){
 sizeBook();
 const detail=$('bookDetail');detail.hidden=bookSpecies===null;journalPanel.classList.toggle('detail-open',!detail.hidden);
 if(bookSpecies!==null){renderBookDetail(bookSpecies);return;}
 const matches=bookMatches(),pages=Math.max(1,Math.ceil(matches.length/bookSize));
 bookOffset=Math.max(0,Math.min(bookOffset,pages-1));const fragment=document.createDocumentFragment();
 for(const id of matches.slice(bookOffset*bookSize,(bookOffset+1)*bookSize)){
  const f=atlas.fish[id],n=g.caught(id),tile=document.createElement('button');tile.type='button';tile.id='species-'+id;tile.className='record '+(n?'found':'unseen');
  const knownName=f.scientificName ? f.name+' · '+f.scientificName : f.name;
  tile.style.borderColor=tierFrames[f.tier];tile.style.borderStyle='solid';tile.title=(n?knownName:L('Undiscovered'))+' · '+atlas.ranks[f.tier];tile.setAttribute('aria-label',tile.title);
  tile.append(fishPortrait(id,72,38));if(n){
   tile.append(bookText('b',f.name));
   if(f.scientificName && f.thaiNameKind!=='species')tile.append(bookText('small',f.scientificName));
   const mark=bookText('span','✓');mark.className='caught-mark';tile.append(mark);
  }
  tile.onclick=()=>{bookSpecies=id;historyPage=0;renderBook();$('bookDetail').focus({preventScroll:true});};fragment.append(tile);
 }
 $('records').replaceChildren(fragment);
 setUi($('bookPage'),matches.length?(bookOffset+1)+' / '+pages+' · '+matches.length.toLocaleString(language)+' '+L('species'):'No matching species');
 $('bookPrev').disabled=!bookOffset;$('bookNext').disabled=bookOffset+1>=pages;
}
function renderBookDetail(id){
 const f=atlas.fish[id],detail=$('bookDetail'),n=g.caught(id);detail.tabIndex=-1;
 const info=document.createElement('div');info.className='book-profile';
 const picture=fishPortrait(id,144,75);if(n)enhanceCollectedPortrait(picture,id);picture.style.borderColor=tierFrames[f.tier];const title=bookText('div','');
 const tier=bookText('small',atlas.ranks[f.tier]+(f.fiction?' · '+L('Fictional'):''));tier.style.color=tierFrames[f.tier];
 title.append(tier,bookText('h2',n?f.name:L('Undiscovered')));
 if(n&&f.scientificName)title.append(bookText('small',f.scientificName));
 if(n&&f.family)title.append(bookText('small',f.family));
 if(n&&!g.hasPortrait(id))title.append(bookText('small',language==='th'?'อยู่ระหว่างวาดภาพประจำชนิด':'Species illustration pending'));
 const water=f.spot!=null?atlas.locations[f.spot].name:atlas.sites[f.site][0],habitat=document.createElement('div');habitat.className='book-facts';
 iconInfo(habitat,'pin',L('Origin'),water);iconInfo(habitat,'bait',L('Hook bait'),baitTip(id));
 const mask=f.mask??(id===40?12:id===41?9:15);periodIcons.forEach((icon,i)=>{if(mask&(1<<i))iconInfo(habitat,icon,L(times[i]));});
 title.append(habitat);info.append(picture,title);
 const heading=bookText('h3',(language==='th'?'ประวัติการจับ':'Catch history')+' · '+n);
 detail.replaceChildren(info);if(n&&f.lore)detail.append(bookText('p',f.lore));detail.append(heading);
 const rows=catchHistory.filter(c=>c.id===id).reverse(),per=1;
 for(const c of rows.slice(historyPage*per,(historyPage+1)*per)){
  const row=document.createElement('div');row.className='catch-log';
  if(Number.isFinite(c.at))iconInfo(row,'date',language==='th'?'เวลาประเทศไทย':'Bangkok time',new Intl.DateTimeFormat(language==='th'?'th-TH':'en-GB',{timeZone:'Asia/Bangkok',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(c.at));
  if(atlas.locations[c.place])iconInfo(row,'pin',L('Origin'),atlas.locations[c.place].name);
  if(periodIcons[c.period])iconInfo(row,periodIcons[c.period],L(times[c.period]));
  if(weatherIcons[c.weather])iconInfo(row,weatherIcons[c.weather],L(weatherLabels[c.weather]));
  iconInfo(row,'length',L(readEngineText(g.measurement(id,c.cm))),L(c.cm+' cm'));iconInfo(row,'mass',L('EST. WEIGHT'),L(displayMass(c.grams)));
  if(Number.isInteger(c.bait)&&c.bait>=0&&c.bait<18){iconInfo(row,'bait',L('Hook bait'),$('hookBait').options[c.bait%6].text);iconInfo(row,'depth',L('Fishing depth'),$('baitDepth').options[Math.floor(c.bait/6)].text);}
  detail.append(row);
 }
 if(!n)detail.append(bookText('p',language==='th'?'ยังไม่เคยจับได้':'No catches yet.'));
 if(n>rows.length)detail.append(bookText('p',language==='th'?'บันทึกเดิม '+(n-rows.length)+' ครั้ง · ยาวที่สุด '+g.best(id)+' ซม.':'Earlier catches without trip details: '+(n-rows.length)+' · Best '+g.best(id)+' cm'));
 if(rows.length>per){const nav=document.createElement('div');nav.className='history-nav';for(const [dir,label] of [[-1,'Previous'],[1,'Next']]){
  const b=document.createElement('button');b.type='button';b.setAttribute('aria-label',L(label));b.append(journalIcon(dir<0?'back':'next'));b.disabled=historyPage+dir<0||(historyPage+dir)*per>=rows.length;b.onclick=()=>{historyPage+=dir;renderBookDetail(id);};nav.append(b);
 }detail.append(nav);}
}
function closeBookDetail(){const id=bookSpecies;bookSpecies=null;renderBook();$('species-'+id)?.focus({preventScroll:true});}
function showBookEntry(id){$('bookSearch').value='';$('bookFilter').selectedIndex=0;bookOffset=Math.floor(id/bookSize);bookSpecies=id;historyPage=0;renderBook();}
function resetBook(){bookOffset=0;bookSpecies=null;renderBook();}
$('bookFilter').onchange=$('bookSearch').oninput=resetBook;
$('bookPrev').onclick=()=>{bookOffset--;renderBook();};
$('bookNext').onclick=()=>{bookOffset++;renderBook();};

// Turn the list by page or the open profile by species, keeping active filters.
function turnBook(direction){
 if(bookSpecies===null){
  const button=$(direction<0?'bookPrev':'bookNext');
  if(!button.disabled)button.click();
  return;
 }
 const matches=bookMatches(),index=matches.indexOf(bookSpecies),next=index+direction;
 if(index<0||next<0||next>=matches.length)return;
 bookOffset=Math.floor(next/bookSize);bookSpecies=matches[next];historyPage=0;
 renderBook();$('bookDetail').focus({preventScroll:true});
}

// Track on the content only. Preserve vertical scroll, pinch, and ordinary taps.
let bookSwipe=null,bookSwipeClick=null;
const activeBook=()=>menu.open&&menuPage==='book';
window.addEventListener('pointerdown',e=>{
 if(bookSwipe&&e.pointerId!==bookSwipe.id)bookSwipe=null;
 if(e.isPrimary)bookSwipeClick=null;
},true);
for(const surface of [$('records'),$('bookDetail')]){
 surface.style.touchAction='pan-y pinch-zoom';
 surface.addEventListener('pointerdown',e=>{
  if(!activeBook()||!e.isPrimary||e.button!==0||
    e.target.closest('input,select,textarea,a,[contenteditable],#bookDetail button'))return;
  bookSwipe={id:e.pointerId,x:e.clientX,y:e.clientY,entry:bookSpecies};
 });
}
window.addEventListener('pointercancel',e=>{if(bookSwipe?.id===e.pointerId)bookSwipe=null;});
window.addEventListener('pointerup',e=>{
 if(bookSwipe?.id!==e.pointerId)return;
 const start=bookSwipe;bookSwipe=null;
 const dx=e.clientX-start.x,dy=e.clientY-start.y;
 if(!activeBook()||start.entry!==bookSpecies||Math.abs(dx)<44||Math.abs(dx)<1.5*Math.abs(dy))return;
 // Replacing tiles can retarget a synthesized click; capture it at window level.
 bookSwipeClick={id:e.pointerId,x:e.clientX,y:e.clientY,until:performance.now()+450};
 e.preventDefault();
 turnBook(dx<0?1:-1);
});
window.addEventListener('click',e=>{
 if(!bookSwipeClick||!e.detail||!activeBook())return;
 const {id,x,y,until}=bookSwipeClick;
 if(performance.now()>until)return;
 if(e.pointerId>0&&e.pointerId!==id)return;
 if(Math.hypot(e.clientX-x,e.clientY-y)>24)return;
 bookSwipeClick=null;e.preventDefault();e.stopImmediatePropagation();
},true);

// Chromium can deliver the complete first Back touch after a profile swipe
// without synthesizing a click. Recognize just that native button tap; retain
// the normal click path for mouse, keyboard and accessibility activation.
{
 const back=$('back'),radius=12;
 let contact=null,completed=null;
 const within=(e,start)=>Math.hypot(e.clientX-start.x,e.clientY-start.y)<=radius;
 const hitsBack=e=>document.elementFromPoint(e.clientX,e.clientY)?.closest('button')===back;
 window.addEventListener('pointerdown',e=>{
  if(e.isPrimary)completed=null;
  if(contact){contact=null;return;}
  if(e.isTrusted&&e.pointerType==='touch'&&e.isPrimary&&e.button===0&&activeBook()&&
    bookSpecies!==null&&!back.disabled&&e.target.closest?.('button')===back&&hitsBack(e))
   contact={id:e.pointerId,x:e.clientX,y:e.clientY,entry:bookSpecies};
 },true);
 window.addEventListener('pointermove',e=>{
  if(contact?.id===e.pointerId&&!within(e,contact))contact=null;
 },true);
 for(const type of ['pointercancel','lostpointercapture'])window.addEventListener(type,e=>{
  if(contact?.id===e.pointerId)contact=null;
 },true);
 window.addEventListener('pointerup',e=>{
  if(contact?.id!==e.pointerId)return;
  const start=contact;contact=null;
  if(!e.isTrusted||e.pointerType!=='touch'||!e.isPrimary||!activeBook()||
    start.entry!==bookSpecies||back.disabled||!within(e,start)||!hitsBack(e))return;
  completed={id:e.pointerId,x:e.clientX,y:e.clientY,until:performance.now()+500};
  closeBookDetail();
 },true);
 back.addEventListener('click',e=>{
  const tap=completed;
  if(!tap||!e.isTrusted||!e.detail||performance.now()>tap.until||!within(e,tap))return;
  if(e.pointerType==='touch'?e.pointerId!==tap.id:
    Boolean(e.pointerType)||!e.sourceCapabilities?.firesTouchEvents)return;
  completed=null;e.preventDefault();e.stopImmediatePropagation();
 },true);
}
