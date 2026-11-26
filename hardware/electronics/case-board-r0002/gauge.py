"""Build the component-height gauge from the PCB STEP, then export a single SuperTack plate."""
import math, sys, json
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
import numpy as np
import trimesh
from mount import HERE, ROOT, stock, cq
from layout import LIMITS, RADIUS, SCREWS
SOURCE=ROOT/'hardware/mechanical/step-fit-r0008'
OUT=HERE/'Case-board-R0002-PolyTerra-SuperTack-X1C.3mf'
CORE='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'

def make_gauge():
    x,y,X,Y=LIMITS
    center=((x+X)/2-13,-14-(y+Y)/2,-.04)
    body=cq.Workplane('XY',origin=center).box(X-x,Y-y,.84,centered=(True,True,False)).edges('|Z').fillet(RADIUS).val()
    for x,y in SCREWS:
        body=body.cut(cq.Solid.makeCylinder(1.15,1.2,cq.Vector(x-13,-14-y,-.12)))
    packages=[s for s in stock(HERE/'case-board.step').Solids() if s.BoundingBox().zmax>.81]
    boxes=[]
    for s in packages:
        b=s.BoundingBox()
        top=math.ceil((b.zmax+.04-.00001)/.2)*.2-.04
        boxes.append(cq.Solid.makeBox(b.xlen,b.ylen,top-.78,cq.Vector(b.xmin,b.ymin,.78)))
    body=body.fuse(*boxes).clean()
    assert len(packages)>25 and body.isValid() and len(body.Solids())==1
    assert max(s.cut(body).Volume() for s in packages)<.001
    cq.exporters.export(body,str(HERE/'pcb-gauge.step'))

def emit():
    path='3D/Objects/gauge_108.model'
    with ZipFile(next(SOURCE.glob('*.3mf'))) as z:
        files={k:z.read(k) for k in z.namelist() if not k.startswith('3D/Objects/') or k==path}
    verts,faces=stock(HERE/'pcb-gauge.step').tessellate(.008,.07)
    v,ids=np.unique(np.round([p.toTuple() for p in verts],8),axis=0,return_inverse=True)
    f=ids[np.array(faces)]
    assert trimesh.Trimesh(v,f,process=False).is_volume
    center=(v.max(0)+v.min(0))/2
    def xml(key):return E.fromstring(files[key])
    def save(key,r):files[key]=E.tostring(r,encoding='UTF-8',xml_declaration=True)
    def remove(nodes):
        for n in nodes:n.getparent().remove(n)
    root=xml(path)
    mesh=root.find('.//'+CORE+'mesh')
    for n in mesh:n.clear()
    for p in v-center:E.SubElement(mesh[0],CORE+'vertex',**dict(zip('xyz',map(str,p))))
    for face in f:E.SubElement(mesh[1],CORE+'triangle',**dict(zip(('v1','v2','v3'),map(str,face))))
    save(path,root)
    key='3D/3dmodel.model';m=xml(key)
    remove(m.xpath('//*[local-name()="object" and @id!="108"] | //*[local-name()="item" and @objectid!="108"]'))
    item=m.find('.//'+CORE+'item')
    item.set('transform',f'1 0 0 0 1 0 0 0 1 128 128 {center[2]-v[:,2].min():.8f}')
    save(key,m)
    key='Metadata/model_settings.config';cfg=xml(key)
    remove(cfg.xpath('object[@id!="108"] | plate[not(metadata[@key="plater_id" and @value="7"])] | plate/model_instance[not(metadata[@key="object_id" and @value="108"])]'))
    for n in cfg.xpath('object//metadata[@key="name"]'):n.set('value','Rectangular control PCB - component-height gauge')
    cfg.find('object/part/mesh_stat').set('face_count',str(len(f)))
    for k,val in [('plater_id','1'),('plater_name','Gray PLA - rectangular case board')]:
        cfg.find(f'plate/metadata[@key="{k}"]').set('value',val)
    save(key,cfg)
    key='3D/_rels/3dmodel.model.rels';rels=xml(key)
    remove([n for n in rels if n.get('Target')!='/'+path]);save(key,rels)
    for k in ('Metadata/cut_information.xml','Metadata/layer_config_ranges.xml'):save(k,E.Element('objects'))
    with ZipFile(OUT,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for k in sorted(files):z.writestr(k,files[k])

if __name__=='__main__':
    make_gauge()
    emit()
