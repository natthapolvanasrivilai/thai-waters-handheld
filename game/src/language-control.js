function applyLanguage(next){
 language=next;document.documentElement.lang=next;
 document.title=next==='th'?'Thai Waters • ตกปลา':'Thai Waters • Play';
 chooseAtlas();
 for(const [node,english] of staticText)if(node.isConnected)node.data=L(english);
 for(const [el,key,english] of staticAttrs)if(el.isConnected)el.setAttribute(key,L(english));
 for(const el of document.querySelectorAll('main *')){
  if(updates.has(el))setUi(el,updates.get(el));
 }
 for(const b of document.querySelectorAll('[data-language]'))b.setAttribute('aria-pressed',String(b.dataset.language===next));
 if(sessionOnly)$('sessionCareerNotice').textContent=sessionCareerWords();
 document.dispatchEvent(new Event('game-language'));
 if(g){lastLabel='';refresh();if(menu.open)section(menuPage);draw();}
}
for(const button of document.querySelectorAll('[data-language]')){
 button.onclick=()=>{if(!sessionOnly)try{localStorage.setItem(languageKey,button.dataset.language);}catch{}applyLanguage(button.dataset.language);};
}
applyLanguage(language);
