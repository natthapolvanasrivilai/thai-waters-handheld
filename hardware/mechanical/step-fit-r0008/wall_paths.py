"""Check continuous extrusion and adjacent clear space across the two USB side faces."""
from pathlib import Path
import sys,json
from zipfile import ZipFile
import numpy as np
import trimesh
from shapely.geometry import box,MultiPoint
from housing_project import HERE,OUT,T,kit
from channels import footprints

def run(path):
    with ZipFile(OUT) as z:
        root=kit.E.fromstring(z.read(kit.MODEL))
    item=root.find(f".//{kit.CORE}item[@objectid='2']")
    xyzt=np.array(list(map(float,item.get('transform').split()[-3:])))+[0,-2,0]
    rows=[]
    for sign in (-1,1):
        for label,(near,far) in [('wall', (8.40,8.55)), ('outside',(9.06,9.26))]:
            ys=sorted((sign*near, sign*far))
            sample=trimesh.creation.box(bounds=[[-46.6,ys[0],16.6],[-40.5,ys[1],21.7]])
            sample.apply_transform(T);sample.apply_translation(xyzt)
            lo,hi=sample.bounds
            layers=footprints(path,box(lo[0]-.4,lo[1]-.4,hi[0]+.4,hi[1]+.4),lo[2]-.12,hi[2]+.12,object_id='385')
            # 0.12 mm housing layers begin above the 0.20 mm first layer, including any
            # where no deposition was found in the target. Ignore support-only interlayers.
            coverage=[]
            for j in range(1,786):
                top=round(.20+.12*j,2)
                if not lo[2]<top-.06<hi[2]:continue
                edges=trimesh.intersections.mesh_plane(sample,[0,0,1],[0,0,top-.06])
                section=MultiPoint(edges[:,:,:2].reshape(-1,2)).convex_hull
                if section.area<.06:continue
                deposited=layers.get(top,{}).get('model')
                coverage.append(0 if deposited is None else section.intersection(deposited).area/section.area)
            assert len(coverage)>50
            rows.append(dict(y_face_mm=8.76*sign,region=label,layers=len(coverage),
                             min_coverage=round(min(coverage),5),max_coverage=round(max(coverage),5)))
    return rows

if __name__=='__main__':
    directory=Path(sys.argv[1]);result={}
    for name,n in [('combined',0),('independent',1)]:
        result[name]=run(directory/f'final{n}'/'plate_1.gcode')
    print(result,flush=True)
    assert all(r['min_coverage']>.90 if r['region']=='wall' else r['max_coverage']<.001 for rows in result.values() for r in rows)
    (HERE/'wall-paths.json').write_text(json.dumps(result,indent=2)+'\n')
