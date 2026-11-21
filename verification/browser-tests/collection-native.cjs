/* Export game pixels, not a screenshot of the browser stage. Synthetic fixture only. */
const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path');
const {createHash}=require('node:crypto'),{pathToFileURL}=require('node:url');
const input=path.resolve(process.env.NATIVE_HTML||path.join(__dirname,'../../game/Thai-Waters-play.html'));
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const htmlSHA256=digest(fs.readFileSync(input));
if(process.env.NATIVE_HTML_SHA256)assert.equal(htmlSHA256,process.env.NATIVE_HTML_SHA256,'Candidate HTML differs from verified bundle');
if(process.env.SOURCE_SHA)assert.match(process.env.SOURCE_SHA,/^[0-9a-f]{40}$/,'Expected full source revision');
const signature=Buffer.from('89504e470d0a1a0a','hex');
function verifyPng(bytes){
 assert(bytes.subarray(0,8).equals(signature));
 assert.equal(bytes.toString('ascii',12,16),'IHDR');
 assert.deepEqual([bytes.readUInt32BE(16),bytes.readUInt32BE(20)],[480,320]);
}
if(require.main===module && process.argv.includes('--check-input')){
 console.log('PASS exact candidate SHA-256',htmlSHA256);
}else if(require.main===module){
 main().catch(e=>{console.error(e);process.exitCode=1});
}
module.exports={verifyPng,htmlSHA256};

