// Keep choice lists on the LCD. The existing select elements remain the
// source of truth for saved settings, location filters and change handlers.
(()=>{
 const menu=document.getElementById('menu');
 const picker=document.createElement('div');
 picker.id='lcdPicker';picker.hidden=true;
 picker.setAttribute('role','dialog');picker.setAttribute('aria-labelledby','lcdPickerTitle');
 picker.innerHTML='<div class="menubar"><button type="button" data-navicon="back" aria-label="Back" title="Back"></button><h2 id="lcdPickerTitle"></h2></div><div class="choice-list" role="listbox" aria-labelledby="lcdPickerTitle"></div>';
 menu.append(picker);
 const heading=picker.querySelector('h2'),list=picker.querySelector('.choice-list');
 const triggers=new Map();
 let current=null,offset=0;
 const pageSize=6,nav=picker.querySelector('.menubar');
 const prev=document.createElement('button'),next=document.createElement('button'),number=document.createElement('small');
 for(const [b,icon,dir] of [[prev,'back',-1],[next,'next',1]]){
  b.type='button';b.dataset.navicon=icon;b.onclick=()=>showOptions(offset+dir);nav.append(b);
 }
 nav.insertBefore(number,next);
 function showOptions(page,focusIndex){
  if(!current)return;
  const select=current,count=Math.ceil(select.options.length/pageSize);
  offset=Math.max(0,Math.min(page,count-1));prev.hidden=next.hidden=number.hidden=count<2;
  prev.disabled=offset===0;next.disabled=offset===count-1;
  prev.setAttribute('aria-label',L('Previous'));next.setAttribute('aria-label',L('Next'));
  number.textContent=(offset+1)+'/'+count;
  const options=document.createDocumentFragment();
  for(let index=offset*pageSize;index<Math.min(select.options.length,(offset+1)*pageSize);index++){
   const option=select.options[index];
   const row=document.createElement('button');
   row.type='button';row.textContent=option.text;row.dataset.index=String(index);
   if(select.id==='hookBait'){
    const icon=document.createElement('canvas');icon.width=48;icon.height=30;icon.setAttribute('aria-hidden','true');
    const label=document.createElement('span');label.textContent=index===2?L('Rum rice bran'):option.text;
    row.classList.add('bait-option');row.replaceChildren(icon,label);drawBait(icon,index);
   }
   row.setAttribute('role','option');row.setAttribute('aria-selected',String(option.selected));
   row.disabled=option.disabled;row.tabIndex=option.selected?0:-1;options.append(row);
  }
  list.replaceChildren(options);
  const target=list.querySelector('[data-index="'+focusIndex+'"]')||list.querySelector('[aria-selected=true]')||list.firstElementChild;
  if(target){target.tabIndex=0;target.focus({preventScroll:true});}
 }

 function sync(select){
  const button=triggers.get(select);
  const value=select.selectedOptions[0]?.text || 'No choices';
  button.textContent=value;
  button.setAttribute('aria-label',button.dataset.label+' · '+value);
  button.disabled=select.disabled||!select.options.length;
 }
 function closePicker(focus=true){
  if(!current)return;
  const trigger=triggers.get(current);
  current=null;picker.hidden=true;
  trigger.setAttribute('aria-expanded','false');
  if(focus&&menu.open&&!trigger.disabled)trigger.focus({preventScroll:true});
 }
 function openPicker(select){
  const trigger=triggers.get(select);
  if(trigger.disabled)return;
  current=select;picker.dataset.field=select.id;heading.textContent=trigger.dataset.label;
  trigger.setAttribute('aria-expanded','true');
  picker.hidden=false;showOptions(Math.floor(select.selectedIndex/pageSize),select.selectedIndex);
 }
 list.onclick=e=>{
  const row=e.target.closest('[role=option]');
  if(!row||!current)return;
  const select=current;
  select.selectedIndex=Number(row.dataset.index);
  closePicker();
  select.dispatchEvent(new Event('input',{bubbles:true}));
  select.dispatchEvent(new Event('change',{bubbles:true}));sync(select);
 };
 picker.querySelector('.menubar button').onclick=()=>closePicker();
 menu.addEventListener('keydown',e=>{
  if(!current)return;
  if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();closePicker();return;}
  const rows=[...list.querySelectorAll('button:enabled')],at=rows.indexOf(document.activeElement);
  if(e.key==='Tab'){
   const targets=[...picker.querySelectorAll('button:not(:disabled):not([hidden])')].filter(b=>b.closest('.menubar')||b.tabIndex===0);
   const at=targets.indexOf(document.activeElement);e.preventDefault();targets[(at+(e.shiftKey?-1:1)+targets.length)%targets.length]?.focus();return;
  }
  if(!['ArrowDown','ArrowUp','Home','End','PageDown','PageUp'].includes(e.key)||!rows.length)return;
  e.preventDefault();e.stopImmediatePropagation();
  const index=Number(rows[at]?.dataset.index??offset*pageSize);
  const dest=e.key==='Home'?0:e.key==='End'?current.options.length-1:index+({ArrowDown:1,ArrowUp:-1,PageDown:pageSize,PageUp:-pageSize}[e.key]);
  const target=Math.max(0,Math.min(current.options.length-1,dest));showOptions(Math.floor(target/pageSize),target);
 },true);
 menu.addEventListener('close',()=>closePicker(false));
 for(const select of menu.querySelectorAll('label > select')){
  const label=select.parentElement;
  const field=document.createElement('div'),caption=document.createElement('span'),wrap=document.createElement('span');
  field.className='lcd-choice';wrap.className='lcd-select-wrap';
  caption.textContent=[...label.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent.trim()).join(' ');
  const trigger=document.createElement('button');trigger.type='button';trigger.dataset.label=caption.textContent;caption.dataset.choiceCaption=caption.textContent;
  trigger.setAttribute('aria-haspopup','listbox');trigger.setAttribute('aria-controls','lcdPicker');trigger.setAttribute('aria-expanded','false');
  trigger.onclick=()=>openPicker(select);
  trigger.onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();openPicker(select);}};
  select.setAttribute('aria-label',caption.textContent);select.setAttribute('aria-hidden','true');select.tabIndex=-1;
  field.hidden=label.hidden;label.replaceWith(field);field.append(caption,wrap);wrap.append(select,trigger);triggers.set(select,trigger);sync(select);
  select.addEventListener('change',()=>sync(select));
  new MutationObserver(()=>sync(select)).observe(select,{attributes:true,childList:true,subtree:true});
 }
 document.addEventListener('game-language',()=>{
  const back=picker.querySelector('.menubar button');back.title=L('Back');back.setAttribute('aria-label',L('Back'));closePicker(false);
  for(const [select,button] of triggers){
   const caption=button.closest('.lcd-choice').querySelector('[data-choice-caption]');
   caption.textContent=L(caption.dataset.choiceCaption);button.dataset.label=caption.textContent;
   select.setAttribute('aria-label',caption.textContent);sync(select);
  }
 });
 new MutationObserver(()=>{
  if(menu.open){for(const select of triggers.keys())sync(select);}else closePicker(false);
 }).observe(menu,{attributes:true,attributeFilter:['open']});
 menu.querySelectorAll('[data-section]').forEach(section=>{
  new MutationObserver(()=>{
   if(!section.hidden)for(const select of section.querySelectorAll('select'))sync(select);
  }).observe(section,{attributes:true,attributeFilter:['hidden']});
 });
})();
