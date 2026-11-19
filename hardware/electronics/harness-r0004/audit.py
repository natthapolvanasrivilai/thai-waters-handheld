"""Verify the mated A3 branch and service path in a dressed STEP (mm)."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import cadquery as cq
import fcl
import numpy as np

HERE = Path(__file__).resolve().parent
NET = {1: "VCC", 3: "SCL", 4: "SDA", 5: "GND"}
PIN = {net: f"A3-J1-C{i}" for i, net in NET.items()}


def pair(a, b):
    return tuple(sorted((a,b)))


def allowed_contacts():
    rows = [
        ("drvBoard","adhH"),("A3-J1-spacer","drvBoard"),
        ("A3-J1-header","A3-J1-spacer"),("A3-J1-header","A3-mode-strap-Cu"),
        ("A3-mode-strap-Cu","A3-mode-strap"),
    ]
    for k in ("wm0","wm1"):
        rows.extend([(k,"motor"),(k,k+"-Cu")])
    for net,contact in PIN.items():
        lead, trunk, joint, seal = "wh"+net,"w1"+net,"tee-"+net+"-Cu","tee-"+net+"-seal"
        rows.extend([(contact,"A3-J1-header"),(contact,lead+"-Cu"),(contact,lead),
                     (lead,lead+"-Cu"),(joint,seal),(joint,trunk),(seal,trunk),
                     (joint,lead),(seal,lead),(trunk,"termination-W1-"+net)])
    return {pair(*x) for x in rows}


def bounds(shape):
    b = shape.BoundingBox()
    return (np.array([b.xmin,b.ymin,b.zmin]),np.array([b.xmax,b.ymax,b.zmax]))


def box_gap(a,b,offset):
    return np.linalg.norm(np.maximum(0,np.maximum(a[0]+offset-b[1],b[0]-a[1]-offset)))


class Scene:
    def __init__(self, shapes):
        self.shapes=shapes
        self.bounds={n:bounds(s) for n,s in shapes.items()}
        self.meshes={}
        self.query=fcl.DistanceRequest()

    def mesh(self,name):
        if name not in self.meshes:
            v,faces=self.shapes[name].tessellate(.025,.14)
            model=fcl.BVHModel()
            model.beginModel(len(v),len(faces))
            model.addSubModel(np.array([p.toTuple() for p in v]),np.array(faces))
            model.endModel()
            self.meshes[name]=model
        return self.meshes[name]

    def gap(self,a,b,delta=(0.,0.,0.),limit=3.0):
        offset=np.asarray(delta)
        lower=box_gap(self.bounds[a],self.bounds[b],offset)
        if lower>limit:
            return math.inf
        moving=fcl.CollisionObject(self.mesh(a),fcl.Transform(offset))
        fixed=fcl.CollisionObject(self.mesh(b))
        return max(0.,fcl.distance(moving,fixed,self.query,fcl.DistanceResult()))


def smallest(rows):
    d,a,b=min(rows)
    return dict(parts=[a,b],gap_mm=round(d,4))


def verify(shapes):
    manifest=json.loads((HERE/"installed.json").read_text())
    new={row["name"] for row in manifest["add"]}
    assert new<=shapes.keys()
    allowed=allowed_contacts()
    cur=Scene(shapes)
    gaps={}
    for a in sorted(new):
        for b in shapes:
            key=pair(a,b)
            if a!=b and key not in gaps:
                gaps[key]=cur.gap(a,b)
    faults=[key for key,d in gaps.items() if d<.002 and key not in allowed]
    assert not faults,faults
    # The plug and mated contacts move together, using the plastic envelope.
    # Clearance to the parked/flexible loom requires a first article. Retain
    # the other fixed items including the motor, its leads and the case.
    plug="A3-J1-plug"
    fixed={n for n in shapes if not n.startswith(("wh","w1","tee-","termination-W1-","A1-","A2-","A3-J1-C"))}
    fixed-= {plug,"A3-J1-header","J8plug"}
    parked=[]
    installed=[]
    for y in np.arange(0,8.251,.25):
        for b in fixed:
            d=cur.gap(plug,b,(0.,float(y),0.))
            if math.isfinite(d):parked.append((d,b,float(y)))
        for b in [n for n in new if n.startswith("w1")]:
            d=cur.gap(plug,b,(0.,float(y),0.))
            if math.isfinite(d):installed.append((d,b,float(y)))
    closest=min(parked)
    assert closest[0]>.13, closest
    wire_names={"wh"+n for n in PIN}
    def group_gap(A,B):
        return smallest((gaps[pair(a,b)],a,b) for a in A for b in B if a!=b)
    rigid={"A3-J1-header",plug,"A3-J1-spacer","A3-mode-strap","A3-mode-strap-Cu","drvBoard","drvParts"}
    results=dict(
        method="CadQuery STEP geometry tessellated at 0.025 mm / 0.14 rad. FCL surface distance in mm; designed interfaces enumerated in audit.py.",
        checked_changed_parts=len(new),all_assembly_nodes=len(shapes),
        boundary_pairs=len(gaps),unintended_surface_contacts=faults,
        pigtail_to_pigtail=group_gap(wire_names,wire_names),
        pigtail_to_motor_and_motor_leads=group_gap(wire_names,{"motor","wm0","wm1"}),
        strap_to_adhesive_or_shell=group_gap({"A3-mode-strap"},{"Housing","adhH"}),
        a3_to_shell=group_gap(rigid,{"Housing"}),
        rigid_plug_travel=dict(direction="+Y",stroke_mm=8.25,sample_interval_mm=.25,
               parked_w1_minimum_sampled_clearance_mm=round(closest[0],4),
               nearest_fixed_item=closest[1],worst_sample_stroke_mm=closest[2],
               continuous_motion_mesh_lower_bound_mm=round(closest[0]-.125,4),
               first_stroke_intersecting_the_dressed_W1_mm=min((y for d,n,y in installed if d<.002),default=None),
               parked_items="A1/display and its J8 connection, AS5600 assembly, W1 trunks and tees, four mobile W4 branches. Release and support harness before extraction.",
               residual_work="Physical disconnect/reconnect stroke, grip access and wire movement require first-article testing."),
        manufacturer_CAD="61900519521 5-way header",
        drawing_derived="61900511621 housing and 61900113722 formed contact. Cavity clearance, latch engagement and contact force remain unverified.",
        physical_tests="Not performed")
    # Closed solid, unmeshed distances cross-check the most important external interfaces.
    for item in ["pigtail_to_pigtail","pigtail_to_motor_and_motor_leads","strap_to_adhesive_or_shell","a3_to_shell"]:
        a,b=results[item]["parts"]
        results[item]["brep_distance_mm"]=round(shapes[a].distance(shapes[b]),4)
    return results


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("step",type=Path)
    ap.add_argument("--output",type=Path,default=HERE/"clearance.json")
    args=ap.parse_args()
    asm=cq.Assembly.load(str(args.step))
    shapes={node.name:node.obj.moved(node.loc) for node in asm.children}
    data=verify(shapes)
    data.update(step_file=args.step.name,step_sha256=hashlib.sha256(args.step.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(data,indent=2)+"\n")
