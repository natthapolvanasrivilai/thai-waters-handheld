"""Scratch-only instrumentation; reads exact canonical files, never edits source checkout."""
from pathlib import Path
import hashlib,shutil,sys
d=Path(__file__).resolve().parent; out=d/'lab'/'verification'/'browser-tests'; out.mkdir(parents=True,exist_ok=True)
game=d/'lab'/'game';game.mkdir(parents=True,exist_ok=True)
original=d.parents[1]/'browser-tests'
p=Path(sys.argv[1])
assert hashlib.sha256(p.read_bytes()).hexdigest()=='4f14cde0e2ca8b480032f24f4fd5734b0284992a2b3175ff747d3ac94bca3676'
shutil.copyfile(p,game/'Thai-Waters-play.html')
shutil.copyfile(d/'observer.cjs',out/'observer.cjs')
shutil.copyfile(original/'menu-controls.cjs',out/'menu-controls.cjs')
src=(original/'arrival.cjs').read_text()
def sub(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
src=sub(src,"const {chromium} = require('playwright-core');","const {chromium} = require('playwright-core');\nconst {attach}=require('./observer.cjs');")
src=sub(src," const url=pathToFileURL"," if(process.env.EXPECT_BROWSER_VERSION)assert.equal(browser.version(),process.env.EXPECT_BROWSER_VERSION);\n const url=pathToFileURL")
src=sub(src,"const url=pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;","const url=process.env.LOCAL_ARRIVAL_TEST_URL||pathToFileURL(path.resolve(__dirname,'../../game/Thai-Waters-play.html')).href;\n if(!/^file:|^http:\\/\\/127\\.0\\.0\\.1:/u.test(url))throw Error('Synthetic local diagnostic only');")
src=sub(src,"await page.addInitScript(()=>localStorage.setItem('thai-waters-language','en'));","const lab=await attach(page);")
src=sub(src,"if(await page.locator('#product').isVisible())await page.locator('#viewMode').click();","if(await page.locator('#product').isVisible())await page.locator('#viewMode').click();\n   await lab.seed({writeCanaries:false});")
src=sub(src,"for(const reduced of [false,true]){","assert(['desktop','mobile'].includes(process.env.TW62_LAYOUT));\n  for(const reduced of [process.env.TW62_LAYOUT==='mobile']){")
src=sub(src,"const {observed:castPhase,trace:beforeRestore}=await page.evaluate","const {observed:castPhase,trace:beforeRestore,preReload}=await page.evaluate")
src=sub(src,"assert([1,2].includes(castPhase),'The tap after Skip starts fishing');","assert([1,2].includes(castPhase),'The tap after Skip starts fishing');\n   lab.acceptBefore(preReload);")
src=sub(src,"}catch(error){console.error(traceText(beforeRestore,await probeReload(page,{placeName}),errors.length));throw error;}","    console.log('document-start probe '+JSON.stringify(await lab.report({reduced,activePlaceMatched:true,browserVersion:browser.version()})));\n   }catch(error){const after=await probeReload(page,{placeName});console.error(traceText(beforeRestore,after,errors.length));\n    try{console.log('document-start probe '+JSON.stringify(await lab.report({reduced,activePlaceMatched:after.activePlaceMatched,browserVersion:browser.version()})));}catch{};throw error;}")
(out/'arrival-probe.cjs').write_text(src)
tr=(original/'reload-trace.cjs').read_text()
tr=sub(tr,'return {observed,trace};',"return {observed,trace,preReload:observe==='cast'?globalThis.__twProbe62.snapshot():undefined};")
(out/'reload-trace.cjs').write_text(tr)
print('Hash-matched original HTML and original hard assertions preserved in scratch.')
