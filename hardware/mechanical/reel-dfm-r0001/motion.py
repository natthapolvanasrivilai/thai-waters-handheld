"""Test only the new material against the existing folding parts and complete reel rotation."""
import argparse
import json
import math

import cadquery as cq
import fcl
import numpy as np
from rotor import HERE,V,build
from pathlib import Path

def collision_mesh(s):
    v,f=s.tessellate(.008,.055)
    m=fcl.BVHModel()
    m.beginModel(len(v),len(f))
    m.addSubModel(np.array([p.toTuple() for p in v]),np.array(f))
    m.endModel()
    return fcl.CollisionObject(m)

def run(cache):
    _,_,addition=build()
    target=collision_mesh(addition)
    report={}
    for name in ("Stem","Grip","reel1"):
        s=cq.Shape.importBrep(str(cache/(name+".brep")))
        mesh=collision_mesh(s)
        b=s.BoundingBox()
        pivot=np.array([53.6,7.8,0])
        radius=max(math.hypot(x-pivot[0],y-pivot[1]) for x in (b.xmin,b.xmax) for y in (b.ymin,b.ymax))
        minimum=(1e4,0)
        for deg in np.arange(0,90.01,.25):
            a=math.radians(deg)
            rot=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
            mesh.setTransform(fcl.Transform(rot,pivot-rot@pivot))
            dist=fcl.distance(mesh,target,fcl.DistanceRequest(),fcl.DistanceResult())
            minimum=min(minimum,(dist,float(deg)))
        lower=minimum[0]-.025-radius*math.radians(.125)
        report[name]=dict(min_sample_mm=minimum[0],fold_degrees=minimum[1],continuous_mesh_lower_mm=lower)
    # All added stock is contained in this axially aligned annulus in every spin position.
    swept=cq.Solid.makeCylinder(12.75,8.5,V(49,0,14.8),V(1,0,0)).cut(cq.Solid.makeCylinder(10.90,8.5,V(49,0,14.8),V(1,0,0)))
    for name in ("Housing","Bezel"):
        s=cq.Shape.importBrep(str(cache/(name+".brep")))
        report[name]={"full_spin_annulus_clearance_mm":s.distance(swept),"common_mm3":s.intersect(swept).Volume()}
    import sys
    sys.path.insert(0,str(HERE.parents[1]/"electronics/case-board-r0001"))
    from fit import support
    from build import MOUNTS,REST
    seats=[(x-87,y-114) for x,y in MOUNTS]+[REST]
    report["Case-board posts"]={"full_spin_annulus_clearance_mm":
        min(support(x,y,i).distance(swept) for i,(x,y) in enumerate(seats,1))}
    assert report["Case-board posts"]["full_spin_annulus_clearance_mm"]>1
    print(report,flush=True)
    assert min(report[n]["continuous_mesh_lower_mm"] for n in ("Grip","Stem","reel1"))>.15
    assert all(report[n]["common_mm3"]<1e-6 and report[n]["full_spin_annulus_clearance_mm"]>.25 for n in ("Housing","Bezel"))
    (HERE/"fold-and-spin.json").write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("registered_brep_cache",type=Path)
    run(p.parse_args().registered_brep_cache)
