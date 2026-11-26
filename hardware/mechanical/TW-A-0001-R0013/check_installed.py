"""Verify the changed A3 and W4 geometry against the seated STEP, including both pack variants."""
import argparse
import gzip
import shutil
import sys
from pathlib import Path

import cadquery as cq

from assemble import HERE, ROOT, PREVIOUS, digest, load, save
sys.path.insert(0, str(ROOT/"hardware/verification/r0012"))
from installed_fit import separation
from service_check import maximum_drawing_pack

def nearest_parts(moving, fixed, shapes, boxes, solid_cache):
    # PCB exports contain hundreds of discrete solids, and a long loom crosses
    # their combined bounding boxes. Use exact solid distances after pruning
    # with their individual lower bounds; retain every zero-distance neighbor.
    import numpy as np
    def xyz(box):
        return [box.xmin,box.ymin,box.zmin],[box.xmax,box.ymax,box.zmax]
    def solids(key):
        if key not in solid_cache:
            pieces=shapes[key].Solids()
            solid_cache[key]=(pieces,np.array([xyz(s.BoundingBox()) for s in pieces]))
        return solid_cache[key]
    parts,a=solids(moving)
    best=(float("inf"),"")
    touched=[]
    for bound,key in sorted((separation(boxes[moving],boxes[k]),k) for k in fixed):
        if bound>best[0]+1e-5:break
        others,b=solids(key)
        gaps=np.linalg.norm(np.maximum(0,np.maximum(a[:,None,0]-b[None,:,1],b[None,:,0]-a[:,None,1])),axis=2)
        volume=0
        contact=False
        for index in np.argsort(gaps,axis=None):
            i,j=np.unravel_index(index,gaps.shape)
            if gaps[i,j]>best[0]+1e-5:break
            distance=parts[i].distance(others[j])
            best=min(best,(distance,key))
            if distance<1e-5:
                contact=True
                volume+=parts[i].intersect(others[j]).Volume()
        if contact:touched.append({"component":key,"common_volume_mm3":round(volume,6)})
    return {"minimum_nominal_mm":round(best[0],5),"closest":best[1],"touch_or_overlap":touched}

def check(packed, scratch):
    export = load(HERE/"export-verification.json")
    assert digest(packed) == export["packed_step_sha256"]
    scratch.mkdir(exist_ok=True, parents=True)
    path=scratch/"installed-r0013.step"
    with gzip.open(packed,"rb") as src, path.open("wb") as dst:
        shutil.copyfileobj(src,dst)
    assert digest(path) == export["step_sha256"]
    assembly = cq.Assembly.load(str(path))
    shapes = {s.name:s.obj.moved(s.loc) for s in assembly.children}
    assert set(shapes)==set(load(HERE/"installed-step.json")["components"])
    shapes["cellDrawing"] = maximum_drawing_pack()
    boxes = {k:v.BoundingBox() for k,v in shapes.items()}
    checks={}
    cache={}
    def assess(key, group):
        result=nearest_parts(key,group,shapes,boxes,cache)
        print(key,result,flush=True)
        return result
    installed = ["Housing","Bezel","A4-integration","A5-power","A1-carrier","A1-population",
                 "A1-backing","bridge","cellAlt","cellDrawing","motor","A2-pcb","J8plug"]
    changed=export["added_nodes"]
    for battery in ("cellDrawing","cellAlt"):
        checks[battery]=assess(battery,changed+["Housing","bridge","Bezel"])
    checks["drvParts"] = assess("drvParts",installed+["A3-J1-spacer","A3-J1-header","A3-J1-plug",
        "A3-J1-TPA",*[k for k in changed if k.startswith("wh")]])
    checks["A5 board"] = assess("A5-power", [k for k in shapes if k != "A5-power" and not k.startswith("A5-")])
    for name in changed:
        if name.startswith("wh"):
            checks[name]=assess(name,installed+["drvBoard","drvParts","A3-J1-spacer"])
    for k,v in checks.items():
        print(k,v,flush=True)
    save(HERE/"QA/installed-fit.json",{"step_sha256":digest(path),"checked_members":len(assembly.children),
         "seated":checks,"maximum_pack_mm":[35.3,62.3,5.3],
         "scope":"Nominal solids. Intended joints and connector internals are assessed separately in the service study. The two packs are alternative installations."})
    if any(item["common_volume_mm3"]>0.00001 for check in checks.values() for item in check["touch_or_overlap"]):
        raise RuntimeError("Seated physical interference recorded in the fit report.")

if __name__ == "__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("packed",type=Path);cli.add_argument("scratch",type=Path)
    args=cli.parse_args()
    check(args.packed,args.scratch)
