let bookOffset=0;
const bookSize=12;
function bookMatches(){
 const mode=$('bookFilter').selectedIndex,q=$('bookSearch').value.trim().toLowerCase(),matches=[];
 for(let i=0;i<atlas.fish.length;i++){
  const f=atlas.fish[i];
  if(mode===1 && !(i<52?f.site===locationId:f.spot===placeId))continue;
  if(mode===2&&!g.caught(i)||mode===3&&!f.fiction||mode===4&&f.tier!==5)continue;
  if(q && ![f.name,f.family,f.spot!=null?atlas.locations[f.spot]?.name:'',atlas.ranks[f.tier]].some(v=>v&&v.toLowerCase().includes(q)))continue;
  matches.push(i);
 }
 return matches;
}
function renderBook(){
 const matches=bookMatches(),pages=Math.max(1,Math.ceil(matches.length/bookSize));
 bookOffset=Math.max(0,Math.min(bookOffset,pages-1));
 const list=$('records');list.replaceChildren();
 for(const id of matches.slice(bookOffset*bookSize,(bookOffset+1)*bookSize)){
  const f=atlas.fish[id],n=g.caught(id),art=f.art??id;
  const item=document.createElement('div');item.id='species-'+id;item.tabIndex=-1;item.className='record '+(n?'found':'muted');
  const icon=document.createElement('canvas');icon.width=48;icon.height=25;icon.className='fish-thumb';icon.setAttribute('aria-hidden','true');
  const c=icon.getContext('2d');c.drawImage(fishSheet,(art%10)*96,Math.floor(art/10)*50,96,50,0,0,48,25);
  if(!n){c.globalCompositeOperation='source-in';c.fillStyle='#88a695';c.fillRect(0,0,48,25);}
  const title=document.createElement('b');title.textContent=f.name;
  const status=document.createElement('span');status.textContent=atlas.ranks[f.tier]+(f.fiction?' · Fictional':'')+' · '+(n?n+' caught · best '+g.best(id)+' cm':'Undiscovered');
  const tip=document.createElement('small');const mask=f.mask??(id===40?12:id===41?9:15);
  const lights=mask===15?'Any light':times.slice(0,4).filter((_,j)=>mask&(1<<j)).join(' / ');
  const water=f.spot!=null?atlas.locations[f.spot].name:atlas.sites[f.site][0]+' waters';
  tip.textContent=water+' · '+lights+' · '+baitTip(id);
  item.append(icon,title,status,tip);list.append(item);
 }
 $('bookPage').textContent=matches.length?'Page '+(bookOffset+1)+' / '+pages:'No matching species';
 $('bookPrev').disabled=!bookOffset;$('bookNext').disabled=bookOffset+1>=pages;
}
function showBookEntry(id){
 $('bookSearch').value='';$('bookFilter').selectedIndex=0;bookOffset=Math.floor(id/bookSize);renderBook();
}
function resetBook(){bookOffset=0;renderBook();}
$('bookFilter').onchange=$('bookSearch').oninput=resetBook;
$('bookPrev').onclick=()=>{bookOffset--;renderBook();$('records').scrollIntoView({block:'start'});};
$('bookNext').onclick=()=>{bookOffset++;renderBook();$('records').scrollIntoView({block:'start'});};
