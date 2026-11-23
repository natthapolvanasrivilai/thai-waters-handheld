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
    results={}
    for k in ("A2-pcb","A2-chip","A2-population","A2-sockets","drvBoard","A3-J1-header","A4-integration",
              "A5-power","w1VCC","w1GND","w1SDA","w1SCL"):
        shape=shapes[k]
        nearest=float("inf");total=0;unresolved=0
        for solid in shape.Solids():
            v,t=tri(solid)
            nearest=min(nearest,meshgap(model(v,t),obstacle))
            part=manifold(v,t)
            if part is None:unresolved+=1
            else:total+=(installed^part).volume()
        results[k]=dict(surface_gap_mm=round(nearest,5),common_volume_mm3=round(total,5),unresolved_solids=unresolved)
    out=dict(r19b_sha256=R19B, carrier_rebuild_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             installed_transform=trial.MATRIX,tests=results,scope="Mixed-lineage registration study at nominal seated position; A2 and W1 pose comes from R0012. Positive common volumes require reconciliation before combining configurations.")
    (HERE/"r20-carrier-fit.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(results),flush=True)
if __name__=="__main__":
    main()
