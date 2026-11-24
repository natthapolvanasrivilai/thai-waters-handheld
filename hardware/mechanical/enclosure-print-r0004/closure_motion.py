"""Sample the non-flexing bezel installation against the housing and seated A1."""
from pathlib import Path
import sys,json,numpy as np,cadquery as cq,trimesh
from trimesh.collision import CollisionManager
from interfaces import HERE
from project import mesh
def test(cache):
    body=lambda n:mesh(cq.importers.importStep(str(HERE/(n+'.step'))).val())
    fixed=CollisionManager()
    fixed.add_object('housing',body('housing'))
    for n in ('A1-touch','A1-backing','A1-carrier','A1-population'):
        fixed.add_object(n,mesh(cq.Shape.importBrep(str(cache/(n+'.brep')))))
    bezel=body('bezel')
    dx=.35; dz=.12
    segments=[[(dx,z) for z in np.linspace(8,dz,160)],[(x,dz) for x in np.linspace(dx,0,36)],[(0,z) for z in np.linspace(dz,.002,13)]]
    results=[]
    for leg in segments:
        hit=[];minimum=100
        for x,z in leg:
            mat=trimesh.transformations.translation_matrix([x,0,z])
            clash,n=fixed.in_collision_single(bezel,transform=mat,return_names=True)
            if clash:hit.append([x,z,sorted(n)])
            minimum=min(minimum,fixed.min_distance_single(bezel,transform=mat))
        results.append(dict(start=leg[0],end=leg[-1],samples=len(leg),minimum_mm=minimum,collisions=hit))
    for l in results:print(l['start'],l['end'],l['minimum_mm'],l['collisions'][:2],flush=True)
    assert not any(l['collisions'] for l in results)
    (HERE/'closure-motion.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':test(Path(sys.argv[1]))
