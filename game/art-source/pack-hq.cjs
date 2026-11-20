const a=require('node:assert/strict'),fs=require('node:fs'),p=require('node:path'),c=require('node:crypto'),cp=require('node:child_process');
const dir=p.resolve(process.env.TW_ART_DIR||'game/art-source'),{PNG}=require(require.resolve('pngjs',{paths:[p.resolve(dir,'../lan')]})),{individuals}=require(p.join(dir,'segment-field.cjs'));
const rows=JSON.parse(fs.readFileSync(p.join(dir,'field/plates.json'))),fish=JSON.parse(fs.readFileSync(p.join(dir,'../content/extended.json'))),cache=new Map();
function checked(f,h){a.match(f,/^[\w.-]+\.png$/);const b=fs.readFileSync(p.join(dir,'field',f));a.equal(c.createHash('sha256').update(b).digest('hex'),h,f);return b;}
const values=[1822,2158,2160,2190,2192].map(id=>{
 const m=rows.filter(r=>r.ids.includes(id));a.equal(m.length,1);const s=m[0],n=s.ids.indexOf(id);
 a.equal(s.species[n],fish[id-52].name);const r=s.replacements?.[id];checked(s.file,s.sha256);
 if(r?.reference)checked(r.reference,r.reference_sha256);
 const f=r?.file??s.file,h=r?.sha256??s.sha256,cell=r?(r.cell??1):(n+1);
 if(!cache.has(f))cache.set(f,individuals(PNG.sync.read(checked(f,h)),r?(r.rows??1):s.rows,f,r?(r.columns??1):(s.columns??4)));
 const im=cache.get(f)[cell-1];a(im);return {id,scientific:s.species[n],file:f,cell,source_sha256:h,replacement:r??null,png:PNG.sync.write(im).toString('base64')};
});
const py=String.raw`import base64,hashlib,io,json,pathlib,sys
from PIL import Image
out={'format':'thai-waters-fish-hq/v1','width':288,'height':150,'portraits':{}}
total=0
for r in json.load(sys.stdin):
 i=Image.open(io.BytesIO(base64.b64decode(r.pop('png'),validate=True))).convert('RGBA');s=min(276/i.width,138/i.height);w,h=round(i.width*s),round(i.height*s);b=Image.new('RGBA',(288,150));b.paste(i.resize((w,h),Image.Resampling.LANCZOS),((288-w)//2,(150-h)//2));o=io.BytesIO();b.save(o,'WEBP',quality=88,alpha_quality=100,method=6);data=o.getvalue();d=Image.open(io.BytesIO(data)).convert('RGBA');assert d.size==(288,150) and d.getchannel('A').tobytes()==b.getchannel('A').tobytes() and b.getchannel('A').getbbox() and 3000<len(data)<=30000
 r.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),source_dimensions=i.size,art_dimensions=(w,h),webp=base64.b64encode(data).decode());total+=len(data);out['portraits'][str(r['id'])]=r
assert total<=80000
pathlib.Path(sys.argv[1]).write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
print(f'{len(out["portraits"])} portraits; {total} compressed bytes')`;
const result=cp.spawnSync('python3',['-B','-c',py,process.argv[2]],{input:JSON.stringify(values),stdio:['pipe','inherit','inherit']});if(result.error)throw result.error;process.exitCode=result.status??1;
