const {requireBootHome}=require('./boot-home-check.cjs');
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
    await (await requireBootHome(page)).click();
    await page.waitForFunction(()=>typeof g!=='undefined'&&g&&!$('act').disabled);
    await page.locator('#openMenu').click();
    await page.locator('#languageRow [data-language='+lang+']').click();
    await page.waitForFunction(value=>document.documentElement.lang===value,lang);
    if(!ids)ids=await page.evaluate(()=>{
     // First, middle and last of the fixture. The middle eight are verified
     // Thai species labels, including the longest authored name (ID 155).
     const n=atlas.fish.length,middle=[151,152,153,155,827,1433,1565,1566];
     if(!middle.every(i=>atlas.fish[i].thaiNameKind==='species'))throw Error('Verified middle-fixture species labels changed');
     return [...Array.from({length:8},(_,i)=>i),...middle,...Array.from({length:8},(_,i)=>n-8+i)];
    });
    await page.evaluate(fish=>{
     assertSyntheticPage(fish);
     function assertSyntheticPage(list){if(list.some(i=>g.caught(i)))throw Error('Fixture requires a fresh collection');}
     for(const i of fish)g.restoreEntry(i,1,atlas.fish[i].low);
     refresh();
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
    await page.locator('[data-section=home] [data-to=book]').click();

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
      // A DOM Range bounds the font's line box, not painted ink. Fit the
      // same visual segments, face and baseline used by the LCD renderer.
      const measure=document.createElement('canvas').getContext('2d');
      const labelFits=el=>{
       const node=el.firstChild,content=node?.textContent||'',range=document.createRange();
       const style=getComputedStyle(el),box=el.getBoundingClientRect(),heading=[];
       if(!content||node.nodeType!==Node.TEXT_NODE)return false;
       measure.font=style.fontStyle+' '+style.fontWeight+' '+style.fontSize+' '+style.fontFamily;
       measure.textAlign='left';measure.textBaseline='alphabetic';
       const font=measure.measureText('Ag');
       let start=-1,end=0,top=0;
       function line(){
        if(start<0)return;
        range.setStart(node,start);range.setEnd(node,end);
        const r=range.getBoundingClientRect();
        const mark=measure.measureText(content.slice(start,end).replace(/\s+/g,' '));
        const y=r.top+(r.height+font.fontBoundingBoxAscent-font.fontBoundingBoxDescent)/2;
        heading.push({left:r.left-mark.actualBoundingBoxLeft,right:r.left+mark.actualBoundingBoxRight,
                      top:y-mark.actualBoundingBoxAscent,bottom:y+mark.actualBoundingBoxDescent});
       }
       for(const part of lcdPaintSegments(content,true)){
        range.setStart(node,part.index);range.setEnd(node,part.index+part[0].length);
        const y=range.getBoundingClientRect().top;
        if(start<0||Math.abs(y-top)>1){line();start=part.index;top=y;}
        end=part.index+part[0].length;
       }
       line();
       const aa=1; // Fractional Canvas antialias rounding, not an extra text row.
       return {lines:heading.length, fits:heading.length>0&&heading.every(q=>q.left>=box.left-aa&&q.right<=box.right+aa&&q.top>=box.top-aa&&q.bottom<=box.bottom+aa)};
      };
      const overflowingLabels=[],labelsPainted=[];
      let clippingProbeRejected=false;
      // Measure actual light glyph pixels inside each primary-name range,
      // in the same unprojected coordinate system as paintLcdInterface.
      if(kind==='grid'){
       const ui=$('lcdUI'),projection=ui.style.transform;
       try{
        ui.style.transform='none';const base=ui.getBoundingClientRect();
        for(const tile of tiles){
         const label=tile.querySelector('b'),sample={label:label?.textContent||'',pixels:0};
         if(label){
          const geometry=labelFits(label);sample.lines=geometry.lines;
          if(!geometry.fits)overflowingLabels.push(label.textContent);
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
        // Negative control after reading the real bitmap. Never persist or
        // capture the probe, and restore the same markup immediately.
        const probe=tiles[0]?.querySelector('b');
        if(probe){
         const previous=probe.style.maxHeight;
         try{probe.style.maxHeight='2px';clippingProbeRejected=!labelFits(probe).fits;}
         finally{probe.style.maxHeight=previous;}
        }
       }finally{ui.style.transform=projection;}
      }
      return {lang:document.documentElement.lang,dpr:devicePixelRatio,dimensions:[canvas.width,canvas.height],fontStatus:document.fonts.status,
       menu:[menu.offsetWidth,menu.offsetHeight],uiOpacity:getComputedStyle(document.getElementById('lcdUI')).opacity,
       pageText:document.getElementById('bookPage').textContent,recordsVisible:visible(records),
       findVisible:visible(document.getElementById('bookTools')),
       detailVisible:visible(document.getElementById('bookDetail')),active:document.activeElement?.id,
       paintedMenu,paintedCards,labelsPainted,tileIds,labels:tiles.map(el=>[el.id,el.querySelector('b')?.textContent||'']),
       overflowingLabels,clippingProbeRejected,
       png:canvas.toDataURL('image/png').split(',')[1]};
     },kind);
     assert.deepEqual([frame.lang,frame.dpr,frame.dimensions,frame.fontStatus,frame.menu,frame.uiOpacity],
      [lang,1,[480,320],'loaded',[480,320],'0']);
     assert(frame.png!==closed.png,'Final composite did not change versus closed menu');
     assert(frame.paintedMenu>Math.max(1500,closed.menuPalette+1000),'Expected final canvas LCD menu pixels, not a blank/scenery-only image');
     if(kind==='grid'){
      assert(frame.recordsVisible&&!frame.findVisible&&!frame.detailVisible);
      assert(frame.clippingProbeRejected,'Native ink bounds failed to reject a deliberately clipped label');
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
     assert(name.labelsPainted.some(entry=>entry.label==='ปลาการ์ตูนลายปล้องหางเหลือง'&&/[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e]/.test(entry.label)),
      'Middle Thai fixture must include a long label with a combining mark');
    }else{
     const name=images.find(img=>img.filename==='en-middle-480x320.png');
     assert(name.labelsPainted.some(entry=>/[a-z]/i.test(entry.label)),'English fixture must include Latin glyphs');
     const long=images.find(img=>img.filename==='en-last-480x320.png').labelsPainted
      .find(entry=>entry.label==='Trypauchenichthys sumatrensis');
     assert(long?.lines===2&&long.pixels>=150,'Long scientific name must draw both full lines of ink');
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
