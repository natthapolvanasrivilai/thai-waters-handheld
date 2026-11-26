"""Compare native beads with a section through each layer of small working features."""
import sys,json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as E
import numpy as np
import trimesh
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from project import HERE,OUT
sys.path.insert(0,str(HERE.parent/'pocket-reel-r19b-removal-trial'))
from path_evidence import inspect
sys.path.insert(0,str(HERE.parent/'reel-dfm-r0001'))
from thickness import affine
def test(directory):
    names={16:'grip screw keeper',18:'receiver nut keeper',28:'diffuser and flange',
           32:'USB mask perimeter',14:'keyed power cap',114:'RGB board and emitter'}
    records=[]
    with ZipFile(OUT) as z:
        cfg=E.fromstring(z.read('Metadata/model_settings.config'))
        model=E.fromstring(z.read('3D/3dmodel.model'))
        for idx,plate in enumerate(cfg.findall('plate')):
            for inst in plate.findall('model_instance'):
                oid=int(inst.find("metadata[@key='object_id']").get('value'))
                if oid not in names:continue
                instance=inst.find("metadata[@key='identify_id']").get('value')
                c=model.find(f".//{{*}}object[@id='{oid}']/{{*}}components/{{*}}component")
                fn=next(v.lstrip('/') for k,v in c.attrib.items() if k.endswith('}path'))
                data=E.fromstring(z.read(fn)).find('.//{*}mesh')
                v=[[float(i.get(k)) for k in 'xyz'] for i in data.find('{*}vertices')]
                f=[[int(i.get(k)) for k in ('v1','v2','v3')] for i in data.find('{*}triangles')]
                m=trimesh.Trimesh(v,f)
                item=model.find(f".//{{*}}item[@objectid='{oid}']")
                m.apply_transform(affine(item.get('transform'))@affine(c.get('transform')))
                m.apply_translation([-307.2*(idx%3),307.2*(idx//3)-2.,0])
                def observer(id,layers):
                    prev=0.;detail=[]
                    for z,lines in sorted(layers.items()):
                        plane=m.section(plane_origin=[0,0,(prev+z)/2],plane_normal=[0,0,1])
                        prev=z
                        if plane is None:continue
                        rings=[Polygon(p[:,:2]).buffer(0) for p in plane.discrete]
                        shape=Polygon()
                        for r in rings:shape=shape.symmetric_difference(r)
                        actual=unary_union([LineString(pts).buffer(w/2) for w,pts in lines])
                        # Each nominal island must keep a real path throughout its core.
                        comps=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
                        fillings=[actual.intersection(p).area/p.area for p in comps if p.area>.03]
                        holes=[Polygon(r) for p in comps for r in p.interiors if Polygon(r).area>1]
                        holes_open=all(not actual.covers(h.representative_point()) for h in holes)
                        detail.append(dict(z_mm=z,smallest_island_coverage=round(min(fillings,default=1),3),open_holes=len(holes) if holes_open else -1,shape_mm2=round(shape.area,2),bead_mm2=round(actual.area,2)))
                    records.append(dict(part=names[oid],layers=detail))
                inspect(directory/f'plate_{idx+1}.gcode',True,focus={instance},layer_observer=observer)
    (HERE/'fine-features.json').write_text(json.dumps(records,indent=2)+'\n')
    for r in records:
        print(r['part'],min(i['smallest_island_coverage'] for i in r['layers']),min(i['open_holes'] for i in r['layers']),flush=True)
        assert all(i['smallest_island_coverage']>.65 and i['open_holes']>=0 for i in r['layers']),r
if __name__=='__main__':test(Path(sys.argv[1]))
