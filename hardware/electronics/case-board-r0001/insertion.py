"""Evaluate a vertical installation before fitting the display and routing loose leads."""
import argparse
import json
from pathlib import Path
import numpy as np
import cadquery as cq
from motion import HERE,MOUNTS,BASE,tri,model,meshgap,maximum_drawing_pack
from fit import bounds,nearby,cyl

def run(cache, pcb=None, mounts=MOUNTS, output=None, housing=None):
    registry=json.loads((BASE/"installed-step.json").read_bytes())["components"]
    if pcb is None:
        pcb=cq.importers.importStep(str(HERE/"case-board.step")).val().rotate((0,0,0),(1,0,0),180).translate((13,-14,18.5))
    # Parts installed before the board. Caps, lid-mounted hardware and loose
    # display jumpers are fitted afterwards. Includes the dressed A3 harness.
    fixtures={"Housing","Rotor","Stem","Grip","Collar","reel0","reel1","reel2","cellAlt","bridge","tieS1","tieS2",
              "drvBoard","drvParts","motor","Speaker","H3-1","H3-2","H5","J8plug"}
    fixtures.update(n for n in registry if n.startswith(("wh","wm","A3-","A2-","tee-","w1","termination-W1")))
    b=bounds(pcb)
    b[5]+=32
    b=[q+(-3 if i%2==0 else 3) for i,q in enumerate(b)]
    targets={n:model(*tri(cq.Shape.importBrep(str(cache/(n+".brep"))))) for n in fixtures if nearby(registry[n]["bounds_mm"],b)}
    if housing is not None:
        targets["Housing"]=model(*tri(housing))
    targets["maximum pack"]=model(*tri(maximum_drawing_pack()))
    moving=model(*tri(pcb))
    minimum=(float("inf"),)
    for i in range(128):
        d=(i+.5)*.25
        moving.setTranslation(np.array([0.,0.,d]))
        minimum=min(minimum,min((meshgap(moving,m)-.125-.05,n,d) for n,m in targets.items()))
    drivers=[]
    for x,y in mounts:
        sh=model(*tri(cyl(x-87,y-114,19.35,2,26)))
        drivers.append(min((meshgap(sh,m)-.05,n) for n,m in targets.items()))
    out={"board_32mm_drop_to_installed_parts_lower_mm":minimum,"driver_4mm_shank_by_screw_lower_mm":drivers,
         "installation_stage":sorted(targets),"scope":"Footprint lowers to deliberate seating contact on the three integral supports. Approach uses the parent housing plus already installed parts. Driver test uses a 4 mm diameter straight shank with handle above the open case. Placement by hand and tooling tolerance require a fit trial."}
    print(out,flush=True)
    (output or HERE/"insertion.json").write_text(json.dumps(out,indent=2)+"\n")
    assert min(minimum[0],*(d[0] for d in drivers))>0
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("registered_cache",type=Path)
    run(p.parse_args().registered_cache)
