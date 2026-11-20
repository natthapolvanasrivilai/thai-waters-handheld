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
   kinds:atlas.fish.slice(60).reduce((x,f)=>(x[f.thaiNameKind]=(x[f.thaiNameKind]||0)+1,x),{})
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
  assert.equal(initial.target,'ปลาจุ้ยจินบั้ง');
  assert.equal(initial.a,'ปลาขี้ตังเบ็ดฟ้าอกขาว');
  assert.equal(initial.b,'ปลาก้างพระร่วง');
  assert.deepEqual(await page.evaluate(()=>[151,152,153,155,827,1565,1566,1731].map(id=>atlas.fish[id].name)),['ปลาการ์ตูนลายปล้อง','ปลาการ์ตูนแดงดำ','ปลาการ์ตูนส้มขาว','ปลาการ์ตูนลายปล้องหางเหลือง','ปลากะพงขาว','ปลาการ์ตูนเพอร์คูลาร์','ปลาการ์ตูนอานม้า','ปลาทรงเครื่อง']);
  assert.equal(initial.unconfirmed,'ยังไม่มีชื่อไทยที่ยืนยัน');
  assert.deepEqual(initial.kinds,{species:12,family:345,unconfirmed:2128});
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
  await page.reload();await page.waitForFunction(()=>typeof g!=='undefined'&&g&&!$('act').disabled);
  assert.equal(await page.evaluate(()=>g.caught(2152)),1);
  assert.equal(await page.evaluate(()=>g.caught(1433)),1);
  await page.evaluate(()=>{language='en';chooseAtlas();showBookEntry(2152);});
  assert.equal(await page.locator('#bookDetail h2').textContent(),'Uraspis uraspis');
  assert.deepEqual(errors,[]);
  console.log('PASS Thai exact/family/unconfirmed coverage; stable ID, taxon key, art and save; caught-only Thai/Latin/synonym search; catch, journal and Cup; English unchanged.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
