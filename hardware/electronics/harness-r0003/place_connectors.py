"""Place native Molex STEP and the battery vendor's dimensioned JST PHR-2 mesh."""
from pathlib import Path
import json,struct,hashlib,math
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.ShapeFix import ShapeFix_Solid
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source-cad';OUT=ROOT/'placed';OUT.mkdir(exist_ok=True)
ORIGIN=(0,0,0)
def step(name):
    return cq.importers.importStep(str(SOURCE/(name+'.stp'))).val()
def stats(s):
    b=s.BoundingBox();return {'bbox_mm':[round(i,4) for i in (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)],'volume_mm3':round(s.Volume(),5)}
def housing_mesh(path):
    # Convert the vendor's indexed exterior triangles without changing any vertices.
    data=path.read_bytes();jsonlength=struct.unpack_from('<I',data,12)[0]
    mdl=json.loads(data[20:20+jsonlength]);raw=data[28+jsonlength:]
    primitive=mdl['meshes'][0]['primitives'][0]
    def array(idx,dtype,n):
        a=mdl['accessors'][idx];v=mdl['bufferViews'][a['bufferView']]
        return np.frombuffer(raw,dtype=dtype,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0))
    pts=array(primitive['attributes']['POSITION'],'<f4',3).reshape((-1,3))
    indices=array(primitive['indices'],'<u4',1).reshape((-1,3))
    sew=BRepBuilderAPI_Sewing(0.00002)
    for triple in indices:
        corners=[cq.Vector(*p) for p in pts[triple]]
        face=cq.Face.makeFromWires(cq.Wire.makePolygon([*corners,corners[0]]))
        if face.Area()>1e-7:sew.Add(face.wrapped)
    sew.Perform();shell=cq.Shape.cast(sew.SewedShape()).Shells()[0]
    assert shell.Closed()
    solid=cq.Solid.makeSolid(shell);s=cq.Shape.cast(ShapeFix_Solid(solid.wrapped).Solid()).clean()
    assert s.isValid()
    return s
housing=step('510210200');terminal=step('500798000');reference_header=step('532610271')
# OEM STEP supplies both a loose terminal and the illustrative crimp with lead. Keep
# the native formed crimp. Limit the source wire illustration to its barrel shoulder.
formed=max(terminal.Solids(),key=lambda s:s.Volume())
formed=formed.intersect(cq.Solid.makeBox(5,5,8,cq.Vector(-5,-2,-2)))
assert len(formed.Solids())==1
def seated(s,site):
    t=s.rotate(ORIGIN,(0,1,0),180)
    if site=='J9':return t.translate((-.690,-20.225,19.2))
    return t.rotate(ORIGIN,(0,0,1),180).translate((-25.253,21.725,19.2))
def battery(s):
    return s.rotate(ORIGIN,(1,0,0),-90).rotate(ORIGIN,(0,0,1),90).translate((26.2,-22,10.1))
shapes={};checks={}
for site in ['J7','J9']:
    key=site.lower()+'plug';shapes[key]=seated(housing,site)
    # Native cavity coordinates and formed-crimp pose taken from SD-51021-002
    # sheet 1. The 0.90 mm mating-length reference is for the compliant spring.
    for idx,offset in enumerate([-.625,.625]):
        t=formed.rotate(ORIGIN,(1,1,1),120).translate((offset-2,1.725,-.48))
        shapes[site+'-C'+str(idx+1)]=seated(t,site)
    checks[site]={'OEM_header_to_housing_native_overlap_mm3':round(reference_header.intersect(housing).Volume(),6),'registered_reference_bodies':'Molex 53261-0271 with 51021-0200','mated_section_reference_mm':5.2,'mating_contact_length_reference_mm':.9}
ph=step('C131337')
plug=housing_mesh(SOURCE/'jst-ph-2p-outline.glb').rotate(ORIGIN,(1,0,0),180).rotate(ORIGIN,(0,0,1),180).translate((-1,-.55,5.3))
shapes['ph']=battery(ph)
shapes['packplug']=battery(plug)
for key,s in shapes.items():s.exportBrep(str(OUT/(key+'.brep')))
checks['PH']={'mated_solid_intersection_mm3':round(ph.intersect(plug).Volume(),6),'source':'catalog-associated STEP and housing manufacturer-derived published exterior mesh; blind modeled cavities'}
(OUT/'terminals.json').write_text(json.dumps({'model_units':'mm','items':{k:stats(s) for k,s in shapes.items()},'reference_checks':checks,'wire_exit_faces_mm':{'J7':[[-25.878,19.75,19.05],[-24.628,19.75,19.05]],'J9':[[-1.315,-18.25,19.05],[-.065,-18.25,19.05]]}},indent=2)+'\n')
