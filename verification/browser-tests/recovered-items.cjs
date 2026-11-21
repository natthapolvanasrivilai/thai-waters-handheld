const {requireBootHome}=require('./boot-home-check.cjs');
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium,webkit}=require('playwright-core');
(async()=>{
 const browser=process.env.TEST_WEBKIT?await webkit.launch():await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try {
  const page=await browser.newPage({viewport:{width:844,height:390},hasTouch:true});
  const file=pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;
  await page.goto(file);
  const play=await requireBootHome(page);
  assert.equal(page.url(),file);
  assert.equal(await page.evaluate(()=>g.state()),0);
  await play.tap();
  await page.waitForFunction(()=>g&&!$('act').disabled);
  const result=await page.evaluate(()=>{
   const seen=new Set(),images=new Set(),captures=[];
   const paint=ctx.drawImage.bind(ctx);
   ctx.drawImage=function(image,...args){if(image===salvageSheet)captures.push(args.slice(0,4));return paint(image,...args)};
   try {
    for(let site=0;site<atlas.locations.length;site++)for(let seed=1;seed<=150;seed++){
     g.initialize(seed);g.place(site,0);placeId=site;
     const x=g.zoneX(3),y=g.zoneY(3);
     if(g.featureAt(x,y)!==3)continue;
     g.setAim(x,y);g.advance(16,1,0,0);g.advance(g.flightMs(),0,0,0);
     if(g.state()!==8||seen.has(g.junkId()))continue;
     const id=g.junkId(),item=salvageItems[id];
     captures.length=0;draw();if(captures.length)throw Error('Early reveal '+id);
     for(let i=0;i<25&&g.state()===8;i++)g.advance(100,0,0,.09);
     if(g.state()!==9)throw Error('Haul failed '+id);
     g.advance(5000,0,0,0);draw();
     if(captures.length!==1||String(captures[0])!==String([id%4*96,Math.floor(id/4)*50,96,50]))throw Error('Incorrect recovery image '+id);
     if(!$('message').textContent.includes(language==='th'?item.th:item.name)||g.pts()||g.catches())throw Error('Receipt or reward '+id);
     const c=document.createElement('canvas');c.width=96;c.height=50;
     const b=c.getContext('2d');b.drawImage(salvageSheet,...captures[0],0,0,96,50);
     const rgba=b.getImageData(0,0,96,50).data;
     if(!rgba.some((value,i)=>i%4===3&&value)||rgba[3]||rgba[rgba.length-1])throw Error('Sprite alpha '+id);
     images.add(c.toDataURL());seen.add(id);
    }
   }finally{ctx.drawImage=paint;}
   return [seen.size,images.size];
  });
  assert.deepEqual(result,[12,12]);
  console.log('PASS all 12 distinct transparent portraits through concealed contact, winding and landed display, with localized names and zero fish credit.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
