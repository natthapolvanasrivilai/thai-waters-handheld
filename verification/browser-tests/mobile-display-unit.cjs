const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const source=fs.readFileSync(path.join(__dirname,'..','..','game','src','mobile-display.js'),'utf8');
function fixture(mode='native',touch=true) {
  const elements={},listeners={},classes=new Set(),root={
    lang:'en',toggleAttribute(k,v){this[k]=v;},classList:{toggle(k,v){v?classes.add(k):classes.delete(k);},contains:k=>classes.has(k)}
  };
  const $=id=>elements[id]??={setAttribute(k,v){this[k]=v;}};
  const doc={documentElement:root,addEventListener(k,v){listeners[k]=v;}};
  let calls=0,requested,sectionChosen,focused=false;
  if(mode!=='unsupported')root.requestFullscreen=async()=>{calls++;if(mode==='denied')throw Error('blocked');doc.fullscreenElement=root;listeners.fullscreenchange();};
  doc.exitFullscreen=async()=>{doc.fullscreenElement=null;listeners.fullscreenchange();};
  const menu={open:false};
  $('openMenu').click=()=>{menu.open=true;};
  $('enableMotion').focus=()=>{focused=true;};
  const mq={matches:touch,addEventListener(k,v){requested=v;}};
  vm.runInNewContext(source,{$,menu,document:doc,navigator:{maxTouchPoints:touch?1:0},matchMedia:()=>mq,
    L:s=>s,requestAnimationFrame:fn=>fn(),fitFlat(){},product:{hidden:true},section:s=>sectionChosen=s});
  return {$: $,root,calls:()=>calls,rotate:()=>requested(),listeners,chosen:()=>sectionChosen,isFocused:()=>focused};
}
(async()=>{
  const a=fixture();
  assert.equal(a.root.classList.contains('immersive'),true);
  assert.equal(a.calls(),0);
  assert.ok(!a.listeners.pointerup,'no gameplay gesture changes fullscreen');
  a.rotate();
  assert.equal(a.root.classList.contains('immersive'),true);
  assert.equal(a.calls(),0);
  await a.$('mobileFullscreen').onclick();
  assert.equal(a.calls(),1);
  assert.equal(a.$('mobileFullscreen').textContent,'Exit fullscreen');
  await a.$('mobileFullscreen').onclick();
  assert.equal(a.root.classList.contains('immersive'),false);
  a.$('motionShortcut').onclick();
  assert.equal(a.chosen(),'sensors');
  assert.equal(a.isFocused(),true);
  for(const mode of ['unsupported','denied']){
    const b=fixture(mode);
    if(mode==='denied')await b.$('mobileFullscreen').onclick();
    assert.equal(b.root.classList.contains('immersive'),true);
    assert.equal(b.$('displayModeNote').hidden,false);
    assert.equal(b.$('mobileFullscreen').textContent,'Exit screen fill');
    await b.$('mobileFullscreen').onclick();
    assert.equal(b.root.classList.contains('immersive'),false);
    await b.$('mobileFullscreen').onclick();
    assert.equal(b.root.classList.contains('immersive'),true);
    assert.equal(b.calls(),mode==='denied'?1:0);
  }
  assert.equal(fixture('native',false).root.classList.contains('immersive'),false);
  console.log('PASS phone viewport fill, explicit native fullscreen, denial/unsupported fallback, motion shortcut');
})().catch(e=>{console.error(e);process.exitCode=1;});
