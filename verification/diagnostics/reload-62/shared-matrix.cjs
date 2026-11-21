const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),{spawn}=require('node:child_process');
const {createInterface}=require('node:readline');
const {createHash}=require('node:crypto');const assert=require('node:assert/strict');
const body=fs.readFileSync(path.join(__dirname,'lab/game/Thai-Waters-play.html'));
assert.equal(createHash('sha256').update(body).digest('hex'),'4f14cde0e2ca8b480032f24f4fd5734b0284992a2b3175ff747d3ac94bca3676');
const runFile=path.join(__dirname,'lab/verification/browser-tests/arrival-probe.cjs');
const host=http.createServer((req,res)=>{
 if(req.url!=='/Thai-Waters-play.html'){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':body.length});res.end(body);
});
async function main(){
 assert(process.env.BROWSER_PATH,'Point BROWSER_PATH to the originally documented Chromium executable');
 assert(process.argv.length===2,'Exactly one pair; no repetition');
 await new Promise(r=>host.listen(0,'127.0.0.1',r));
 const url=`http://127.0.0.1:${host.address().port}/Thai-Waters-play.html`;
 try {
  const check=Buffer.from(await(await fetch(url)).arrayBuffer());assert(check.equals(body));
  let failed=0;
  for(const scheme of ['file','loopback']) {
    const env={...process.env};delete env.LOCAL_ARRIVAL_TEST_URL;
    if(scheme==='loopback')env.LOCAL_ARRIVAL_TEST_URL=url;
    delete env.TW62_LAYOUT;
    if(!env.EXPECT_BROWSER_VERSION)env.EXPECT_BROWSER_VERSION='151.0.7922.34';
    const layoutOrder=[];
    const child=spawn(process.execPath,[runFile],{env,cwd:path.dirname(runFile),stdio:['ignore','pipe','pipe']});
    for(const input of [child.stdout,child.stderr])createInterface({input}).on('line',line=>{
      const tag=['reload trace ','document-start probe '].find(p=>line.startsWith(p));
      if(!tag)return;
      try{
        const row=JSON.parse(line.slice(tag.length));
        if(tag==='document-start probe ')layoutOrder.push(row.reduced?'mobile':'desktop');
        console.log(tag+JSON.stringify({scheme,...row}));
      }catch{}
    });
    const outcome=await new Promise((r,j)=>{child.once('error',j);child.once('close',(code,signal)=>r({code,signal}));});
    console.log('cohort result '+JSON.stringify({scheme,layoutOrder,...outcome}));
    if(outcome.code!==0||layoutOrder.join(',')!=='desktop,mobile')failed++;
  }
  // Never mark a matrix containing a failed hard arrival run as passing.
  if(failed)process.exitCode=1;
 }finally{host.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
