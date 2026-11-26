"""Measure deposited plastic and the empty pilot centers at the revised board seats."""
from pathlib import Path
from zipfile import ZipFile
import sys,json
import numpy as np
import trimesh
from shapely.geometry import MultiPoint,box
from complete_project import HERE,OUT,T,kit,E
from channels import footprints

def check(path):
    with ZipFile(OUT) as z:
        it=E.fromstring(z.read(kit.MODEL)).find(f".//{kit.CORE}item[@objectid='2']")
    off=np.array(list(map(float,it.get('transform').split()[-3:])))+[0,-2,0]
    tests=[('first screw land',37.30,-14.4,14,17.42,True),('second screw land',11.80,3.9,14,17.42,True),
           ('corner bearing land',36.95,17.99,17.11,17.44,True),('stem outer wall east',38.87,19.85,3.3,15.3,True),('stem outer wall west',36.13,19.85,3.3,15.3,True),('stem center infill',37.50,19.85,3.3,15.3,True),
           ('first pilot',36,-14.4,13.5,17.42,False),('second pilot',10.5,3.9,13.5,17.42,False)]
    result=[]
    for name,x,y,z,Z,material in tests:
        rad=.16 if material else .44
        mesh=trimesh.creation.box(bounds=[[x-rad,y-rad,z],[x+rad,y+rad,Z]])
        mesh.apply_transform(T);mesh.apply_translation(off)
        lo,hi=mesh.bounds
        paths=footprints(path,box(lo[0]-.7,lo[1]-.7,hi[0]+.7,hi[1]+.7),lo[2]-.2,hi[2]+.2,object_id='385')
        fractions=[]
        for j in range(1,790):
            top=round(.2+.12*j,2)
            if not lo[2]<top-.06<hi[2]:continue
            edges=trimesh.intersections.mesh_plane(mesh,[0,0,1],[0,0,top-.06])
            if not len(edges):continue
            sec=MultiPoint(edges[:,:,:2].reshape(-1,2)).convex_hull
            if sec.area<.02:continue
            parts=paths.get(top,{})
            kinds=['model'] if material else ['model','support']
            fractions.append(sum(sec.intersection(parts[k]).area/sec.area for k in kinds if k in parts))
        assert len(fractions)>=2
        item=dict(feature=name,layers=len(fractions),minimum=round(min(fractions),4),maximum=round(max(fractions),4))
        result.append(item)
        print(item,flush=True)
        # Report local occupancy inside the tapered stem. These fixed XY probes
        # cross raster boundaries on an inclined part and do not measure wall thickness.
        if name.startswith('stem '):
            assert item['minimum']>0,item
        else:
            assert (item['minimum']>.85 if material else item['maximum']<.001),item
    return result

if __name__=='__main__':
    root=Path(sys.argv[1])
    data={n:check(root/f'final{i}'/'plate_1.gcode') for n,i in [('full',0),('independent',1)]}
    (HERE/'mount-paths.json').write_text(json.dumps(data,indent=2)+'\n')
