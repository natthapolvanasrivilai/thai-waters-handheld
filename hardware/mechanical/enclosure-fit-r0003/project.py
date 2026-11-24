"""Package the registered seven-plate project with the revised hardware and full-height gauges."""
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from copy import deepcopy
from hashlib import sha256
import json,sys,uuid,math
import cadquery as cq
import numpy as np
import manifold3d as mf
import trimesh
from lxml import etree as E
from mount import HERE,geometry,b
from gauges import pcb,other
MECH=HERE.parent
sys.path.insert(0,str(MECH.parents[0]/'electronics/case-board-r0001'))
from print_fit import replace_mesh
from make_project import CORE,PROD,MODEL,SETTINGS,RELATIONSHIPS,encode,value
BASE=MECH/'reel-dfm-r0001/Thai-Waters-DFM-R0001-X1C.3mf'
OUT=HERE/'Thai-Waters-R0003-Enclosure-X1C.3mf'
def mesh(s):
    v,f=s.tessellate(.012,.07)
    return trimesh.Trimesh([p.toTuple() for p in v],f)
def manifold(m):return mf.Manifold(mf.Mesh64(np.array(m.vertices),np.array(m.faces,dtype=np.uint64)))
def tr(m):
    data=m.to_mesh64()
    return trimesh.Trimesh(data.vert_properties[:,:3],data.tri_verts)
def read_mesh(xml,oid):
    q=xml.find(f".//{CORE}object[@id='{oid}']/{CORE}mesh")
    v=[[float(p.get(k)) for k in 'xyz'] for p in q.find(CORE+'vertices')]
    f=[[int(p.get(k)) for k in ('v1','v2','v3')] for p in q.find(CORE+'triangles')]
    return trimesh.Trimesh(v,f)
