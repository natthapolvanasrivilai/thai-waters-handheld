"""Sweep the CviLux service path and rigid screen lift against the case-board changes."""
import argparse
import json
import math
from pathlib import Path
import sys
import cadquery as cq
import numpy as np
from fit import HERE,ROOT,MOUNTS,BASE,REST,support
from leads import installed

# The R0013 study imports its own sibling "build" module.
sys.modules.pop("build",None)
sys.path.insert(0,str(BASE.with_name("TW-A-0001-R0013")))
sys.path.insert(1,str(BASE.with_name("TW-A-0001-R0012")))
from intervals import pole_motion,ribbon
from stroke import new_leads
from service_check import meshgap,model,tri,maximum_drawing_pack

def run(cache):
    cad=lambda n:cq.Shape.importBrep(str(cache/(n+".brep")))
    pcb=cq.importers.importStep(str(HERE/"case-board.step")).val().rotate((0,0,0),(1,0,0),180).translate((13,-14,18.5))
    screws=cq.importers.importStep(str(ROOT/"hardware/components/standard-fasteners/4mm.step")).val()
    fixed={"PCB":pcb,"rest":support(*REST,3)}
    for i,(x,y) in enumerate(MOUNTS,1):
        fixed[f"boss {i}"]=support(x-87,y-114,i)
        fixed[f"screw {i}"]=screws.translate((x-87,y-114,18.5))
    rigid_names=set(fixed)
    fixed.update(installed()[0])
    shapes={k:model(*tri(s)) for k,s in fixed.items()}
    wire=new_leads()
    body,latch=wire.split_latch(cad("A3-J1-plug"))
    old=BASE.with_name("TW-A-0001-R0013")
    members=json.loads((old/"clearance.json").read_bytes())["rigid_members"][1:]
    moving=model(*tri(cq.Compound.makeCompound([body,*[cad(n) for n in members]])))
    def closest(obj,targets):
        return min((meshgap(obj,s),k) for k,s in targets.items())
    report={}
    # Midpoint bounds are distance minus the maximum travel to an endpoint, and
    # a 0.05 mm numerical mesh allowance for the pair of tessellated surfaces.
    rigid=(float("inf"),)
    radius=max(math.hypot(y-wire.PIVOT[1],z-wire.PIVOT[2]) for y in (latch.BoundingBox().ymin,latch.BoundingBox().ymax)
               for z in (latch.BoundingBox().zmin,latch.BoundingBox().zmax))
    for i in range(16):
        u=(i+.5)/16
        g,n=closest(model(*tri(wire.actuate(latch,u))),shapes)
        rigid=min(rigid,(g-.05-radius*abs(math.radians(wire.RELEASE_DEG))/32,n,"latch",u))
    released=model(*tri(wire.actuate(latch,1)))
    for i in range(66):
        d=(i+.5)*.125
        for obj in (moving,released):
            obj.setTranslation(np.array([0.,d,0.]))
            g,n=closest(obj,shapes)
            rigid=min(rigid,(g-.0625-.05,n,"withdrawal",d))
    report["rigid_CviLux_to_changes_mm"]=rigid
    params=wire.bernstein(7,np.linspace(0,1,97))
    routes=json.loads((ROOT/"hardware/electronics/harness-r0006/routing.json").read_bytes())
    best=(float("inf"),)
    for i in range(132):
        a,b=i*.0625,(i+1)*.0625
        for net in wire.NET_PIN:
            tx,_,z=routes[net]["tap_center_mm"]
            poles,displacement=pole_motion(wire,net,tx,z,a,b)
            pts=params@poles
            err=42*np.linalg.norm(np.diff(poles,n=2,axis=0),axis=1).max()/(8*96**2)
            barrel=[pts[0,0],-5.35+(a+b)/2,10.36]
            g,n=closest(ribbon(np.concatenate([[barrel],pts])),shapes)
            best=min(best,(g-displacement-err-wire.JACKET_OD/2-.05,n,net,a,b))
    report["flexible_CviLux_jackets_to_changes_mm"]=best
    pack=model(*tri(maximum_drawing_pack()))
    report["drawing_maximum_pack_to_changes_mm"]=closest(pack,shapes)
    display=[cad(n) for n in json.loads((BASE/"installed-step.json").read_bytes())["components"] if n.startswith("A1-")]
    screen=model(*tri(cq.Compound.makeCompound(display)))
    bound=(float("inf"),)
    for i in range(72):
        d=(i+.5)*.25
        screen.setTranslation(np.array([0.,0.,d]))
        g,n=closest(screen,{k:s for k,s in shapes.items() if k in rigid_names})
        bound=min(bound,(g-.125-.05,n,d))
    report["rigid_display_18mm_lift_to_new_mount_mm"]=bound
    report["scope"]="Conservative midpoint allowances on nominal triangulated CAD. Display check covers rigid parts with electrical leads disconnected. Drawing-maximum pack uses geometric surface distance. Check physical fit, driver access, release force and harness service loop separately."
    print(report,flush=True)
    (HERE/"motion.json").write_text(json.dumps(report,indent=2)+"\n")
    assert min(rigid[0],best[0],bound[0],report["drawing_maximum_pack_to_changes_mm"][0])>0
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("cache",type=Path)
    run(p.parse_args().cache)
