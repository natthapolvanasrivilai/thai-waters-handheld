const {chromium}=require('playwright-core');
const {attach}=require('./observer.cjs');
const assert=require('node:assert/strict');
const {createServer}=require('node:http');
const {writeFileSync,mkdtempSync}=require('node:fs');
const {tmpdir}=require('node:os');
const {join}=require('node:path');
const {pathToFileURL}=require('node:url');
async function run(){
  // Same bytes on both transports. No init language write, gameplay, app or sleep.
  const body=Buffer.from('<!doctype html><meta charset=utf-8><title>Synthetic WebStorage reload</title>');
  const path=join(mkdtempSync(join(tmpdir(),'tw62-bare-')),'bare.html');
  writeFileSync(path,body);
  const host=createServer((req,res)=>{if(req.url!=='/bare.html'){res.writeHead(404);res.end();return;}res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':body.length});res.end(body);});
  await new Promise(r=>host.listen(0,'127.0.0.1',r));
  let browser;
  try {
    browser=await chromium.launch({executablePath:process.env.BROWSER_PATH});
    if(process.env.EXPECT_BROWSER_VERSION)assert.equal(browser.version(),process.env.EXPECT_BROWSER_VERSION);
    const n=Number(process.argv[2]||1);
    assert(Number.isSafeInteger(n)&&n>0&&n<=100);
    let invalid=0;
    for(let i=0;i<n;i++)for(const reduced of [false,true])for(const url of [pathToFileURL(path).href,`http://127.0.0.1:${host.address().port}/bare.html`]){
      const page=await browser.newPage({viewport:reduced?{width:390,height:844}:{width:960,height:760},hasTouch:reduced,isMobile:reduced,reducedMotion:reduced?'reduce':'no-preference'});
      try {
        const inspect=await attach(page,{seedEnglish:false});
        await page.goto(url);
        await inspect.seed();
        await inspect.syntheticKey();
        await inspect.before();
        await page.reload();
        const report=await inspect.report({reduced,rep:i,browserVersion:browser.version()});
        console.log(JSON.stringify(report));if(report.classification!=='storage-and-live-place-retained')invalid++;
      }catch(e){invalid++;console.log(JSON.stringify({protocol:new URL(url).protocol,reduced,rep:i,failure:e.name}));}
      finally{await page.close();}
    }
    if(invalid)process.exitCode=1;
  }finally{if(browser)await browser.close();host.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
