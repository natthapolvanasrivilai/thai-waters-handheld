const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const fs=require('node:fs');
const guide=path.resolve(process.argv[2]||path.join(__dirname,'../../docs/models/R0014-PCB-assembly.html'));
const screenshots=process.env.ASSEMBLY_SCREENSHOTS;
const cases=[{width:1140,height:800},{width:390,height:844}];
async function pixels(page){
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const raw=await page.locator('#model').screenshot();
  return {raw,hash:require('node:crypto').createHash('sha256').update(raw).digest('hex')};
}
(async()=>{
  const opts=process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:
    process.platform==='win32'?{channel:'msedge'}:{};
  const browser=await chromium.launch(opts);
  try{
    for(const [idx,viewport] of cases.entries()){
      const context=await browser.newContext({viewport,offline:true,isMobile:!!idx,hasTouch:!!idx});
      if(idx)await context.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext=function(type,...args){return type.startsWith('webgl')?null:original.call(this,type,...args);};});
      const page=await context.newPage(),errors=[],requests=[];
      page.on('pageerror',err=>errors.push(err.message));
      page.on('request',req=>{if(/^https?:/.test(req.url()))requests.push(req.url());});
      await page.goto(pathToFileURL(guide).href);
      await page.locator('#title').waitFor();
      const assembly=await page.locator('#assemblyData').evaluate(el=>{
        const {scene}=JSON.parse(el.textContent);
        return {id:scene.assembly,housing:scene.parts.housing.source,parts:Object.keys(scene.parts)};
      });
      assert.equal(assembly.id,'TW-A-0001-R0014');
      assert.equal(assembly.housing,'hardware/mechanical/TW-A-0001-R0014/Print/housing-battery-bay.stl');
      assert.deepEqual(assembly.parts.filter(id=>/^A[345]s/.test(id)).sort(),
        ['A4s1','A4s2','A4s3','A5s1','A5s2','A5s3']);
      const ids=await page.locator('#steps option').evaluateAll(x=>x.map(e=>e.value));
      assert.equal(ids.length,23);
      const seen=new Set();
      for(const id of ids){
        await page.selectOption('#steps',id);
        assert.match(await page.locator('#counter').innerText(),new RegExp('Step '+(Number(id)+1)+' of 23'));
        const pic=await pixels(page);
        if(screenshots && !idx && [0,1,4,6,7,11,15,20,22].includes(Number(id))){
          fs.mkdirSync(screenshots,{recursive:true});fs.writeFileSync(path.join(screenshots,'step-'+id+'.png'),pic.raw);
        }
        seen.add(pic.hash);
      }
      assert.equal(seen.size,ids.length,'Each step should render a distinct view');
      await page.selectOption('#steps','6');
      assert.match(await page.locator('#title').innerText(),/integral A3 rails/);
      assert.match(await page.locator('#instruction').innerText(),/R0013 plate 7/);
      assert.ok(await page.locator('#position').isHidden());
      await page.selectOption('#steps','7');
      assert.match(await page.locator('#title').innerText(),/Seat A3 on the housing rails/);
      const before=await pixels(page);
      await page.locator('#position').fill('0');
      const seated=await pixels(page);assert.notEqual(before.hash,seated.hash);
      await page.locator('#ghost').click();assert.notEqual(seated.hash,(await pixels(page)).hash);
      await page.locator('#focus').click();
      const zoomed=await pixels(page);await page.locator('#model').press('ArrowRight');
      assert.notEqual(zoomed.hash,(await pixels(page)).hash);
      await page.locator('#reset').click();await page.locator('#next').click();
      assert.match(await page.locator('#title').innerText(),/KEY/);await page.locator('#prev').click();
      await page.selectOption('#steps','22');
      assert.equal(await page.locator('#checks input').count(),5);
      assert.match(await page.locator('#checks').innerText(),/both integral housing rails/);
      assert.match(await page.locator('#checks').innerText(),/six loose printed spacers/);
      await page.locator('#checks input').first().check();
      await page.selectOption('#pack','adafruit');assert.equal(await page.locator('#checks input').first().isChecked(),false);
      await page.selectOption('#pack','pkcell');assert.ok(await page.locator('#checks input').first().isChecked());
      assert.ok(await page.locator('#next').isDisabled());
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
      await context.close();
    }
    console.log('Passed 23 desktop and 23 mobile-sized offline views, both renderers, movement, zoom, keyboard orbit, closure checks and battery selection.');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
