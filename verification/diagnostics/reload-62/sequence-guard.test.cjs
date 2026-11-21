const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const {join}=require('node:path');
const original=readFileSync(join(__dirname,'../../browser-tests/arrival.cjs'),'utf8');
const probe=readFileSync(join(__dirname,'lab/verification/browser-tests/arrival-probe.cjs'),'utf8');
function assertExactSequence(a,b){
  const behavioral=[
    "const browser=await chromium.launch(",
    "for(const reduced of [false,true]){",
    "const page=await browser.newPage(",
    "await page.locator('#act').click();\n   const placeName='Kwan Phayao';",
    "await page.reload();await page.waitForFunction(()=>!document.getElementById('act').disabled);",
    "assert.equal(await page.locator('#arrivalSkip').isVisible(),false);\n    assert.equal(await page.locator('#spot').textContent(),'Kwan Phayao');",
    "await travel('Krabi coastal waters','Dawn',()=>probeTrip('skip'));",
    "assert.deepEqual(errors,[]);",
    "await page.close();",
    "await browser.close();"
  ];
  for(const text of [a,b]){
    let j=0;
    for(const snippet of behavioral){
      const k=text.indexOf(snippet,j);assert(k>=0,'Original stage missing or reordered: '+snippet);
      assert.equal(text.indexOf(snippet,k+snippet.length),-1,'Unexpected extra original stage: '+snippet);j=k+snippet.length;
    }
  }
  // Compare every original hard assertion, except for no-rewrite safety/version guard.
  const hard=x=>x.split('\n').map(l=>l.trim()).filter(l=>l.startsWith('assert.'));
  assert.deepEqual(hard(b),hard(a));
}
test('generated diagnostic keeps exact canonical shared launch and hard assertions',()=>{
  assertExactSequence(original,probe);
});
test('topology guard detects common invalid comparisons',()=>{
  assert.throws(()=>assertExactSequence(original,probe.replace('[false,true]','[true,false]')));
  assert.throws(()=>assertExactSequence(original,probe.replace('await page.close();','')));
  assert.throws(()=>assertExactSequence(original,probe.replace("assert.equal(await page.locator('#spot').textContent(),'Kwan Phayao');","")));
});
