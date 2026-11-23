"""Reinforce the negative-Y end of the folding-crank pocket in installed coordinates."""
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
MECH = HERE.parent
PARENT = MECH / "TW-A-0001-R0009"
V = cq.Vector

def build():
    old = cq.Shape.importBrep(str(PARENT / "CAD/rotor.brep"))
    # Follow the circular sweep. Keep 0.35 mm of front chamfer at the new lip.
    disk = cq.Solid.makeCylinder(12.75,8.5,V(49,0,14.8),V(1,0,0))
    outside = cq.Workplane(obj=disk).edges(">X").chamfer(.35).val()
    pocket = cq.Solid.makeCylinder(10.90,10,V(48,0,14.8),V(1,0,0))
    end = cq.Solid.makeBox(10,14,30,V(48,-22,0))
    # Preserve the original oblique bed land without creating material below it.
    clip = (cq.Workplane("XZ",origin=(0,20,0)).polyline([(40,-20),(65,-20),(65,11.8),(40,-13.2)])
            .close().extrude(40).val())
    band = outside.cut(pocket,clip).intersect(end)
    new = old.fuse(band).clean()
    assert new.isValid() and len(new.Solids())==1
    addition=new.cut(old)
    assert abs(old.cut(new).Volume())<1e-6 and addition.Volume()>35
    # Full 8.5 mm pocket length has a radial load path through the end centerline.
    # The axial-most chamfer reduces the minimum nominal radial section by 0.35.
    for x in (50.,53.6,56.9,57.49):
        gauge=cq.Solid.makeBox(.005,1.47,.16,V(x,-12.385,14.72))
        assert gauge.cut(new).Volume()<1e-7
    return old,new,addition

def outputs():
    old,new,added=build()
    new.exportBrep(str(HERE/"rotor.brep"))
    cq.exporters.export(new,str(HERE/"rotor.step"))
    row=json.loads((PARENT/"part-orientations.json").read_bytes())["rotor"]
    mat=np.array(row["assembly_to_print"])
    solid=new.rotate((0,0,0),(0,1,0),45).translate(tuple(mat[:3,3]))
    cq.exporters.export(solid,str(HERE/"rotor.stl"),tolerance=.012,angularTolerance=.06)
    mesh=trimesh.load_mesh(HERE/"rotor.stl")
    assert mesh.is_volume and len(mesh.split())==1 and abs(mesh.bounds[0,2])<.008
    return {"source_brep_sha256":hashlib.sha256((PARENT/"CAD/rotor.brep").read_bytes()).hexdigest(),
            "added_mm3":added.Volume(),"removed_mm3":old.cut(new).Volume(),"old_midplane_radial_mm":.5,
            "old_front_open":True,"new_radial_mm":1.85,"new_front_chamfer_min_radial_mm":1.5,
            "installed_to_print":mat.tolist(),"print_sha256":hashlib.sha256((HERE/"rotor.stl").read_bytes()).hexdigest()}
if __name__=="__main__":
    (HERE/"rotor-geometry.json").write_text(json.dumps(outputs(),indent=2)+"\n")
