"""Export checked geometry and carry the unchanged parts forward from the tagged assembly."""
from pathlib import Path
import base64,gzip,hashlib,json,re,shutil,zlib
import cadquery as cq
import numpy as np
import trimesh

def save(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_stl(shape,path,flip=False):
    if flip:shape=shape.rotate((0,0,0),(1,0,0),180)
    b=shape.BoundingBox()
    shape=shape.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
    cq.exporters.export(shape,str(path),tolerance=.025,angularTolerance=.1)
    mesh=trimesh.load_mesh(path)
    assert mesh.is_watertight and mesh.is_volume and len(mesh.split())==1,path
    assert abs(mesh.volume-shape.Volume())<shape.Volume()*.004,path
    return [round(float(a),3) for a in mesh.extents]
def new_mesh(shape):
    vv,ff=shape.tessellate(.065,.18)
    def encode(a):return base64.b64encode(zlib.compress(a.tobytes(),7)).decode()
    return dict(v=encode(np.rint(np.array([p.toTuple() for p in vv])*100).astype('<i2')),t=encode(np.array(ff,dtype='<u4')))
def export(here,ref,work,out,rows,shapes,changed,report,qa,routes):
    dst=here/'Print';dst.mkdir(exist_ok=True)
    catalog={}
    for key,name in [('Housing','housing-battery-bay'),('Retainer','key-board-retainer-west'),('bridge','battery-wire-bridge')]:
        catalog[name]=write_stl(shapes[key],dst/(name+'.stl'),key=='Retainer')
    inherited=['bezel','rotor','folding-stem','grip','collar','power-cap','rod-grip','grip-screw-keeper','receiver-nut-keeper']
    for name in inherited:
        src=ref.parent/'Print'/(name+'.stl')
        if not src.exists():src=ref.parents[1]/'rev-E/Print'/(name+'.stl')
        shutil.copyfile(src,dst/src.name)
        mesh=trimesh.load_mesh(src);assert mesh.is_volume and mesh.is_watertight and len(mesh.split())==1
        catalog[name]=[round(float(a),3) for a in mesh.extents]
    save(here/'print-manifest.json',{k:dict(extents_mm=v,sha256=hashfile(dst/(k+'.stl')),inherited=k in inherited) for k,v in catalog.items()})
    save(here/'collisions.json',report);save(here/'qualification.json',qa)
    allroutes=json.loads((ref/'routes.json').read_text());allroutes.update(routes);save(here/'routes.json',allroutes)
    old=out/'Riffle-Rev-F-exploded.html'
    assert hashfile(old)=='4eef6011bc672552e4a9a37d80bfb782719e3d5ec2870499e18fd3c947cde702'
    raw=re.search(r'id="geometry">(.+?)</script>',old.read_text(encoding='utf-8'),re.S)[1]
    oldmeshes={r['id']:r for r in json.loads(raw)}
    view=[]
    for k,r in rows.items():
        if k in changed:
            v=shapes[k];b=v.BoundingBox()
            r.update(bounds_mm=[round(getattr(b,a),4) for a in ('xmin','xmax','ymin','ymax','zmin','zmax')],solids=len(v.Solids()))
            mesh=new_mesh(v)
        else:mesh={i:oldmeshes[k][i] for i in ('v','t')}
        if k in ('Retainer','Keeper screw'):
            r.update(source='rev-G/geometry.py',note='West-side carrier keeper at X −43.2, Y 28.7; top-left switch and cap retain their Rev F positions.')
        view.append(dict(**r,**mesh))
    save(here/'parts.json',list(rows.values()))
    (work/'meshes.json').write_text(json.dumps(view,separators=(',',':')),encoding='utf-8')
    full=cq.Assembly(name='Thai_Waters_Rev_G_Drawing_Max')
    for k,r in rows.items():
        if k in ('usbGauge','cellAlt','Cell','pack0','pack1') or r.get('batteryVariant') in ('catalog','alt'):continue
        full.add(shapes[k],name=k,color=cq.Color(r['color']))
    step=work/'Rev-G.step';full.export(str(step))
    with step.open('rb') as f,gzip.open(out/'Riffle-Rev-G-dressed.step.gz','wb',compresslevel=5) as g:shutil.copyfileobj(f,g)
    print('Exported',len(view),'viewer records and',len(catalog),'verified print solids.',flush=True)

