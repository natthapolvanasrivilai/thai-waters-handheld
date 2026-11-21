const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require('playwright-core');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const file=process.env.GAME_HTML||path.join(__dirname,'../../game/Thai-Waters-play.html');
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(file));});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const page=await browser.newPage({isMobile:true,hasTouch:true,viewport:{width:844,height:390}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:'+server.address().port);
  await page.waitForFunction(()=>typeof g!=='undefined'&&g&&!document.querySelector('#act').disabled);
  const initial=await page.evaluate(()=>({
   size:atlas.fish.length, art:atlas.fish[2152].art,key:atlas.fish[2152].key, original:originalAtlas.fish[2152].name,
   target:atlas.fish[2152].name, a:atlas.fish[77].name,b:atlas.fish[2354].name,unconfirmed:atlas.fish[805].name,
   kinds:atlas.fish.slice(60).reduce((x,f)=>(x[f.thaiNameKind]=(x[f.thaiNameKind]||0)+1,x),{}),
   sourceCount:Object.keys(thaiSpecimenLabels.species).length,
   valid:atlas.fish.every((f,i)=>{
    const o=originalAtlas.fish[i],s=thaiSpecimenLabels.species[i];
    return /^[ก-๙]+(?:[ -][ก-๙]+)*$/u.test(f.name)&&(!o.key||f.key===o.key&&f.art===o.art&&
     f.scientificName===o.name&&f.thaiNameKind===(s?'species':'transliteration')&&
     f.name===(s?.name??thaiSpecimenTranscriptions.names[o.name]));
   })
  }));
  assert.deepEqual(await page.evaluate(()=>[42,47].map(id=>atlas.fish[id].name)),['ปลาลัง','ปลาสละ']);
  const ray=await page.evaluate(()=>({name:atlas.fish[1433].name,kind:atlas.fish[1433].thaiNameKind,
   base:originalAtlas.fish[1433].name,art:atlas.fish[1433].art,key:atlas.fish[1433].key}));
  assert.deepEqual(ray,{name:'ปลากระเบนทอง',kind:'species',base:'Taeniura lymma',art:1433,key:5215810});
  await page.evaluate(()=>{$('bookSearch').value='ปลากระเบนหางพัดจุดฟ้า';});
  assert(!await page.evaluate(()=>bookMatches().includes(1433)));
  await page.evaluate(()=>{g.restoreCatch(1433,35);pendingDay=0;save();draw();});
  await page.waitForFunction(()=>$('message').textContent==='ปลากระเบนทอง'&&!$('catchContinue').hidden);
  await page.evaluate(()=>$('catchContinue').click());
  await page.waitForFunction(()=>g.caught(1433)===1&&g.state()===0);
  assert.deepEqual(await page.evaluate(()=>['ปลากระเบนทอง','ปลากระเบนหางพัดจุดฟ้า','Taeniura lymma'].map(q=>{$('bookSearch').value=q;return bookMatches();})),[[1433],[1433],[1433]]);
  await page.evaluate(()=>showBookEntry(1433));
  assert.equal(await page.locator('#bookDetail h2').textContent(),'ปลากระเบนทอง');
  assert.match(await page.locator('#bookDetail').textContent(),/Taeniura lymma/u);
  await page.evaluate(()=>closeBookDetail());
  const sweet=await page.evaluate(()=>{
   const f=atlas.fish[1164],o=originalAtlas.fish[1164];
   return {name:f.name,kind:f.thaiNameKind,scientific:f.scientificName,base:o.name,key:f.key,
    art:f.art,aliases:f.thaiSearchAliases,fishData:['low','high','tier','weight','form','site','spot'].map(k=>[f[k],o[k]]),
    size:f.low};
  });
  assert.deepEqual([sweet.name,sweet.kind,sweet.scientific,sweet.base,sweet.key,sweet.art,sweet.aliases],
   ['ปลาสร้อยนกเขาทะเล','species','Plectorhinchus pictus','Plectorhinchus pictus',9713196,1164,[]]);
  assert.ok(sweet.fishData.every(([a,b])=>a===b),'species gameplay data unchanged');
  await page.evaluate(name=>{$('bookSearch').value=name;},sweet.name);
  assert(!await page.evaluate(()=>bookMatches().includes(1164)));
  await page.evaluate(size=>{g.restoreCatch(1164,size);pendingDay=0;save();draw();},sweet.size);
  await page.waitForFunction(()=>$('message').textContent==='ปลาสร้อยนกเขาทะเล'&&!$('catchContinue').hidden);
  await page.evaluate(()=>$('catchContinue').click());
  await page.waitForFunction(()=>g.caught(1164)===1&&g.state()===0);
  assert.deepEqual(await page.evaluate(()=>['ปลาสร้อยนกเขาทะเล','Plectorhinchus pictus','Diagramma pictum'].map(q=>{
   $('bookSearch').value=q;return bookMatches().includes(1164);
  })),[true,true,false]);
  await page.evaluate(()=>showBookEntry(1164));
  assert.equal(await page.locator('#bookDetail h2').textContent(),'ปลาสร้อยนกเขาทะเล');
  assert.match(await page.locator('#bookDetail').textContent(),/Plectorhinchus pictus/u);
  await page.evaluate(()=>closeBookDetail());
  assert.equal(initial.target,'ปลาจุ้ยจินบั้ง');
  assert.equal(initial.a,'ปลาขี้ตังเบ็ดฟ้าอกขาว');
  assert.equal(initial.b,'ปลาก้างพระร่วง');
  assert.deepEqual(await page.evaluate(()=>[151,152,153,155,827,1565,1566,1731].map(id=>atlas.fish[id].name)),['ปลาการ์ตูนลายปล้อง','ปลาการ์ตูนแดงดำ','ปลาการ์ตูนส้มขาว','ปลาการ์ตูนลายปล้องหางเหลือง','ปลากะพงขาว','ปลาการ์ตูนเพอร์คูลาร์','ปลาการ์ตูนอานม้า','ปลาทรงเครื่อง']);
  assert(initial.valid,'Every exact catalog ID has a Thai-script label without changing identity or claiming unsupported vernacular');
  assert.notEqual(initial.unconfirmed,'ยังไม่มีชื่อไทยที่ยืนยัน');
  assert.deepEqual(initial.kinds,{species:initial.sourceCount,transliteration:2485-initial.sourceCount});
  assert(initial.sourceCount>=84,'all three source-reviewed batches present');
  const curatedNext=[
   [215,2341214,'Bagarius suchus','แค้งู'],
   [63,2398657,'Abudefduf bengalensis','ปลาตะกรับเจ็ดแถบ'],
   [1058,5202457,'Pangasius bocourti','ปลายางหางดอก'],
   [1557,7734965,'Ambastaia sidthimunki','ปลาหมูอารีย์'],
   [1120,2356584,'Pegasus laternarius','ปลาผีเสื้อกลางคืนสั้น']
  ];
  assert.deepEqual(await page.evaluate(ids=>ids.map(id=>{
   const f=atlas.fish[id];
   return [id,f.key,f.scientificName,f.name,f.thaiNameKind];
  }),curatedNext.map(([id])=>id)),curatedNext.map(row=>[...row,'species']),
  'representative newly attested Thai names from each cited review tranche');
  assert(initial.sourceCount>=194,'verified catalog overlay contains at least the 194 attested names');
  const wetlandsNext=[
   [282,2386080,'Butis butis','ปลาบู่เกล็ดแข็งหางแดง'],
   [861,2384777,'Lutjanus fulviflamma','ปลากะพงเหลืองข้างปาน'],
   [871,2385118,'Lutjanus russellii','ปลากะพงข้างปาน'],
   [1100,2378916,'Parapocryptes serperaster','ปลาท่องเที่ยวเกล็ดใหญ่'],
   [1476,5211201,'Trichopsis vittata','ปลากริมควาย'],
  ];
  assert.deepEqual(await page.evaluate(ids=>ids.map(id=>{
   const f=atlas.fish[id];
   return [f.art,f.key,f.scientificName,f.name,f.thaiNameKind];
  }),wetlandsNext.map(([id])=>id)),wetlandsNext.map(row=>[...row,'species']),
  'species-specific wetland vernaculars presented with the exact Latin and stable IDs');
  assert(initial.sourceCount>=206,'verified catalog overlay contains at least 206 attested names');
  assert.deepEqual([initial.size,initial.art,initial.key,initial.original],[2545,2152,2391358,'Uraspis uraspis']);
  await page.evaluate(()=>{$('bookSearch').value='ปลาจุ้ยจินบั้ง';});
  assert.equal(await page.evaluate(()=>bookMatches().includes(2152)),false);
  await page.evaluate(()=>{g.restoreCatch(2152,30);pendingDay=0;save();draw();});
  await page.waitForFunction(()=>$('message').textContent==='ปลาจุ้ยจินบั้ง'&&!$('catchContinue').hidden);
  await page.evaluate(()=>$('catchContinue').click());
  await page.waitForFunction(()=>g.caught(2152)===1&&g.state()===0);
  assert.deepEqual(await page.evaluate(()=>['ปลาจุ้ยจินบั้ง','Uraspis uraspis','Caranx uraspis'].map(q=>{$('bookSearch').value=q;return bookMatches();})),[[2152],[2152],[2152]]);
  await page.evaluate(()=>{$('bookSearch').value='ปลาจุ้ยจินบั้ง';renderBook();});
  assert.match(await page.locator('#species-2152').getAttribute('aria-label'),/ปลาจุ้ยจินบั้ง/u);
  await page.evaluate(()=>showBookEntry(2152));
  assert.equal(await page.locator('#bookDetail h2').textContent(),'ปลาจุ้ยจินบั้ง');
  assert.match(await page.locator('#bookDetail').textContent(),/Uraspis uraspis/u);
  await page.evaluate(()=>{cupBoard={goal:{day:0,species:2152,spot:113,minimum:30}};drawCup();});
  assert.match(await page.locator('#cupGoal').textContent(),/^ปลาจุ้ยจินบั้ง/u);
  await page.evaluate(()=>closeBookDetail());
  const grunter=await page.evaluate(()=>{const f=atlas.fish[2448];return [f.name,f.scientificName,f.thaiNameKind,f.art,f.key,f.low];});
  assert.deepEqual(grunter.slice(0,5),['ปลาครืดคราด','Pomadasys kaakan','species',2448,2382902]);
  const match=async (q,id)=>page.evaluate(([q,id])=>{$('bookSearch').value=q;return bookMatches().includes(id);},[q,id]);
  assert(!await match('ปลาออดแอดขาว',2448));
  async function land(id,cm){
   await page.evaluate(([id,cm])=>{g.restoreCatch(id,cm);pendingDay=0;save();draw();},[id,cm]);
   await page.waitForFunction(()=>!$('catchContinue').hidden);
  }
  async function file(id){
   await page.evaluate(()=>$('catchContinue').click());
   await page.waitForFunction(id=>g.caught(id)===1&&g.state()===0,id);
  }
  async function nativeCatchText(){
   await page.evaluate(()=>document.fonts.ready);
   return page.evaluate(()=>{
    const labels=[],originalFill=ctx.fillText;
    try{
     ctx.fillText=function(text,x,y,...rest){
      labels.push({text,x,y,width:ctx.measureText(text).width,align:ctx.textAlign});
      return originalFill.call(this,text,x,y,...rest);
     };
     landedCatch(0);
    }finally{ctx.fillText=originalFill;}
    return {lcd:[ctx.canvas.width,ctx.canvas.height],labels};
   });
  }
  function fits(rows){return rows.length>0&&rows.every(r=>r.y>0&&r.y<=310&&r.align==='left'&&r.x>=0&&r.x+r.width<=480);}
  const seamoth=await page.evaluate(()=>{
   const short=atlas.fish[1120],long=atlas.fish[1121];
   return {low:short.low,short:short.name,long:long.name,aliases:short.thaiSearchAliases};
  });
  assert.deepEqual([seamoth.short,seamoth.long,seamoth.aliases],
   ['ปลาผีเสื้อกลางคืนสั้น','ผีเสื้อกลางคืนหางยาว',[]]);
  for(const q of [seamoth.short,'Pegasus laternarius'])assert(!await match(q,1120));
  await land(1120,seamoth.low);
  assert.equal(await page.locator('#message').textContent(),seamoth.short);
  assert(!/ถอดเสียง/u.test(await page.locator('#metrics').textContent()));
  const seamothNative=await nativeCatchText();
  assert.deepEqual(seamothNative.lcd,[480,320]);
  const seamothLatin=seamothNative.labels.find(r=>r.text==='Pegasus laternarius');
  assert(seamothLatin&&fits([seamothLatin]),'exact Latin identification fits the catch card');
  const seamothTitle=seamothNative.labels.filter(r=>r.y>=110&&r.y<seamothLatin.y);
  assert(fits(seamothTitle),'every Thai title line fits the catch card');
  assert.equal(seamothTitle.map(r=>r.text).join(''),seamoth.short,'joined native Thai title is complete');
  await file(1120);
  for(const q of [seamoth.short,'Pegasus laternarius'])assert(await match(q,1120));
  assert(!await match(seamoth.long,1120),'distinct long-finned seamoth does not become a short-finned alias');
  await page.evaluate(()=>showBookEntry(1120));
  assert.equal(await page.locator('#bookDetail h2').textContent(),seamoth.short);
  assert.match(await page.locator('#bookDetail').textContent(),/Pegasus laternarius/u);
  await page.evaluate(()=>closeBookDetail());
  const [snapperId,,snapperLatin,snapperThai]=wetlandsNext[2];
  for(const q of [snapperThai,snapperLatin])assert(!await match(q,snapperId),'uncaught snapper is not returned by Thai or Latin search');
  const snapperLow=await page.evaluate(id=>atlas.fish[id].low,snapperId);
  await land(snapperId,snapperLow);
  assert.equal(await page.locator('#message').textContent(),snapperThai);
  assert(!/ถอดเสียง/u.test(await page.locator('#metrics').textContent()));
  await file(snapperId);
  for(const q of [snapperThai,snapperLatin])assert(await match(q,snapperId));
  assert(!await match(wetlandsNext[1][3],snapperId),'attested yellow snapper name does not match the other snapper');
  await page.evaluate(id=>showBookEntry(id),snapperId);
  assert.equal(await page.locator('#bookDetail h2').textContent(),snapperThai);
  assert.match(await page.locator('#bookDetail').textContent(),/Lutjanus russellii/u);
  await page.evaluate(()=>closeBookDetail());
  await land(2448,grunter[5]);
  assert.equal(await page.locator('#message').textContent(),'ปลาครืดคราด');
  assert(!/ถอดเสียง/u.test(await page.locator('#metrics').textContent()));
  const named=await nativeCatchText();
  assert.deepEqual(named.lcd,[480,320]);
  assert(fits(named.labels.filter(r=>r.text==='ปลาครืดคราด'||r.text==='Pomadasys kaakan')));
  assert(named.labels.some(r=>r.text==='ปลาครืดคราด'));
  await file(2448);
  for(const q of ['ปลาครืดคราด','ปลาออดแอดขาว','Pomadasys kaakan'])assert(await match(q,2448));
  await page.evaluate(()=>showBookEntry(2448));
  assert.equal(await page.locator('#bookDetail h2').textContent(),'ปลาครืดคราด');
  assert.match(await page.locator('#bookDetail').textContent(),/Pomadasys kaakan/u);
  await page.evaluate(()=>closeBookDetail());
  const fallback=await page.evaluate(()=>{const f=atlas.fish[805];return [f.name,f.scientificName,f.thaiNameKind,f.low];});
  assert.equal(fallback[1],'Kryptopterus bicirrhis');
  assert.equal(fallback[2],'transliteration','historic name for #2354 must not bleed into #805');
  assert(!await match(fallback[0],805));assert(!await match(fallback[1],805));
  await land(805,fallback[3]);
  assert.equal(await page.locator('#message').textContent(),fallback[0]);
  assert.match(await page.locator('#metrics').textContent(),/ชื่อวิทยาศาสตร์ถอดเสียง · Kryptopterus bicirrhis/u);
  const roman=await nativeCatchText();
  assert.deepEqual(roman.lcd,[480,320]);
  const catchArea=roman.labels.filter(r=>r.y===82&&r.text.includes('ถอดเสียง')||r.text===fallback[1]||r.y>=110&&r.y<=156&&fallback[0].includes(r.text));
  assert(fits(catchArea)&&catchArea.some(r=>r.text.includes('ถอดเสียง'))&&catchArea.some(r=>r.text===fallback[1]));
  assert(catchArea.some(r=>r.y>=110&&r.y<=156&&fallback[0].includes(r.text)));
  await file(805);
  assert(await match(fallback[0],805));assert(await match(fallback[1],805));
  assert(!await match('ปลาก้างพระร่วง',805));
  await page.locator('#openMenu').tap();
  await page.locator('[data-to=book]').tap();
  assert(await match(fallback[0],805));
  await page.evaluate(()=>renderBook());
  assert.match(await page.locator('#species-805').getAttribute('aria-label'),/ชื่อวิทยาศาสตร์ถอดเสียง · Kryptopterus bicirrhis/u);
  await page.evaluate(()=>showBookEntry(805));
  assert.equal(await page.locator('#bookDetail h2').textContent(),fallback[0]);
  assert.match(await page.locator('#bookDetail').textContent(),/ชื่อวิทยาศาสตร์ถอดเสียง · Kryptopterus bicirrhis/u);
  assert(await page.evaluate(()=>{
   const ui=$('lcdUI'),old=ui.style.transform;
   try{
    ui.style.transform='none';
    const d=$('bookDetail'),limit=$('menu').getBoundingClientRect();
    const marker=[...d.querySelectorAll('small')].find(n=>n.textContent.includes('ชื่อวิทยาศาสตร์ถอดเสียง'));
    return ui.offsetWidth===480&&ui.offsetHeight===320&&[d.querySelector('h2'),marker].every(n=>{
     const r=n?.getBoundingClientRect();
     return r?.width>0&&r.height>0&&r.left>=limit.left&&r.right<=limit.right&&r.top>=limit.top&&r.bottom<=limit.bottom;
    });
   }finally{ui.style.transform=old;}
  }), 'Thai name, exact Latin and transcription marker fit the visible native detail');
  await page.evaluate(()=>{cupBoard={goal:{day:0,species:805,spot:113,minimum:30}};drawCup();});
  assert.match(await page.locator('#cupGoal').textContent(),/ชื่อวิทยาศาสตร์ถอดเสียง/u);
  await page.reload();await page.waitForFunction(()=>typeof g!=='undefined'&&g&&!$('act').disabled);
  assert.equal(await page.evaluate(()=>g.caught(2152)),1);
  assert.equal(await page.evaluate(()=>g.caught(1433)),1);
  assert.equal(await page.evaluate(()=>g.caught(1164)),1);
  assert.deepEqual(await page.evaluate(()=>[2448,805].map(id=>g.caught(id))),[1,1]);
  assert.equal(await page.evaluate(()=>g.caught(1120)),1,'new Thai label preserves the same filed specimen after reload');
  assert.equal(await page.evaluate(()=>{
   $('bookSearch').value='ปลาสร้อยนกเขาทะเล';
   return bookMatches().includes(1164);
  }),true,'Thai search matches the same caught species after reload');
  await page.evaluate(()=>showBookEntry(1164));
  assert.equal(await page.locator('#bookDetail h2').textContent(),'ปลาสร้อยนกเขาทะเล');
  assert.match(await page.locator('#bookDetail').textContent(),/Plectorhinchus pictus/u);
  await page.evaluate(()=>closeBookDetail());
  await page.evaluate(()=>{language='en';chooseAtlas();showBookEntry(2152);});
  assert.equal(await page.locator('#bookDetail h2').textContent(),'Uraspis uraspis');
  await page.evaluate(()=>showBookEntry(1164));
  assert.equal(await page.locator('#bookDetail h2').textContent(),'Plectorhinchus pictus');
  assert.deepEqual(errors,[]);
  console.log('PASS every Thai catalog name, separated sourced vernacular/transcription coverage; stable ID, taxon key, art and save; caught-only Thai/Latin/synonym search; catch, journal and Cup; English unchanged.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
