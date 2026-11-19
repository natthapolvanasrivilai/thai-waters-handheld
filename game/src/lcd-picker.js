// Keep choice lists on the LCD. The existing select elements remain the
// source of truth for saved settings, location filters and change handlers.
(()=>{
 const menu=document.getElementById('menu');
 const picker=document.createElement('div');
 picker.id='lcdPicker';picker.hidden=true;
 picker.setAttribute('role','dialog');picker.setAttribute('aria-labelledby','lcdPickerTitle');
 picker.innerHTML='<div class="menubar"><button type="button">Back</button><h2 id="lcdPickerTitle"></h2></div><div class="choice-list" role="listbox" aria-labelledby="lcdPickerTitle"></div>';
 menu.append(picker);
 const heading=picker.querySelector('h2'),list=picker.querySelector('.choice-list');
 const triggers=new Map();
 let current=null;

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
  current=select;heading.textContent=trigger.dataset.label;
  trigger.setAttribute('aria-expanded','true');
  const options=document.createDocumentFragment();
  for(const [index,option] of [...select.options].entries()){
   const row=document.createElement('button');
   row.type='button';row.textContent=option.text;row.dataset.index=String(index);
   row.setAttribute('role','option');row.setAttribute('aria-selected',String(option.selected));
   row.disabled=option.disabled;row.tabIndex=option.selected?0:-1;options.append(row);
  }
  list.replaceChildren(options);picker.hidden=false;
  const selected=list.querySelector('[aria-selected=true]')||list.firstElementChild;
  if(selected){selected.focus({preventScroll:true});list.scrollTop=Math.max(0,selected.offsetTop-list.offsetTop-6);}
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
   const back=picker.querySelector('.menubar button'),choice=rows.find(x=>x.tabIndex===0)||rows[0];
   e.preventDefault();(document.activeElement===back?choice:back)?.focus();return;
  }
  if(!['ArrowDown','ArrowUp','Home','End'].includes(e.key)||!rows.length)return;
  e.preventDefault();e.stopImmediatePropagation();
  const index=e.key==='Home'?0:e.key==='End'?rows.length-1:Math.max(0,Math.min(rows.length-1,at+(e.key==='ArrowDown'?1:-1)));
  for(const row of rows)row.tabIndex=-1;
  rows[index].tabIndex=0;rows[index].focus({preventScroll:true});
  const row=rows[index],top=row.offsetTop-list.offsetTop;
  if(top<list.scrollTop)list.scrollTop=top;
  else if(top+row.offsetHeight>list.scrollTop+list.clientHeight)list.scrollTop=top+row.offsetHeight-list.clientHeight;
 },true);
 menu.addEventListener('close',()=>closePicker(false));
 for(const select of menu.querySelectorAll('label > select')){
  const label=select.parentElement;
  const field=document.createElement('div'),caption=document.createElement('span'),wrap=document.createElement('span');
  field.className='lcd-choice';wrap.className='lcd-select-wrap';
  caption.textContent=[...label.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent.trim()).join(' ');
  const trigger=document.createElement('button');trigger.type='button';trigger.dataset.label=caption.textContent;
  trigger.setAttribute('aria-haspopup','listbox');trigger.setAttribute('aria-controls','lcdPicker');trigger.setAttribute('aria-expanded','false');
  trigger.onclick=()=>openPicker(select);
  trigger.onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();openPicker(select);}};
  select.setAttribute('aria-label',caption.textContent);select.setAttribute('aria-hidden','true');select.tabIndex=-1;
  field.hidden=label.hidden;label.replaceWith(field);field.append(caption,wrap);wrap.append(select,trigger);triggers.set(select,trigger);sync(select);
  select.addEventListener('change',()=>sync(select));
  new MutationObserver(()=>sync(select)).observe(select,{attributes:true,childList:true,subtree:true});
 }
 new MutationObserver(()=>{
  if(menu.open){for(const select of triggers.keys())sync(select);}else closePicker(false);
 }).observe(menu,{attributes:true,attributeFilter:['open']});
 menu.querySelectorAll('[data-section]').forEach(section=>{
  new MutationObserver(()=>{
   if(!section.hidden)for(const select of section.querySelectorAll('select'))sync(select);
  }).observe(section,{attributes:true,attributeFilter:['hidden']});
 });
})();
