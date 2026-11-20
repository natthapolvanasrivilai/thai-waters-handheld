import {execFileSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import {documentationPaths} from './documents.mjs';

const [ref,destination]=process.argv.slice(2);
if(!ref||ref.startsWith('-')||!destination)throw new Error('Usage: node game/sites/snapshot-docs.mjs <commit-or-ref> <output-json>');
const git=(...args)=>execFileSync('git',args,{encoding:'utf8',maxBuffer:8*1024*1024});
const revision=git('rev-parse','--verify',ref+'^{commit}').trim();
const files=documentationPaths.map(path=>{
  const sha=git('rev-parse','--verify',revision+':'+path).trim();
  return {path,sha,body:git('cat-file','blob',sha)};
});
writeFileSync(destination,JSON.stringify({revision,files})+'\n');
console.log('Captured '+files.length+' documentation blobs from '+revision);
