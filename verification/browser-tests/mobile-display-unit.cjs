const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const js=fs.readFileSync(process.argv[2]||path.resolve(__dirname,'../../game/src/mobile-display.js'),'utf8');
function fake({ios=false,standalone=false,enabled=false,deny=false}={}){
 const events={};const values={};let req=0;let trap=0;let overlay=0;let selected;const menu={open:false};
 function node(){const attrs={};return {dataset:{},hidden:false,open:false,isConnected:true,
  addEventListener:(ev,fn)=>{},removeAttribute:k=>delete attrs[k],setAttribute:(k,v)=>attrs[k]=v,
  getAttribute:k=>attrs[k],focus:()=>{trap++},showModal(){this.open=true;overlay++},close(){this.open=false;events['dialog.close']?.({})},
  querySelector:()=>null,classList:{values:new Set,toggle(key,on){on?this.values.add(key):this.values.delete(key)},contains(key){return this.values.has(key)}}
 };}
 const root=node(),shop=node(); const doc={documentElement:root,fullscreenEnabled:enabled,fullscreenElement:null,
   querySelector:()=>shop,addEventListener:(e,fn)=>events[e]=fn,
   exitFullscreen(){doc.fullscreenElement=null; events.fullscreenchange();return Promise.resolve();}
 };
 shop.addEventListener=(e,fn)=>events[e]=fn;
 root.toggleAttribute=(k,v)=>void(values[k]=v);
 root.requestFullscreen=function(){req++;return deny?Promise.reject(new Error('policy')):Promise.resolve().then(()=>{doc.fullscreenElement=root;events.fullscreenchange();});}
 const nodes=new Map;
 function $(id){if(!nodes.has(id)){let n=node();if(id==='displayHelp')n.addEventListener=(e,fn)=>events['dialog.'+e]=fn;nodes.set(id,n)}return nodes.get(id);}
 const mb=$('mobileFullscreen');
 $('openMenu').click=()=>{menu.open=true;};
 vm.runInNewContext(js,{document:doc,window:{visualViewport:{addEventListener:()=>{}}},
  navigator:{standalone,userAgent:ios?'iPhone':'Firefox',platform:'Linux',maxTouchPoints:ios?5:0},
  matchMedia:q=>({matches:false,addEventListener:(e,fn)=>events[q]=fn}),$,L:x=>x,
  menu,section:name=>{selected=name;},
  fitFlat(){},product:{hidden:true},requestAnimationFrame:fn=>fn(),physicalView:null});
 return {root,doc,$,events,values,mb,requests:()=>req,focus:()=>trap,chosen:()=>selected,
  control:(id,gesture=true)=>$(id).onclick({isTrusted:gesture,currentTarget:$(id)})}
}
(async()=>{
const safari=fake({ios:true});
assert.equal(safari.root.dataset.displayMode,'fit');
assert.equal(safari.requests(),0);
assert.equal(safari.mb.getAttribute('aria-haspopup'),'dialog');
await safari.control('mobileFullscreen');
assert(safari.$('displayHelp').open);
assert.match(safari.$('displayHelpText').textContent,/Add to Home Screen.*Open as Web App/);
assert.equal(safari.requests(),0);
safari.$('displayHelpClose').onclick();assert(!safari.$('displayHelp').open && safari.focus()===1);
await safari.control('fullscreen');safari.$('displayHelpWindow').onclick();
assert.equal(safari.root.dataset.displayMode,'window');
await safari.control('fullscreen');safari.$('displayHelpWindow').onclick();
assert.equal(safari.root.dataset.displayMode,'fit');
for(const [type,edit,want] of [['contextmenu',false,true],['contextmenu',true,false],['selectstart',false,true],['selectstart',true,false]]){
 let p=false;
 safari.events[type]({type,pointerType:'touch',target:{closest:()=>edit},preventDefault(){p=true;}});
 assert.equal(p,want);
}
assert.equal(safari.events.pointerup,undefined,'Gameplay pointerup never activates fullscreen');
safari.events['(orientation: landscape)']();assert.equal(safari.root.dataset.displayMode,'fit');
for(const [button,firesTouchEvents,expect] of [[2,false,true],[0,true,true],[0,false,false]]){
 let cancelled=false;
 safari.events.contextmenu({type:'contextmenu',button,sourceCapabilities:{firesTouchEvents},target:{closest:()=>null},preventDefault(){cancelled=true;}});
 assert.equal(cancelled,expect);
}
safari.$('motionShortcut').onclick();assert.equal(safari.chosen(),'sensors');
const home=fake({ios:true,standalone:true});
assert.equal(home.root.dataset.displayMode,'standalone');
await home.control('fullscreen');assert.equal(home.root.dataset.displayMode,'window');
assert(!home.$('displayHelp').open && home.requests()===0);
const chrom=fake({enabled:true});
assert.equal(chrom.root.dataset.displayMode,'window');
await chrom.control('fullscreen',false);assert.equal(chrom.requests(),0);
await chrom.control('fullscreen',true);assert.equal(chrom.requests(),1);assert.equal(chrom.root.dataset.displayMode,'native');
await chrom.control('fullscreen',true);assert.equal(chrom.root.dataset.displayMode,'window');
const restricted=fake({enabled:true,deny:true});
await restricted.control('fullscreen');assert.equal(restricted.requests(),1);assert.equal(restricted.root.dataset.displayMode,'fit');
assert.match(restricted.$('displayModeNote').textContent,/bars may remain/);
await restricted.control('fullscreen');assert.equal(restricted.requests(),1);assert.equal(restricted.root.dataset.displayMode,'window');
console.log('PASS no fullscreen on load/synthetic click, native user gesture + exit, denied capability CSS fallback, iPhone Home Screen dialog open/close and focus restore, standalone, scoped editable touches.')

})().catch(e=>{console.error(e);process.exitCode=1});
