"""Build the independently mounted assembly and intersect it with the registered R0017 solids."""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq
from build import HERE, MOUNTS, REST
from leads import installed

ROOT = HERE.parents[2]
BASE = ROOT / "hardware/mechanical/TW-A-0001-R0017"
REF = json.loads((BASE/"installed-step.json").read_bytes())
FLOOR,SEAT,BACK = 2.5,17.7,18.5
OLD = {"A4-integration","A4-spacers","A4-bond","A5-power","A5-spacers","A5-bond"}

def bounds(s):
    b = s.BoundingBox()
    return [getattr(b,k) for k in ("xmin","xmax","ymin","ymax","zmin","zmax")]

def nearby(a,b,gap=.001):
    return all(a[i]<=b[i+1]+gap and b[i]<=a[i+1]+gap for i in (0,2,4))

def check(shapes,others):
    results={}
    for key,shape in shapes.items():
        hits={}
        for solid in shape.Solids():
            a=bounds(solid)
            for name,parts in others.items():
                for part,b in parts:
                    if nearby(a,b):
                        vol=sum(v.Volume() for v in solid.intersect(part).Solids())
                        if vol>1e-5:hits[name]=hits.get(name,0)+vol
        results[key]={k:round(v,5) for k,v in hits.items()}
        print(key,results[key],flush=True)
    return results

def cyl(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))

def support(x,y,index):
    if index==3:
        return cq.Solid.makeCone(2.05,1.75,15.6,cq.Vector(x,y,2.1))
    if index==2:
        # Carry the pilot above the haptic board. The foot is set back toward
        # +Y so the board edge is clear below Z6.11; the ramp grows at 62 deg.
        foot=cyl(x,y+2.5,2.1,2.05,5.0)
        a=cq.Wire.makeCircle(2.05,cq.Vector(x,y+2.5,7.1),cq.Vector(0,0,1))
        b=cq.Wire.makeCircle(2.05,cq.Vector(x,y,12.1),cq.Vector(0,0,1))
        stock=foot.fuse(cq.Solid.makeLoft([a,b],True),cyl(x,y,12.1,2.05,5.6)).clean()
    else:
        stock=cyl(x,y,2.1,2.05,15.6)
    return stock.cut(cyl(x,y,13.2,.82,4.6)) if index in (1,2) else stock

def main(cache,step):
    source=HERE/"case-board.step"
    pcb=cq.importers.importStep(str(source)).val().rotate((0,0,0),(1,0,0),180).translate((13,-14,BACK))
    screw=cq.importers.importStep(str(ROOT/"hardware/components/standard-fasteners/4mm.step")).val()
    screws={}
    posts={}
    for i,(kx,ky) in enumerate(MOUNTS,1):
        x,y=kx-87,ky-114
        screws[f"screw {i}"]=screw.translate((x,y,BACK))
        posts[f"boss {i}"]=support(x,y,i)
    posts["third rest"]=support(*REST,3)
    leads, specs=installed()
    solids={"populated board":pcb,**screws,**posts,**leads}
    # All registered assembly members are considered in the broad phase.
    area=[bounds(s) for s in solids.values()]
    needed={n for n,r in REF["components"].items() if n not in OLD and
            any(nearby(b,r["bounds_mm"],.02) for b in area)}
    if step:
        assert hashlib.sha256(step.read_bytes()).hexdigest()==REF["step_sha256"]
        cache.mkdir(exist_ok=True,parents=True)
        for child in cq.Assembly.load(str(step)).children:
            child.obj.moved(child.loc).exportBrep(str(cache/(child.name+".brep")))  # Include the full display and lower fixtures for motion checks.
    others={}
    for name in sorted(needed):
        s=cq.Shape.importBrep(str(cache/(name+".brep")))
        assert max(abs(a-b) for a,b in zip(bounds(s),REF["components"][name]["bounds_mm"]))<.02,name
        others[name]=[(p,bounds(p)) for p in s.Solids()]
    case=others["Housing"][0][0]
    housing=case.fuse(*posts.values()).clean()
    assert len(housing.Solids())==1 and housing.isValid()
    cq.exporters.export(housing,str(HERE/"housing.step"))
    asm=cq.Assembly(name="Case_mounted_control_and_power")
    asm.add(housing,name="Housing with integral supports",color=cq.Color(.47,.60,.52))
    asm.add(pcb,name="Control and power board",color=cq.Color(.14,.39,.28))
    for name,s in leads.items():
        asm.add(s,name=name,color=cq.Color(.20,.20,.19) if name.startswith("W3") else cq.Color(.72,.33,.17))
    for name,s in screws.items():asm.add(s,name=name,color=cq.Color(.72,.73,.72))
    asm.export(str(HERE/"case-mount-assembly.step"))
    print("CAD ready; board extents",bounds(pcb),flush=True)
    previous=check({"populated board":pcb},{n:v for n,v in others.items() if n.startswith("A5-W")})
    retained={}
    for name,items in others.items():
        if name.startswith(("A5-W2","A5-W3","A5-W7")) and not name.endswith("cover"):
            if name.endswith("solder"):
                retained[name+" fixed joint"]=[(s,b) for s,b in items if b[1]<0]
        else:
            retained[name]=items
    seated=check({"populated board":pcb,**screws},retained)
    lead_fit=check(leads,{**retained,**{n:[(s,bounds(s)) for s in part.Solids()] for n,part in solids.items() if n not in leads}})
    neighbours={}
    for a in ("W2","W3","W7"):
        peers={n:[(s,bounds(s))] for n,s in leads.items() if not n.startswith(a)}
        neighbours.update(check({n:s for n,s in leads.items() if n.startswith(a)},peers))
    post=check(posts,{n:v for n,v in retained.items() if n!="Housing"})
    internal=check({"populated board":pcb},{n:[(s,bounds(s))] for n,s in {**posts,**screws}.items()})
    report=dict(reference_sha256=REF["step_sha256"],pcb_step_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                installed_pcb_bounds_mm=bounds(pcb),tested_reference_members=sorted(needed),
                seated_overlaps_mm3=seated,support_overlaps_mm3=post,board_mount_overlaps_mm3=internal,
                legacy_board_intersections_mm3=previous,lead_routes=specs,lead_overlaps_mm3=lead_fit,inter_lead_overlaps_mm3=neighbours,
                note="Nominal static BRep intersection. Bosses fuse to housing. Screws form threads in the printed pilots. Legacy solder, leads and their intentional land contacts are included.")
    (HERE/"fit.json").write_text(json.dumps(report,indent=2)+"\n")
    assert not any(seated.values()) and not any(post.values()) and not any(internal.values())
    assert not any(neighbours.values())
    for name,hits in lead_fit.items():
        if name=="W2 copper":
            assert set(hits)=={"A1-J8"} and 0<hits["A1-J8"]<.001
        else:
            assert not hits,(name,hits)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache",type=Path)
    parser.add_argument("--registered-step",type=Path)
    args=parser.parse_args()
    main(args.cache,args.registered_step)
