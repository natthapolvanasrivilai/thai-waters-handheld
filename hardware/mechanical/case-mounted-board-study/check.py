"""Screen a case-mounted A4/A5 replacement against the registered R0017 assembly."""
import argparse
import hashlib
import json
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.with_name("TW-A-0001-R0017") / "installed-step.json"
OLD = {"A4-integration","A4-spacers","A4-bond","A5-power","A5-spacers","A5-bond"}
FLOOR, SEAT, THICKNESS = 2.50, 17.70, .80
SCREWS = [(35.,-11.5),(15.5,10.)]
REST = (29.,12.8)
METAL_HEAD_RADIUS, METAL_HEAD_HEIGHT = 1.95, 1.60
EPS = 1e-5

def box(x,y,z,w,l,h):
    return cq.Solid.makeBox(w,l,h,cq.Vector(x,y,z))

def cyl(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))

def common(a,b):
    return sum(s.Volume() for s in a.intersect(b).Solids())

def near(b,c,gap):
    return all(getattr(b,k+"min")-gap <= getattr(c,k+"max") and
               getattr(c,k+"min")-gap <= getattr(b,k+"max") for k in "xyz")

def geometry():
    pcb = box(13,-14,SEAT,24.5,33,THICKNESS)
    edges=[edge for edge in pcb.Edges() if edge.BoundingBox().zlen>.79]
    pcb=pcb.fillet(1.,edges)
    parts={}
    for i,(x,y) in enumerate(SCREWS,1):
        pcb=pcb.cut(cyl(x,y,SEAT-.02,1.15,THICKNESS+.04))
        raw=cyl(x,y,FLOOR-.40,2.15,SEAT-FLOOR+.40)
        parts[f"boss {i}"]=raw.cut(cyl(x,y,SEAT-5.2,.82,5.21))
        parts[f"head envelope {i}"]=cyl(x,y,SEAT+THICKNESS,METAL_HEAD_RADIUS,METAL_HEAD_HEIGHT)
    parts["third bearing"]=cyl(*REST,FLOOR-.40,2.15,SEAT-FLOOR+.40)
    parts["blank PCB"]=pcb
    return parts

def run(source):
    reference=json.loads(REFERENCE.read_bytes())

    sha=hashlib.sha256()
    with source.open("rb") as f:
        for buf in iter(lambda:f.read(1024*1024),b""): sha.update(buf)
    assert sha.hexdigest()==reference["step_sha256"]
    scene=cq.Assembly.load(str(source))
    assert len(scene.children)==reference["component_count"]
    pieces=geometry()
    bounds=[s.BoundingBox() for s in pieces.values()]
    existing={}
    case=None
    for child in scene.children:
        if child.name in OLD:continue
        solid=child.obj.moved(child.loc)
        if not child.name.startswith("A1-") and not any(near(b,solid.BoundingBox(),3.) for b in bounds):continue
        if child.name=="Housing":case=solid
        existing[child.name]=[(s,s.BoundingBox()) for s in solid.Solids()]
    assert case is not None
    def probe(shape,skip=(),gap=1.):
        bound=shape.BoundingBox()
        hits={}
        closest=gap
        pair=None
        for name,solids in existing.items():
            if name in skip:continue
            for item,b in solids:
                if not near(bound,b,gap):continue
                distance=shape.distance(item)
                if distance<closest:
                    closest,pair=distance,name
                if distance<1e-6:
                    v=common(shape,item)
                    if v>EPS: hits[name]=hits.get(name,0)+v
        return dict(overlap_mm3={n:round(v,5) for n,v in hits.items()},
                    nearest_within_search_mm=round(closest,5) if pair else None,nearest_member=pair,search_radius_mm=gap)
    checks={}
    for name,shape in pieces.items():
        post=name.startswith("boss") or name=="third bearing"
        # Only the first 0.40 mm of each post is intentionally fused into the floor.
        tested=shape.cut(box(0,-30,-10,60,60,FLOOR+10.0001)) if post else shape
        checks[name]=probe(tested,skip=["Housing"] if post else [])
        if post:
            stock=common(shape,case)
            expected=3.141592653589793*2.15**2*.40
            assert abs(stock-expected)<1e-4,(name,stock)
            checks[name]["floor_root_common_mm3"]=round(stock,5)
            assert common(tested,case)<EPS
        print(name,checks[name],flush=True)
    # A conservative unperforated sweep of each fixed solid, relative to a
    # straight upward lift of A1. This checks the complete stroke, not just
    # the seated/removed endpoints. The display harness is a separate task.
    display_checks={}
    display_skips=[name for name in existing if not name.startswith("A1-")]
    for name,shape in pieces.items():
        b=shape.BoundingBox()
        if name=="blank PCB":
            env=box(b.xmin,b.ymin,b.zmin-18,b.xlen,b.ylen,b.zlen+18)
        else:
            env=cyl(b.center.x,b.center.y,b.zmin-18,b.xlen/2,b.zlen+18)
        display_checks[name]=probe(env,display_skips)
    print("Display sweep",display_checks,flush=True)
    assert all(not entry["overlap_mm3"] for entry in display_checks.values())
    assert all(all(hit.startswith("A5-W") for hit in entry["overlap_mm3"]) for entry in checks.values()),checks
    # Test the old positions independently with simple full-size feet.
    rejected={}
    for group,z,centres in [("A4",18.5,[(15.5,-10),(33.5,-9.5),(33.5,-1.5)]),
                            ("A5",17.8,[(17.5,16.5),(28.5,14.1),(32.5,17.3)])]:
        for i,(x,y) in enumerate(centres,1):
            rejected[f"{group} foot {i}"]=probe(box(x-1.5,y-1.5,FLOOR+.001,3,3,z-FLOOR-.001),
                                                 skip=["Housing"],gap=.001)["overlap_mm3"]
    assert sum(bool(v) for v in rejected.values())==5
    asm=cq.Assembly(name="Case_mount_feasibility")
    # Include an actual cutaway of the reference housing floor so the STEP
    # shows which structure supports the PCB. The three posts are integral.
    floor_patch=case.intersect(box(8,-18,-3.21,34,41,5.71))
    floor_patch=floor_patch.fuse(pieces["boss 1"],pieces["boss 2"],pieces["third bearing"]).clean()
    assert len(floor_patch.Solids())==1
    asm.add(floor_patch,name="Housing floor cutaway with integral supports",color=cq.Color(.64,.72,.67))
    asm.add(pieces["blank PCB"],name="Combined bare board envelope",color=cq.Color(.15,.43,.33))
    for i in (1,2):
        asm.add(pieces[f"head envelope {i}"],name=f"Screw head envelope {i}",color=cq.Color(.72,.74,.74))
    asm.export(str(HERE/"case-mount-concept.step"))
    report=dict(source_step_sha256=sha.hexdigest(),old_board_members_removed=sorted(OLD),static_fit=checks,display_rigid_18mm_lift=display_checks,
                original_foot_locations_external_intersections_mm3=rejected,
                support_centres_xy_mm=SCREWS+[REST],bare_board_area_mm2=round(pieces["blank PCB"].Volume()/THICKNESS,2),
                blank_bounds_mm=[13,37.5,-14,19,SEAT,SEAT+THICKNESS],
                scope="Static nominal board and fastener-head envelopes only. Legacy wire collisions retained. Component placement, copper, insertion, tool access, connector and flexible lead motion, print strength and bench behavior remain open.")
    (HERE/"fit.json").write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dressed_step",type=Path)
    run(parser.parse_args().dressed_step)
