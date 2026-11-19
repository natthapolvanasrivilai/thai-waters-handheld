"""Produce the receiver-down housing using the registered, already tessellated housing surface."""
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
OLD = HERE.with_name("TW-A-0001-R0010")
LEGACY = HERE.with_name("TW-A-0001-R0009")
NAME = "housing-battery-bay"

def load(path):
    return json.loads(path.read_text(encoding="utf8"))

def save(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n", encoding="utf8")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    meta=load(OLD/"part-orientations.json")
    for row in meta.values():
        for key in ("print_stl","assembly_brep"):
            path=(OLD/row[key]).resolve()
            row[key]="../"+path.relative_to(HERE.parent).as_posix()
    h=meta[NAME]
    old_mesh=HERE/h["print_stl"]
    assert digest(old_mesh)==h["sha256"]
    mesh=trimesh.load_mesh(old_mesh)
    mesh.apply_transform(np.linalg.inv(h["assembly_to_print"]))
    # Keep assembly X and Y. Lift the integral receiver soles onto Z=0.
    height=-mesh.bounds[0,2]
    matrix=np.eye(4)
    matrix[2,3]=height
    mesh.apply_transform(matrix)
    dest=HERE/"Print"/old_mesh.name
    dest.parent.mkdir(exist_ok=True)
    mesh.export(dest)
    h.update(original_stl=str(old_mesh.relative_to(HERE)).replace("\\","/"),
             print_stl="Print/"+dest.name,sha256=digest(dest),assembly_to_print=matrix.tolist(),
             build_up_assembly=[0,0,1],bed_face="Integral rod-grip receiver soles and closed end",
             brim="None",extents_mm=mesh.extents.round(4).tolist())
    save(HERE/"part-orientations.json",meta)

if __name__=="__main__":
    build()