def run(cache):
    assert sha256(BASE.read_bytes()).hexdigest()=='58a072dcd4f14b83a02fcd88fbe1f8ee0ba960334c662bdeeb04ccaa8939fb60'
    with ZipFile(BASE) as z: files={k:z.read(k) for k in z.namelist()}
    model,config,rels=[E.fromstring(files[k]) for k in (MODEL,SETTINGS,RELATIONSHIPS)]
    resources=model.find(CORE+'resources'); build=model.find(CORE+'build');plate=config.findall('plate')[6]
    def obj(oid):
        node=resources.find(f"{CORE}object[@id='{oid}']")
        component=node.find('.//'+CORE+'component')
        path=component.get(PROD+'path').lstrip('/')
        data=E.fromstring(files[path])
        definition=config.find(f"object[@id='{oid}']")
        return data,component.get('objectid'),path,definition,definition.find('part')
    def assign(oid,m,label):
        xml,pid,path,definition,part=obj(oid)
        replace_mesh(xml,pid,m);files[path]=encode(xml)
        for node in (part,definition):
            node.find("metadata[@key='name']").set('value',label)
        part.find('mesh_stat').set('face_count',str(len(m.faces)))
        face=definition.find('metadata[@face_count]')
        if face is not None:face.set('face_count',str(len(m.faces)))
    shell0,shell,sled,posts,cut=geometry()
    xml,pid,_,_,part=obj('2')
    offsets=np.array([float(value(part,'source_offset_'+k)) for k in 'xyz'])
    shift=np.array([0,0,3.200001004005232])-offsets
    def placed(s):
        m=mesh(s);m.apply_translation(shift);return manifold(m)
    body=manifold(read_mesh(xml,pid))-placed(cut)
    for post in posts:body=body+placed(post)
    from closure import features
    bosses,reliefs,pads,bores=features()
    for stock in bosses:body=body+placed(stock)
    for void in reliefs:body=body-placed(void)
    assert len(body.decompose())==1
    assign('2',tr(body),'Housing - removable lamp shelf')
    xml,pid,_,_,part=obj('4')
    offset=np.array([float(value(part,'source_offset_'+k)) for k in 'xyz'])
    pose=np.array(json.loads((MECH/'TW-A-0001-R0009/part-orientations.json').read_bytes())['bezel']['assembly_to_print'])
    parent_bezel=cq.Shape.importBrep(str(cache/'Bezel.brep'))
    bezel_cad=parent_bezel.fuse(*pads).cut(*bores).clean()
    assert bezel_cad.isValid() and len(bezel_cad.Solids())==1
    bezel=mesh(bezel_cad)
    bezel.apply_transform(pose);bezel.apply_translation(-offset)
    assert bezel.is_volume
    assign('4',bezel,'Bezel - four recessed screws')
    xml,pid,*_=obj('6')
    pts=read_mesh(xml,pid).vertices
    th=math.radians(-135);cs,sn=math.cos(th),math.sin(th)
    rot=np.array([[cs,0,sn],[0,1,0],[-sn,0,cs]])
    item=build.find(f"{CORE}item[@objectid='6']")
    xy=[float(v) for v in item.get('transform').split()[-3:-1]]
    # Bake the pose into the part. Bambu otherwise reports a rotated bounding
    # box of the old bounding box, which gives incorrect native mesh limits.
    rotor=read_mesh(xml,pid)
    rotor.vertices=pts@rot.T
    center=rotor.bounds.mean(axis=0)
    rotor.apply_translation(-center)
    assign('6',rotor,'Reel rotor - pocket facing up')
    item.set('transform',f'1 0 0 0 1 0 0 0 1 {xy[0]} {xy[1]} {rotor.extents[2]/2}')
    g,review=pcb()
    spk,motor,sr=other(cache)
    report={'pcb':review,'external_gauges':sr}
    m=mesh(g); mid=m.bounds.mean(axis=0);m.apply_translation(-mid)
    assign('108',m,'Combined PCB - populated height gauge')
    item=build.find(f"{CORE}item[@objectid='108']")
    item.set('transform',' '.join(item.get('transform').split()[:-1]+[str(m.extents[2]/2)]))
    # Duplicate the existing gauge's native placement contract on plate seven.
    def add(oid,label,m,x,y):
        assert m.is_volume and len(m.split())==1,label
        m=m.copy();m.apply_translation(-m.bounds.mean(axis=0))
        pid=str(int(oid)-1)
        node=deepcopy(resources.find(f"{CORE}object[@id='108']"));node.set('id',oid)
        component=node.find('.//'+CORE+'component')
        path=f'3D/Objects/gauge_{oid}.model'
        component.set(PROD+'path','/'+path);component.set('objectid',pid)
        xml,oldpid,_,dc,_=obj('108')
        xml.find('.//'+CORE+'object').set('id',pid)
        def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,'thai-waters/enclosure-r0003/'+oid+k))
        node.set(PROD+'UUID',uid('wrapper'));component.set(PROD+'UUID',uid('component'))
        xml.find('.//'+CORE+'object').set(PROD+'UUID',uid('mesh'));resources.append(node)
        files[path]=encode(xml)
        rel=deepcopy(rels[0]);rel.set('Id','gauge-'+oid);rel.set('Target','/'+path);rels.append(rel)
        dc=deepcopy(dc);dc.set('id',oid);p=dc.find('part');p.set('id',pid);p.set('uuid',uid('part'))
        p.find("metadata[@key='matrix']").set('value',f'1 0 0 {x} 0 1 0 {y} 0 0 1 {m.extents[2]/2} 0 0 0 1')
        config.find('plate').addprevious(dc)
        it=deepcopy(item);it.set('objectid',oid);it.set(PROD+'UUID',uid('instance'));it.set('transform',f'1 0 0 0 1 0 0 0 1 {x} {y-614.4} {m.extents[2]/2}');build.append(it)
        instance=deepcopy(plate.find('model_instance'))
        for k,v in {'object_id':oid,'identify_id':str(2000+int(oid))}.items():instance.find(f"metadata[@key='{k}']").set('value',v)
        plate.append(instance);assign(oid,m,label)
    add('142','USB lamp shelf - device part',mesh(sled),65,65)
    add('144','Speaker with gasket and lead exits',mesh(spk),100,62)
    add('146','Vibration motor and lead exit',mesh(motor),129,60)
    # Mated connector on an alternative A3. The projection down to the board
    # makes it a one-piece installation gauge. Test real withdrawal separately.
    source=MECH/'pcb-fit-r0013'
    original=trimesh.load_mesh(source/'meshes/A3-haptic.stl')
    plug=cq.Shape.importBrep(str(cache/'A3-J1-plug.brep'));x,X,y,Y,z,Z=b(plug)
    from mount import box
    sh=box(x-10.8,y+16.8,0,X-10.8,Y+16.8,Z-4.6)
    add('148','A3 alternate - plug seated',tr(manifold(original)+manifold(mesh(sh))),162,63)
    report['a3_plug_bounds']=b(plug)
    files.update({MODEL:encode(model),SETTINGS:encode(config),RELATIONSHIPS:encode(rels)})
    with ZipFile(OUT,'w') as z:
        for k,v in sorted(files.items()):z.writestr(ZipInfo(k,(2026,11,24,0,0,0)),v,compress_type=ZIP_DEFLATED)
    report['project_sha256']=sha256(OUT.read_bytes()).hexdigest()
    (HERE/'gauge-datums.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':run(Path(sys.argv[1]))
