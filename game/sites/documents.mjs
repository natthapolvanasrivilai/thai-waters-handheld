import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {posix} from 'node:path';

export const documentationPaths=[
  'README.md','game/sites/Phone-playtest.md',
  ...['Home','Software-and-tests','Game-and-demo','Hardware-and-3D','Electrical-verification',
      'Validation-and-compliance','Factory-and-service','BOM-and-business','Clock-and-saves'].map(n=>'docs/wiki/'+n+'.md'),
];
export function requireAllDocuments(files){
  const paths=new Set(files?.map(f=>f.path));
  if(paths.size!==documentationPaths.length||documentationPaths.some(path=>!paths.has(path)))
    throw new Error('Site publication requires the full canonical documentation snapshot');
}

const base='https://github.com/natthapolvanasrivilai/thai-waters-handheld';
const index='docs/wiki/Home.md';
const allow=/^(?:README\.md|docs\/wiki\/[A-Za-z0-9-]+\.md|game\/sites\/Phone-playtest\.md)$/;
const hash=/^[a-f0-9]{40}$/;
const route=(path)=>path===index?'/docs/':'/docs/'+path.replace(/^docs\//,'');
const escape=(text)=>String(text).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const style=':root{color-scheme:light dark;--line:#858585}*{box-sizing:border-box}body{font:1rem/1.6 system-ui,sans-serif;margin:auto;max-width:70rem;padding:1.25rem}nav{display:flex;gap:.5rem 1.1rem;flex-wrap:wrap;margin-bottom:1.2rem}a{text-underline-offset:.17em;overflow-wrap:anywhere}main{max-width:85ch;margin:auto}h1,h2,h3{line-height:1.24}h1{font-size:clamp(1.75rem,5vw,2.6rem)}table{border-collapse:collapse;display:block;overflow:auto}td,th{border:1px solid var(--line);padding:.4rem .55rem;min-width:8rem;vertical-align:top}code{overflow-wrap:anywhere}pre{overflow:auto}footer{border-top:1px solid var(--line);margin-top:2rem;padding-top:.6rem;font-size:.9rem}';

function pandoc(args,input){
  const p=spawnSync('pandoc',args,{input,encoding:'utf8',maxBuffer:8*1024*1024});
  if(p.error||p.status!==0) throw new Error('Pandoc could not render canonical documentation: '+(p.error?.message??p.stderr));
  return p.stdout;
}

function links(node,path,present,revision){
  if(Array.isArray(node)){for(const child of node)links(child,path,present,revision);return;}
  if(!node||typeof node!=='object')return;
  if(node.t==='RawBlock'||node.t==='RawInline'){
    node.t=node.t==='RawBlock'?'Plain':'Str';
    if(node.t==='Str')node.c='';
    else node.c=[];
    return;
  }
  if(node.t==='Image'){
    node.t='Link';
    if(!node.c[1].length)node.c[1]=[{t:'Str',c:'Open original image'}];
  }
  if(node.t==='Link'){
    links(node.c[1],path,present,revision);
    const target=node.c[2];const url=target[0];
    if(!url||url.startsWith('#'))return;
    if(/^[a-z][a-z0-9+.-]*:|^\/\//i.test(url)){
      if(!/^https?:\/\//i.test(url)) target[0]='#';
      return;
    }
    const match=/^([^#?]*)(.*)$/.exec(url);let logical;
    try{logical=posix.normalize(posix.join(posix.dirname(path),decodeURIComponent(match[1])));}catch{target[0]='#';return;}
    if(logical==='..'||logical.startsWith('../')||logical.includes('\\')){target[0]='#';return;}
    target[0]=(present.has(logical)?route(logical):base+'/blob/'+revision+'/'+logical.split('/').map(encodeURIComponent).join('/'))+match[2];
    return;
  }
  for(const child of Object.values(node))links(child,path,present,revision);
}

export function buildDocuments({revision,files}){
  if(!hash.test(revision)||!Array.isArray(files)||!files.length) throw new Error('Missing exact canonical documentation snapshot');
  const present=new Map();
  for(const {path,body,sha} of files){
    if(!allow.test(path)) throw new Error('Unexpected document path: '+path);
    if(present.has(path)) throw new Error('Duplicate document: '+path);
    if(typeof body!=='string'||createHash('sha1').update('blob '+Buffer.byteLength(body)+'\0').update(body).digest('hex')!==sha) throw new Error('Canonical Git blob mismatch: '+path);
    present.set(path,body);
  }
  if(!present.has(index))throw new Error('Canonical wiki index is missing');
  const pages={};
  for(const [path,body] of present){
    const doc=JSON.parse(pandoc(['-f','gfm-raw_html','-t','json'],body));
    links(doc,path,present,revision);
    const html=pandoc(['-f','json','-t','html5','--wrap=none'],JSON.stringify(doc));
    const title=(body.match(/^# (.+)/m)?.[1]??'Documentation')+' | Pocket Reel';
    const github=base+'/blob/'+revision+'/'+path;
    pages[route(path)]='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escape(title)+'</title><style>'+style+'</style><main><nav aria-label="Site"><a href="/">Play</a><a href="/docs/">Product wiki</a><a href="'+github+'">This page on GitHub</a><a href="'+base+'/releases">GitHub releases</a></nav>'+html+'<footer>From GitHub documentation snapshot <a href="'+base+'/tree/'+revision+'"><code>'+revision.slice(0,9)+'</code></a>. This copy does not change GitHub or the installed firmware.</footer></main></html>';
  }
  return pages;
}

export function docsResponse(request,pages){
  const path=new URL(request.url).pathname;
  if(path!=='/docs'&&!path.startsWith('/docs/'))return null;
  const headers={'cache-control':'private, no-cache','content-type':'text/html; charset=utf-8','content-security-policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",'x-content-type-options':'nosniff','referrer-policy':'no-referrer'};
  if(request.method!=='GET'&&request.method!=='HEAD')return new Response(null,{status:405,headers:{...headers,allow:'GET, HEAD'}});
  const key=path==='/docs'?'/docs/':path;
  if(!Object.hasOwn(pages,key))return new Response(null,{status:404,headers});
  return new Response(request.method==='HEAD'?null:pages[key],{headers});
}