async function main(){
 const {chromium,webkit}=require('playwright-core');
 const runner=process.env.TEST_WEBKIT?webkit:chromium;
 const executablePath=process.env.BROWSER_PATH||(process.env.TEST_WEBKIT?undefined:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe');
 const browser=await runner.launch({executablePath});
 const out=process.env.NATIVE_OUT?path.resolve(process.env.NATIVE_OUT):null;
 const images=[];
 try{
  if(out)fs.mkdirSync(out,{recursive:true});
  let ids;
  for(const lang of ['th','en']){
   // Independent ephemeral contexts; no auth, real career or protected file reads.
   const context=await browser.newContext({viewport:{width:960,height:720},deviceScaleFactor:1});
   try{
    const page=await context.newPage(),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(pathToFileURL(input).href);
    await page.waitForFunction(()=>typeof g!=='undefined'&&g&&!$('act').disabled);
    await page.locator('#openMenu').click();
    await page.locator('[data-language='+lang+']').click();
    await page.waitForFunction(value=>document.documentElement.lang===value,lang);
    if(!ids)ids=await page.evaluate(()=>{
     // Three fixed catalog ranges. Ensure a longest Thai display label with a diacritic is on the middle page.
     const n=atlas.fish.length;
     const midCandidates=atlas.fish.map((f,i)=>({f,i})).slice(Math.floor(n/3),Math.floor(2*n/3));
     const long=midCandidates.filter(({f})=>/[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e]/.test(f.name))
      .sort((a,b)=>b.f.name.length-a.f.name.length||a.i-b.i)[0].i;
     const middle=Math.min(Math.max(8,long-3),n-16);
     return [...Array.from({length:8},(_,i)=>i),...Array.from({length:8},(_,i)=>i+middle),...Array.from({length:8},(_,i)=>n-8+i)];
    });
    await page.evaluate(fish=>{
     assertSyntheticPage(fish);
     function assertSyntheticPage(list){if(list.some(i=>g.caught(i)))throw Error('Fixture requires a fresh collection');}
     for(const i of fish)g.restoreEntry(i,1,atlas.fish[i].low);
    },ids);
    await page.locator('#resume').click();
    const closed=await page.evaluate(async()=>{
     await document.fonts.ready;
     await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
     const canvas=$('scene'),rgb=canvas.getContext('2d').getImageData(0,0,480,320).data;
     let menuPalette=0,cardPalette=0;
     for(let i=0;i<rgb.length;i+=4){
      if(rgb[i]===21&&rgb[i+1]===47&&rgb[i+2]===42)menuPalette++;
      if(rgb[i]===41&&rgb[i+1]===70&&rgb[i+2]===62)cardPalette++;
     }
     return {menuPalette,cardPalette,png:canvas.toDataURL('image/png').split(',')[1]};
    });
    await page.locator('#openMenu').click();
    await page.locator('[data-to=book]').click();

    async function capture(name,kind,expectedIds){
     const frame=await page.evaluate(async kind=>{
      const menu=document.getElementById('menu'),canvas=document.getElementById('scene');
      // FontFaceSet waits for layout-driven font requests. Proactively request each
      // currently painted game face against the actual label, then await ready again.
      const elements=[...menu.querySelectorAll('#menuTitle,#records b,#records small,#bookFindHeading,#bookDetail h2')].filter(el=>el.getClientRects().length);
      await Promise.all(elements.map(el=>{
       const s=getComputedStyle(el);
       return document.fonts.load(s.fontStyle+' '+s.fontWeight+' '+s.fontSize+' '+s.fontFamily,el.textContent);
      }));
      await document.fonts.ready;
      await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
      const visible=el=>!!(el.getClientRects().length);
      const rgb=canvas.getContext('2d').getImageData(0,0,480,320).data;
      let paintedMenu=0,paintedCards=0;
      for(let i=0;i<rgb.length;i+=4){
       if(rgb[i]===21&&rgb[i+1]===47&&rgb[i+2]===42)paintedMenu++;
       if(rgb[i]===41&&rgb[i+1]===70&&rgb[i+2]===62)paintedCards++;
      }
      const records=document.getElementById('records'),tiles=[...records.children];
      const tileIds=tiles.map(el=>+el.id.slice('species-'.length));
      const labelFits=el=>{
       const range=document.createRange();range.selectNodeContents(el);
       const text=range.getBoundingClientRect(),box=el.getBoundingClientRect();
       return text.width>0&&text.height>0&&text.bottom<=box.bottom+1&&text.left>=box.left-1&&text.right<=box.right+1;
      };
      // Measure actual light glyph pixels inside each primary-name range,
      // in the same unprojected coordinate system as paintLcdInterface.
      const labelsPainted=[];
      if(kind==='grid'){
       const ui=$('lcdUI'),projection=ui.style.transform;
       try{
        ui.style.transform='none';const base=ui.getBoundingClientRect();
        for(const tile of tiles){
         const label=tile.querySelector('b'),sample={label:label?.textContent||'',pixels:0};
         if(label){
          const range=document.createRange();range.selectNodeContents(label);
          const box=label.getBoundingClientRect();
          for(const r of range.getClientRects()){
           const x0=Math.max(0,Math.ceil(Math.max(r.left,box.left)-base.left)),
                 x1=Math.min(480,Math.floor(Math.min(r.right,box.right)-base.left)),
                 y0=Math.max(0,Math.ceil(Math.max(r.top,box.top)-base.top)),
                 y1=Math.min(320,Math.floor(Math.min(r.bottom,box.bottom)-base.top));
           for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
            const i=(y*480+x)*4;
            if(rgb[i]>=170&&rgb[i+1]>=170&&rgb[i+2]>=145)sample.pixels++;
           }
          }
         }
         labelsPainted.push(sample);
        }
       }finally{ui.style.transform=projection;}
      }
      return {lang:document.documentElement.lang,dpr:devicePixelRatio,dimensions:[canvas.width,canvas.height],fontStatus:document.fonts.status,
       menu:[menu.offsetWidth,menu.offsetHeight],uiOpacity:getComputedStyle(document.getElementById('lcdUI')).opacity,
       pageText:document.getElementById('bookPage').textContent,recordsVisible:visible(records),
       findVisible:visible(document.getElementById('bookTools')),
       detailVisible:visible(document.getElementById('bookDetail')),active:document.activeElement?.id,
       paintedMenu,paintedCards,labelsPainted,tileIds,labels:tiles.map(el=>[el.id,el.querySelector('b')?.textContent||'']),
       overflowingLabels:kind==='grid'?tiles.flatMap(el=>[...el.querySelectorAll('b')]).filter(el=>!labelFits(el)).map(el=>el.textContent):[],
       png:canvas.toDataURL('image/png').split(',')[1]};
     },kind);
     assert.deepEqual([frame.lang,frame.dpr,frame.dimensions,frame.fontStatus,frame.menu,frame.uiOpacity],
      [lang,1,[480,320],'loaded',[480,320],'0']);
     assert(frame.png!==closed.png,'Final composite did not change versus closed menu');
     assert(frame.paintedMenu>Math.max(1500,closed.menuPalette+1000),'Expected final canvas LCD menu pixels, not a blank/scenery-only image');
     if(kind==='grid'){
      assert(frame.recordsVisible&&!frame.findVisible&&!frame.detailVisible);
      assert.deepEqual(frame.tileIds,expectedIds,'Wrong fixture page');
      assert(frame.paintedCards>Math.max(12000,closed.cardPalette+10000),'Fish card fills absent from final LCD canvas');
      assert(frame.labelsPainted.every(g=>g.label&&g.pixels>=6),'A primary label has no visible glyph pixels in final LCD: '+JSON.stringify(frame.labelsPainted));
     }
     if(kind==='find')assert(frame.findVisible&&!frame.recordsVisible&&frame.active==='bookFindHeading');
     if(kind==='detail')assert(frame.detailVisible&&!frame.recordsVisible);
     const bytes=Buffer.from(frame.png,'base64');verifyPng(bytes);delete frame.png;
     const filename=lang+'-'+name+'-480x320.png';
     images.push({filename,sha256:digest(bytes),...frame});
     if(out)fs.writeFileSync(path.join(out,filename),bytes);
    }

    await page.locator('#bookFind').click();
    await capture('find','find');
    await page.locator('#bookFilter + button').click();
    await page.locator('#lcdPicker [data-index="2"]').click(); // Collected
    await page.locator('#bookFindDone').click();
    assert(await page.locator('#bookFind').evaluate(el=>document.activeElement===el),'Find returns focus');
    for(let i=0;i<3;i++){
     if(i)await page.locator('#bookNext').click();
     await capture(['first','middle','last'][i],'grid',ids.slice(i*8,i*8+8));
    }
    if(lang==='th'){
     const name=images.find(img=>img.filename==='th-middle-480x320.png');
     assert(name.labelsPainted.some(entry=>entry.label.length>=16&&/[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e]/.test(entry.label)),
      'Middle Thai fixture must include a long label with a combining mark');
    }else{
     const name=images.find(img=>img.filename==='en-middle-480x320.png');
     assert(name.labelsPainted.some(entry=>/[a-z]/i.test(entry.label)),'English fixture must include Latin glyphs');
    }
    await page.locator('#species-'+ids[23]).click();
    await capture('detail','detail');
    await page.locator('#back').click();
    assert(await page.locator('#species-'+ids[23]).isVisible(),'Detail back preserves the same last page');
    assert.deepEqual(errors,[],'No unhandled app exceptions');
   }finally{await context.close();}
  }
  if(out)fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({
   sourceCommit:process.env.SOURCE_SHA||null,htmlSHA256,renderer:browser.version(),capture:'Raw final #scene PNG; synthetic fresh state; DPR 1',specimenIds:ids,images
  },null,2)+'\n');
  for(const frame of images)assert.deepEqual(frame.overflowingLabels,[],frame.filename+' primary names exceed the drawn label bounds');
  console.log('PASS',images.length,'raw native frames with exact digests; visual review still required');
 }finally{await browser.close();}
}
