const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const fs=require('node:fs');
const guides=process.argv[2]?[path.resolve(process.argv[2])]:
  ['R0013-PCB-assembly-corrected.html','R0014-PCB-assembly.html','R0015-PCB-assembly.html']
    .map(name=>path.join(__dirname,'../../docs/models',name));
const screenshots=process.env.ASSEMBLY_SCREENSHOTS;
const cases=[{width:1140,height:800},{width:390,height:844}];
async function pixels(page){
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const raw=await page.locator('#model').screenshot();
  return {raw,hash:require('node:crypto').createHash('sha256').update(raw).digest('hex')};
}
async function inspect(browser,guide){
    const revision=path.basename(guide).split('-')[0];
    const looseRails=revision==='R0013';
    const assemblyId='TW-A-0001-'+revision;
    const loadReport=(name,assembly=assemblyId)=>JSON.parse(fs.readFileSync(
      path.join(__dirname,'../../hardware/mechanical',assembly,'QA/power-key',name),'utf8'));
    const key=loadReport('key-path.json'),blocked=key.pcb.status==='blocked';
    assert.equal(blocked,revision!=='R0015');
    for(const [idx,viewport] of cases.entries()){
      const context=await browser.newContext({viewport,offline:true,isMobile:!!idx,hasTouch:!!idx});
      if(idx)await context.addInitScript(()=>{
        const original=HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext=function(type,...args){return type.startsWith('webgl')?null:original.call(this,type,...args);};
        // Capture the actual projected guide vertices handed to the fallback canvas.
        window.guideVertices=[];
        for(const name of ['moveTo','lineTo','putImageData']){
          const draw=CanvasRenderingContext2D.prototype[name];
          CanvasRenderingContext2D.prototype[name]=function(...args){
            if(this.canvas.id==='model'){
              if(name==='putImageData')window.guideVertices=[];
              else window.guideVertices.push(args);
            }
            return draw.apply(this,args);
          };
        }
      });
      const page=await context.newPage(),errors=[],requests=[];
      page.on('pageerror',err=>errors.push(err.message));
      page.on('request',req=>{if(/^https?:/.test(req.url()))requests.push(req.url());});
      await page.goto(pathToFileURL(guide).href);
      await page.waitForFunction(()=>document.querySelector('#title').textContent.length>0);
      assert.equal(await page.locator('#model').evaluate(canvas=>Boolean(canvas.getContext('webgl2'))),!idx);
      const assembly=await page.locator('#assemblyData').evaluate(el=>{
        const {scene,steps}=JSON.parse(el.textContent);
        return {id:scene.assembly,housing:scene.parts.housing.source,parts:Object.keys(scene.parts),steps};
      });
      assert.equal(assembly.id,assemblyId);
      const housingAssembly=looseRails?'TW-A-0001-R0011':assemblyId;
      assert.equal(assembly.housing,'hardware/mechanical/'+housingAssembly+'/Print/housing-battery-bay.stl');
      assert.ok((await page.title()).includes(revision));
      assert.deepEqual(assembly.parts.filter(id=>/^A[345]s/.test(id)).sort(),
        [...(looseRails?['A3s1','A3s2']:[]),'A4s1','A4s2','A4s3','A5s1','A5s2','A5s3']);
      const ids=await page.locator('#steps option').evaluateAll(x=>x.map(e=>e.value));
      const titles=assembly.steps.map(step=>step.title);
      const select=async title=>{
        assert.ok(titles.includes(title),title);
        await page.selectOption('#steps',String(titles.indexOf(title)));
      };
      assert.equal(ids.length,titles.length);
      assert.equal(new Set(titles).size,titles.length);
      const seen=new Set();
      for(const id of ids){
        await page.selectOption('#steps',id);
        assert.equal(await page.locator('#counter').innerText(),'Step '+(Number(id)+1)+' of '+ids.length);
        const pic=await pixels(page);
        if(screenshots && !idx){
          fs.mkdirSync(screenshots,{recursive:true});fs.writeFileSync(path.join(screenshots,revision+'-step-'+id+'.png'),pic.raw);
        }
        seen.add(pic.hash);
      }
      assert.equal(seen.size,ids.length,'Each step should render a distinct view');
      if(looseRails){
        await select('Place the two A3 floor strips');
        assert.match(await page.locator('#instruction').innerText(),/2\.10 mm high/);
        assert.ok(await page.locator('#position').isVisible());
        await select('Set A3 on both strips');
      }else{
        await select('Inspect the integral A3 rails');
        assert.match(await page.locator('#instruction').innerText(),/R0013 plate 7/);
        assert.ok(await page.locator('#position').isHidden());
        await select('Seat A3 on the housing rails');
      }
      const before=await pixels(page);
      await page.locator('#position').fill('0');
      const seated=await pixels(page);assert.notEqual(before.hash,seated.hash);
      await page.locator('#ghost').click();assert.notEqual(seated.hash,(await pixels(page)).hash);
      await page.locator('#focus').click();
      const zoomed=await pixels(page);await page.locator('#model').press('ArrowRight');
      assert.notEqual(zoomed.hash,(await pixels(page)).hash);
      await page.locator('#reset').click();await page.locator('#next').click();
      const motionSteps=assembly.steps.filter(step=>step.motionPart);
      assert.deepEqual(motionSteps.map(step=>step.motionPart),blocked?['cap']:['cap','KEY','keeper']);
      assert.equal(await page.locator('#title').innerText(),motionSteps[0].title);
      const records=[loadReport('cap-path.json',looseRails?'TW-A-0001-R0014':assemblyId),key.pcb,key.keeper];
      for(const [i,step] of motionSteps.entries()){
        await select(step.title);
        assert.deepEqual(step.waypoints,records[i].removal_offsets_mm);
        assert.deepEqual(step.active,[step.motionPart]);
        assert.deepEqual(step.visible.filter(id=>['cap','KEY','keeper'].includes(id)).sort(),
          motionSteps.slice(0,i+1).map(previous=>previous.motionPart).sort());
        assert.equal(await page.locator('#position').inputValue(),'100');
        assert.equal(await page.locator('#positionText').innerText(),'Clear above housing');
        const start=await pixels(page);
        assert.ok(await page.locator('#tag').isVisible());
        if(idx&&step.motionPart==='cap'){
          const points=await page.evaluate(()=>window.guideVertices);
          assert.equal(points.length,3,'The path must turn at the opening');
          const [[x,y],[a,b],[c,d]]=points;
          assert.ok(Math.abs((a-x)*(d-b)-(b-y)*(c-a))>5,'The camera must show the bend');
          await page.locator('#position').fill('50');
          await pixels(page);
          const [seat,bend,half]=await page.evaluate(()=>window.guideVertices);
          assert.deepEqual(seat,[x,y]);
          assert.deepEqual(bend,[a,b]);
          const fraction=(26.5/2-2.5)/24;
          assert.ok(Math.hypot(half[0]-(a+(c-a)*fraction),half[1]-(b+(d-b)*fraction))<.01,
            'The highlighted part and guide must stop partway along the vertical leg');
          await page.locator('#position').fill('100');
        }
        await page.locator('#overview').click();
        assert.notEqual((await pixels(page)).hash,start.hash);
        await page.locator('#reset').click();
        assert.equal((await pixels(page)).hash,start.hash,'Restore the step camera');
        let previous=start;
        for(let j=step.waypoints.length-2;j>=0;j--){
          await page.locator('#nextPosition').click();
          const now=await pixels(page);
          assert.notEqual(now.hash,previous.hash,'Moving to a waypoint must change the part view');
          assert.ok(await page.locator('#tag').isVisible());
          if(step.motionPart==='cap'&&j===1){
            assert.equal(await page.locator('#positionText').innerText(),'2.5 mm to seat');
            if(idx)assert.equal((await page.evaluate(()=>window.guideVertices)).length,2);
          }
          previous=now;
        }
        assert.equal(await page.locator('#positionText').innerText(),'Seated');
        assert.ok(await page.locator('#nextPosition').isDisabled());
        await page.locator('#focus').click();
        await page.locator('#position').fill('100');
        await pixels(page);
        assert.ok(await page.locator('#tag').isVisible(),'Focused part must stay in frame while moving');
      }
      if(blocked){
        const stop=assembly.steps.findIndex(step=>step.inspectionPart==='KEY');
        assert.ok(stop>0&&assembly.steps[stop-1].motionPart==='cap');
        await select(titles[stop]);
        assert.ok(await page.locator('#position').isHidden());
        assert.deepEqual(assembly.steps[stop].visible,['KEY']);
        for(const step of assembly.steps.slice(stop+1)){
          assert.ok(step.visible.every(id=>!['cap','KEY','keeper'].includes(id)));
        }
      }
      await select('Fit the bezel and inspect the seam');
      assert.equal(await page.locator('#checks input').count(),5);
      const checks=await page.locator('#checks').innerText();
      if(looseRails){
        assert.match(checks,/eight printed spacers/);
        assert.match(checks,/retainer aside before closure/);
      }else{
        assert.match(checks,/both integral housing rails/);
        assert.match(checks,/six loose printed spacers/);
        assert.match(checks,blocked?/bay remains empty/:/KEY remains captured/);
      }
      await page.locator('#checks input').first().check();
      await page.selectOption('#pack','adafruit');assert.equal(await page.locator('#checks input').first().isChecked(),false);
      await page.selectOption('#pack','pkcell');assert.ok(await page.locator('#checks input').first().isChecked());
      assert.ok(await page.locator('#next').isDisabled());
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
      await context.close();
    }
    console.log(revision+': passed every offline assembly step on desktop and mobile, measured power-key paths, waypoint navigation, camera controls, closure checks and battery selection.');
}
(async()=>{
  const opts=process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:
    process.platform==='win32'?{channel:'msedge'}:{};
  const browser=await chromium.launch(opts);
  try{
    for(const guide of guides)await inspect(browser,guide);
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
