// The original browser key remains the sole authority. No network/provider use.
function makeCareerStorage(storage,{fish,places,validSize,beforeWrite}){
 const key='thai-atlas-v2',format='Pocket Reel career',version=1,schema=4,limit=8*1024*1024;
 const invalid=()=>{throw Error('Invalid or incompatible career backup');};
 const int=(n,min,max)=>Number.isSafeInteger(n)&&n>=min&&n<=max;
 const object=o=>o!==null&&typeof o==='object'&&!Array.isArray(o);
 const json=s=>{if(typeof s!=='string'||s.length>limit)invalid();return JSON.parse(s);};
 const size=(n,i)=>int(n,1,65535)&&(!validSize||validSize(i,n));
 const id=(i)=>int(i,0,fish-1);
 function record(x,strict){
  if(!object(x)||!id(x.id)||!size(x.cm,x.id)){if(strict)invalid();return null;}
  const r={id:x.id,cm:x.cm};
  const ranges={grams:[0,2147483647],at:[0,8640000000000000],place:[0,places-1],period:[0,3],weather:[0,4],bait:[0,17]};
  if(x.uid!==undefined){
   if(typeof x.uid==='string'&&/^[0-9a-f]{1,64}$/i.test(x.uid))r.uid=x.uid;
   else if(strict)invalid();
  }
  for(const [field,[min,max]] of Object.entries(ranges))if(x[field]!==undefined){
   if(int(x[field],min,max))r[field]=x[field];
   else if(strict)invalid();
  }
  return r;
 }
 function normalize(x,strict){
  if(!object(x)||!Array.isArray(x.book)||x.book.length>fish)invalid();
  // Only known versions may migrate. Reject a future local save before writing.
  if(strict?x.schema!==schema:x.schema!==undefined&&!int(x.schema,1,schema))invalid();
  const b={schema};
  b.book=Array.from(x.book,(e,i)=>{
   if(Array.isArray(e)&&e.length===2&&int(e[0],0,9999999)&&(e[0]===0?e[1]===0:size(e[1],i)))return [e[0],e[1]];
   if(strict)invalid();
   return [0,0];
  });
  const opts={site:[0,4,0],place:[0,places-1,int(x.site,0,3)?x.site:0],time:[0,4,4],weather:[0,4,0],finish:[0,2,0],bait:[0,17,0],rig:[0,2,0]};
  for(const [field,[min,max,fallback]] of Object.entries(opts)){
   if(int(x[field],min,max))b[field]=x[field];
   else if(strict)invalid();
   else b[field]=fallback;
  }
  if(strict&&(!Array.isArray(x.rank)||x.rank.length!==3||!Array.isArray(x.history)))invalid();
  b.rank=Array.from({length:3},(_,i)=>{
   if(int(x.rank?.[i],0,3))return x.rank[i];
   if(strict)invalid();
   return 0;
  });
  b.history=Array.isArray(x.history)?x.history.map(y=>record(y,strict)).filter(Boolean):[];
  b.pending=null;
  if(x.pending!=null){
   if(Array.isArray(x.pending)&&(strict?x.pending.length===3:x.pending.length>=2)&&id(x.pending[0])&&size(x.pending[1],x.pending[0])&&int(x.pending[2]??0,0,Number.MAX_SAFE_INTEGER))
    b.pending=[x.pending[0],x.pending[1],x.pending[2]??0];
   else if(strict)invalid();
  }
  b.pendingCapture=x.pendingCapture==null?null:record(x.pendingCapture,strict);
  if(b.pendingCapture&&(!b.pending||b.pendingCapture.id!==b.pending[0]||b.pendingCapture.cm!==b.pending[1])){
   if(strict)invalid();
   b.pendingCapture=null;
  }
  return b;
 }
 function load(){
  const raw=storage.getItem(key);if(raw===null)return null;
  const parsed=json(raw);
  return normalize(parsed,parsed?.schema===schema);
 }
 function commit(value,{replace=false}={}){
  const valid=normalize(value,true);
  if(replace&&valid.pending)valid.pending[2]=0; // Imported catch has no live Cup authorization.
  const next=JSON.stringify(valid);if(next.length>limit)invalid();
  // Automatic writes must never clobber damaged or newer saves; manual imports
  // require explicit user confirmation before callers pass replace=true.
  const previous=(!replace||beforeWrite)?load():null;
  beforeWrite?.(previous);
  storage.setItem(key,next);
  return valid;
 }
 return {
  load,commit,
  exportBackup(value){
   const text=JSON.stringify({format,version,savedAt:new Date().toISOString(),career:normalize(value,true)},null,2);
   if(text.length>limit)invalid();
   return text;
  },
  parseBackup(text){
   const envelope=json(text);
   if(!object(envelope)||envelope.format!==format||envelope.version!==version)invalid();
   return normalize(envelope.career,true);
  }
 };
}

function makeFileCareerGuard(isFile,browserHistory){
 let known=false,recovering=false;
 if(isFile)try{known=browserHistory.state?.pocketReelCareerKnown===true;}catch{}
 function markKnown(){
  if(!isFile||known||recovering)return;
  known=true;
  try{browserHistory.replaceState({...browserHistory.state,pocketReelCareerKnown:true},'');}catch{}
 }
 function lock(){if(isFile)recovering=true;}
 function beforeWrite(previous){
  if(!isFile)return;
  if(recovering||(known&&previous===null)){lock();throw Error('Previous browser career unavailable for this file');}
 }
 return {markKnown,lock,beforeWrite,get recovering(){return recovering;}};
}
