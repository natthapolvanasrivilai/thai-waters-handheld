"""Check the revised inert carrier against the R0012 electronics at shared device datums."""
import argparse
import hashlib
import importlib.util
import json
from zipfile import ZipFile

import numpy as np
from lxml import etree

from r19b_shell_fit import ROOT, HERE, H, R19B, manifold, tri, model, meshgap
from service_check import read_shapes

def main():
    p=argparse.ArgumentParser(description=__doc__)
    from pathlib import Path
    p.add_argument("r19b",type=Path)
    p.add_argument("baseline_breps",type=Path)
    p.add_argument("--overlay",type=Path)
    p.add_argument("--output",type=Path,default=HERE/"r20-carrier-fit.json")
    args=p.parse_args()
    assert hashlib.sha256(args.r19b.read_bytes()).hexdigest()==R19B
    source=ROOT/"hardware/mechanical/pocket-reel-r19b-removal-trial/build.py"
    spec=importlib.util.spec_from_file_location("r20_geometry",source)
    trial=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trial)
    with ZipFile(args.r19b) as z:
        definition=etree.fromstring(z.read("3D/Objects/object_61.model"))
    carrier=trial.new_carrier(trial.read_mesh(definition.find(trial.C+"resources"),"60"))
    installed=carrier.transform(np.array(trial.MATRIX[:3],dtype=float))
    mesh=trial.to_mesh(installed)
    obstacle=model(mesh.vertices,mesh.faces)
    shapes=read_shapes(args.baseline_breps)
    keys={"A2-pcb","A2-chip","A2-population","A2-sockets","drvBoard","A3-J1-header","A4-integration",
          "A5-power","w1VCC","w1GND","w1SDA","w1SCL"}
    if args.overlay:
        import cadquery as cq
        for row in json.loads(args.overlay.read_bytes())["add"]:
            src=args.overlay.parent/row["brep"]
            assert hashlib.sha256(src.read_bytes()).hexdigest()==row["sha256"]
            shapes[row["name"]]=cq.Shape.importBrep(str(src))
            keys.add(row["name"])
    carrier_min,carrier_max=np.asarray(mesh.vertices).min(axis=0),np.asarray(mesh.vertices).max(axis=0)
    results={}
    for k in sorted(keys):
        shape=shapes[k]
        nearest=float("inf");total=0;unresolved=0
        disjoint=0
        for solid in shape.Solids():
            v,t=tri(solid)
            nearest=min(nearest,meshgap(model(v,t),obstacle))
            if args.overlay:
                box=solid.BoundingBox()
                low=np.array((box.xmin,box.ymin,box.zmin))
                high=np.array((box.xmax,box.ymax,box.zmax))
                if np.any(low>carrier_max+1e-5) or np.any(high<carrier_min-1e-5):
                    disjoint+=1
                    continue
            part=manifold(v,t)
            if part is None:unresolved+=1
            else:total+=(installed^part).volume()
        results[k]=dict(surface_gap_mm=round(nearest,5),common_volume_mm3=round(total,5),unresolved_solids=unresolved)
        if args.overlay:
            results[k]["solids_proven_disjoint_by_native_bounds"]=disjoint
    out=dict(r19b_sha256=R19B, carrier_rebuild_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             installed_transform=trial.MATRIX,tests=results,scope="Mixed-lineage registration study at nominal seated position; A2 and W1 pose comes from R0012. Positive common volumes require reconciliation before combining configurations.")
    if args.overlay:
        out["overlay_sha256"]=hashlib.sha256(args.overlay.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(out,indent=2)+"\n")
    if any(r["common_volume_mm3"]>1e-5 or r["unresolved_solids"] for r in results.values()):
        raise RuntimeError("Carrier reconciliation required")
    print(json.dumps(results),flush=True)
if __name__=="__main__":
    main()
