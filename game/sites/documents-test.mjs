import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {buildDocuments, docsResponse} from './documents.mjs';
const revision='a'.repeat(40);
const blob=(body)=>createHash('sha1').update('blob '+Buffer.byteLength(body)+'\0').update(body).digest('hex');
const item=(path,body)=>({path,body,sha:blob(body)});
const files=[
  item('docs/wiki/Home.md','# Test guide\n\n[Details](Software-and-tests.md#current-release) · [Gate](../../quality/hardware-gate.md)\n\n|Board|Status|\n|--|--|\n|Waveshare|Hold|\n\n[Unsafe](javascript:alert%281%29)\n\n<script>alert(1)</script>\n'),
  item('docs/wiki/Software-and-tests.md','# Software\n\n## Current release\nExact text.\n'),
];
const pages=buildDocuments({revision,files});
const get=(path,method='GET')=>docsResponse(new Request('https://example.test'+path,{method}),pages);
const home=get('/docs/');
assert.equal(home.status,200);
assert.match(home.headers.get('cache-control'),/private/);
assert.match(home.headers.get('content-security-policy'),/default-src 'none'/);
const h=await home.text();
assert.match(h,/<h1 id="test-guide">Test guide<\/h1>/);
assert.match(h,/\/docs\/wiki\/Software-and-tests\.md#current-release/);
assert.match(h,new RegExp('/blob/'+revision+'/quality/hardware-gate.md'));
assert.match(h,/<table>/);
assert.doesNotMatch(h,/<script|href="javascript:/i);
assert.match(await get('/docs/wiki/Software-and-tests.md').text(),/id="current-release".*Current release<\/h2>/);
assert.equal(await get('/docs/wiki/Software-and-tests.md','HEAD').text(),'');
assert.equal(get('/docs/unlisted.md').status,404);
assert.equal(get('/docs/','POST').status,405);
assert.equal(get('/outside'),null);
assert.throws(()=>buildDocuments({revision,files:[{...files[0],body:'Tampered'}]}),/blob/i);
assert.throws(()=>buildDocuments({revision,files:[files[0],files[0]]}),/duplicate/i);
console.log('PASS canonical blob, Markdown headings and tables, pinned links, restrictive output and private doc routes.');
