const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright-core');
const fs=require('node:fs');
const guides=process.argv[2]?[path.resolve(process.argv[2])]:
  ['R0013-PCB-assembly-corrected.html','R0014-PCB-assembly.html','R0015-PCB-assembly.html','R0016-PCB-assembly.html','R0017-PCB-assembly.html']
    .map(name=>path.join(__dirname,'../../docs/models',name));
const screenshots=process.env.ASSEMBLY_SCREENSHOTS;
const cases=[{width:1140,height:800},{width:390,height:844}];
async function pixels(page){
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const raw=await page.locator('#model').screenshot();
  return {raw,hash:require('node:crypto').createHash('sha256').update(raw).digest('hex')};
}
async function assertRestoredSection(page, before, after){
  // Compare the rendered composition in normalized coordinates. Chrome and the
  // window system can round antialiased edges differently on a second render.
  const delta=await page.evaluate(async pngs=>{
    const images=await Promise.all(pngs.map(async png=>{
      const image=new Image();
      image.src='data:image/png;base64,'+png;
      await image.decode();
      const canvas=document.createElement('canvas');
      canvas.width=128;canvas.height=96;
      const ctx=canvas.getContext('2d');
      ctx.drawImage(image,0,0,128,96);
      return ctx.getImageData(0,0,128,96).data;
    }));
    let changed=0,total=0;
    for(let i=0;i<images[0].length;i+=4){
      const rgb=[0,1,2].map(k=>Math.abs(images[0][i+k]-images[1][i+k]));
      total+=rgb[0]+rgb[1]+rgb[2];
      if(Math.max(...rgb)>16)changed++;
    }
    return {mean:total/(128*96*3),fraction:changed/(128*96)};
  },[before,after].map(pic=>pic.raw.toString('base64')));
  assert.ok(delta.mean<2 && delta.fraction<.025,'Restored section differs: '+JSON.stringify(delta));
}
async function usbPixels(page){
  return page.locator('#model').evaluate(canvas=>{
    const {width:w,height:h}=canvas,rgba=canvas.getContext('2d').getImageData(0,0,w,h).data;
    const bounds=predicate=>{
      let left=w,right=-1,top=h,bottom=-1;
      for(let y=0;y<h;y++)for(let x=0;x<w;x++){
        const i=4*(y*w+x);
        if(rgba[i+3]===255&&predicate(rgba[i],rgba[i+1],rgba[i+2])){
          left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
        }
      }
      return right<0?null:{left,right,top,bottom,x:(left+right)/2,y:(top+bottom)/2};
    };
    const board=bounds((r,g,b)=>r>g*1.35&&g>b*1.7);
    const pipe=bounds((r,g,b)=>b>g*1.15&&g>r*1.65);
    let roof;
    if(board){
      for(let y=board.bottom+1;y<h;y++){
        const i=4*(y*w+Math.round(board.x));
        if(rgba[i+3]===255&&rgba[i+1]>rgba[i]&&rgba[i+1]>rgba[i+2]){roof=y;break;}
      }
    }
    return {board,pipe,roof};
  });
}
async function inspect(browser,guide){
    const revision=path.basename(guide).split('-')[0];
    const looseRails=revision==='R0013';
    const assemblyId='TW-A-0001-'+revision;
    const housingId=revision==='R0017'?'TW-A-0001-R0016':assemblyId;
    const loadReport=(name,assembly=housingId)=>JSON.parse(fs.readFileSync(
      path.join(__dirname,'../../hardware/mechanical',assembly,'QA/power-key',name),'utf8'));
    const key=loadReport('key-path.json'),blocked=key.pcb.status==='blocked';
    const usb=loadReport('../usb-indicator/'+housingId.slice(-5)+'.json','TW-A-0001-R0015');
    assert.equal(blocked,revision==='R0013'||revision==='R0014');
    assert.equal(usb.status==='clear',housingId.endsWith('R0016'));
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
      const housingAssembly=looseRails?'TW-A-0001-R0011':housingId;
      assert.equal(assembly.housing,'hardware/mechanical/'+housingAssembly+'/Print/housing-battery-bay.stl');
      assert.ok((await page.title()).includes(revision));
      if(revision==='R0017'){
        assert.ok(assembly.steps.some(s=>s.instruction.includes('R0016 plate-1 housing')));
        assert.ok(assembly.steps.every(s=>!s.instruction.includes('R0017 plate-1 housing')));
      }
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
      const motionSteps=assembly.steps.filter(step=>['cap','KEY','keeper'].includes(step.motionPart));
      assert.deepEqual(motionSteps.map(step=>step.motionPart),blocked?['cap']:['cap','KEY','keeper']);
      assert.equal(await page.locator('#title').innerText(),motionSteps[0].title);
      const records=[loadReport('cap-path.json',looseRails?'TW-A-0001-R0014':housingId),key.pcb,key.keeper];
      for(const [i,step] of motionSteps.entries()){
        await select(step.title);
        assert.deepEqual(step.waypoints,records[i].removal_offsets_mm);
        assert.deepEqual(step.active,[step.motionPart]);
        assert.deepEqual(step.visible.filter(id=>['cap','KEY','keeper'].includes(id)).sort(),
          motionSteps.slice(0,i+1).map(previous=>previous.motionPart).sort());
        if(revision==='R0017' && step.motionPart==='cap'){
          assert.match(await page.locator('#positionText').innerText(),/2.5 mm to seat/);
          assert.match(step.facing,/matching corner/);
          const capSource=await page.locator('#assemblyData').evaluate(el=>JSON.parse(el.textContent).scene.parts.cap.source);
          assert.match(capSource,/R0017\/Print\/power-cap.stl$/);
          await page.locator('#position').fill('100');
        }
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
      const usbStep=assembly.steps.find(s=>s.usbIndicator);
      assert.deepEqual(usbStep.active,['USB1']);
      assert.ok(usbStep.visible.includes('housing')&&usbStep.visible.includes('uGuide'));
      await select(usbStep.title);
      assert.equal(await page.locator('#section').getAttribute('aria-pressed'),'true');
      assert.ok(await page.locator('#sectionLegend').isVisible());
      const usbStart=await pixels(page);
      await page.locator('#section').click();
      assert.ok(await page.locator('#sectionLegend').isHidden());
      assert.notEqual((await pixels(page)).hash,usbStart.hash);
      await page.locator('#reset').click();
      assert.equal(await page.locator('#section').getAttribute('aria-pressed'),'true');
      assert.ok(await page.locator('#sectionLegend').isVisible());
      await assertRestoredSection(page,usbStart,await pixels(page));
      if(usb.status==='blocked'){
        assert.deepEqual(usbStep.fixedOffset,[0,0,usb.rejected_vertical.first_contact_offset_z_from_above_mm[0]]);
        assert.ok(!usbStep.waypoints&&!usbStep.motionPart);
        assert.ok(await page.locator('#position').isHidden());
        assert.match(await page.locator('#instruction').innerText(),/Set the loose gauge aside/);
        assert.ok(assembly.steps.slice(assembly.steps.indexOf(usbStep)+1).every(s=>!s.visible.includes('USB1')));
        if(idx){
          const {board,pipe,roof}=await usbPixels(page);
          assert.ok(board&&pipe&&board.bottom<pipe.top);
          assert.ok(roof-board.bottom<=2,'Blocked gauge must be displayed at the top surface of the roof');
        }
      }else{
        assert.equal(usbStep.motionPart,'USB1');
        assert.deepEqual(usbStep.waypoints,usb.waypoints_offset_mm.slice().reverse());
        assert.equal(await page.locator('#position').inputValue(),'100');
        assert.equal(await page.locator('#positionText').innerText(),'Clear above housing');
        const first=idx?await usbPixels(page):null;
        if(idx){
          const [seat,bend,top]=await page.evaluate(()=>window.guideVertices);
          assert.ok(Math.abs(seat[1]-bend[1])<.01&&Math.abs(bend[0]-top[0])<.01);
          assert.ok(seat[0]>bend[0]+10&&bend[1]>top[1]+10,'Show the slide and drop on separate screen axes');
          assert.ok(Math.hypot(first.board.x-top[0],first.board.y-top[1])<2);
          assert.ok(Math.hypot(first.pipe.x-seat[0],first.pipe.y-seat[1])<2);
        }
        await page.locator('#nextPosition').click();
        const middle=await pixels(page);
        assert.notEqual(middle.hash,usbStart.hash);
        assert.equal(await page.locator('#positionText').innerText(),Math.abs(usb.waypoints_offset_mm[1][1])+' mm to seat');
        const lowered=idx?(await usbPixels(page)).board:null;
        if(idx)assert.ok(Math.abs(lowered.x-first.board.x)<1&&lowered.y>first.board.y+10);
        await page.locator('#nextPosition').click();
        assert.notEqual((await pixels(page)).hash,middle.hash);
        assert.equal(await page.locator('#positionText').innerText(),'Seated');
        assert.ok(await page.locator('#nextPosition').isDisabled());
        if(idx){
          const seated=(await usbPixels(page)).board;
          assert.ok(Math.abs(seated.y-lowered.y)<1&&seated.x>lowered.x+10);
          assert.ok(Math.hypot(seated.x-first.pipe.x,seated.y-first.pipe.y)<2,'Center the seated LED on the pipe');
        }
      }
      await select('Lower the display onto its four seats');
      assert.match(await page.locator('#check').innerText(),/soldered lamp leads cannot span/);
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
    console.log(revision+': passed offline desktop and mobile steps, power-key sequence, USB1 section and '+usb.status+' route, camera controls, closure and battery selection.');
}
(async()=>{
  const opts=process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:
    process.platform==='win32'?{channel:'msedge'}:{};
  const browser=await chromium.launch(opts);
  try{
    for(const guide of guides)await inspect(browser,guide);
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
