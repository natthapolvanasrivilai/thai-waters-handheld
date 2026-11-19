"""Cache Rev G dressed geometry, evaluate the selected candidate CAD in assembly coordinates."""
import argparse
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import shutil
import sys
import cadquery as cq

HERE = Path(__file__).resolve().parent
REV = HERE.parent
MECH = REV.parent
sys.path.insert(0,str(MECH/"rev-G"))
import geometry as g
from qualification import run as battery_qualification

ARCHIVE_HASH = "1f1b15b092394d9874e3d6e5d8921800b4bc8913c28eb5f97512674cfa5200e2"
IDS = {"housing-battery-bay":"Housing", "bezel":"Bezel", "rotor":"Rotor", "folding-stem":"Stem",
       "grip":"Grip", "collar":"Collar", "power-cap":"Key cap", "rod-grip":"Removable rod grip",
       "grip-screw-keeper":"Grip screw keeper","receiver-nut-keeper":"Receiver nut keeper",
       "key-board-retainer-west":"Retainer","battery-wire-bridge":"bridge"}
EPS = .002


def baseline(archive, cache):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_HASH:
        raise ValueError("Unexpected Rev G archive")
    cache.mkdir(exist_ok=True,parents=True)
    if not (cache / "complete.json").exists():
        with gzip.open(archive, "rb") as src,(cache/"assembly.step").open("wb") as out:
            shutil.copyfileobj(src,out)
        asm = cq.Assembly.load(str(cache/"assembly.step"))
        for n in asm.children:
            n.obj.moved(n.loc).exportBrep(str(cache / (n.name+".brep")))
        # Non-drawing variants are excluded from the assembly export. Reconstruct these
        # from source using the released pack datum and supplier STEP.
        extras = {"Cell":g.box(g.CX-17,g.CY-31,g.Z,34,62,5),
                  "cellAlt":cq.importers.importStep(str(MECH/"rev-F/review/inputs/Adafruit-258.step")).val().translate((g.CX,g.CY,g.Z))}
        for variant,prefix in (("alt","altTail"),("catalog","pack")):
            for i in range(2):
                extras[prefix+str(i)]=g.factory_lead(variant,i)[0]
        for name,shape in extras.items():
            shape.exportBrep(str(cache/(name+".brep")))
        (cache/"complete.json").write_text(json.dumps({"archive":ARCHIVE_HASH}))
    return {p.stem:cq.Shape.importBrep(str(p)) for p in cache.glob("*.brep")}


def bounds(s):
    b=s.BoundingBox()
    return (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)


def possible(a,b):
    return all(a[i] < b[i+1]-1e-6 and b[i] < a[i+1]-1e-6 for i in (0,2,4))


def volume(s):
    return max(0.,s.Volume()) if s.Solids() else 0.


def overlap(a,b):
    if not possible(bounds(a),bounds(b)):
        return 0.
    return volume(a.intersect(b))


def round_volume(v):
    return round(v,5)


def changed_material(old,new):
    added={}
    deltas={}
    for stem,k in IDS.items():
        a,b=old[k],new[k]
        add=b.cut(a)
        gain=volume(add)
        # Since V(new)-V(old)=gain-loss, this avoids an unnecessary reverse Boolean.
        loss=max(0.,gain-b.Volume()+a.Volume())
        deltas[stem]={"added_mm3":round_volume(gain),"removed_mm3":round_volume(loss)}
        if gain>EPS:
            added[k]=add
    return added,deltas


def added_checks(add,new):
    # For a collision to be introduced at least one part must gain material.
    # Compare each disconnected gain to all other components in its assembly frame.
    bins={k:[(s,bounds(s)) for s in v.Solids()] for k,v in new.items()}
    rows=[]
    for k,delta in add.items():
        dbins=[(s,bounds(s)) for s in delta.Solids()]
        for other,otherbins in bins.items():
            if k==other:
                continue
            v=sum(volume(a.intersect(b)) for a,ab in dbins for b,bb in otherbins if possible(ab,bb))
            if v>EPS:
                rows.append({"gained_by":k,"other":other,"new_contact_mm3":round_volume(v)})
    return rows


def mechanism(old,new,add):
    # Restrict repeated candidate tests to newly occupied volumes on either member.
    # The reference already passed the same stroke and nominal retention checks.
    results={}
    def motion(label,mobile,fixed,poses,move):
        peak=0.; worst=None; count=0
        for pose in poses:
            for a,b in itertools.product(mobile,fixed):
                if a==b:
                    continue
                count+=1
                q=0.
                if a in add:
                    q=max(q,overlap(move(add[a],pose),new[b]))
                if b in add:
                    q=max(q,overlap(move(new[a],pose),add[b]))
                if q>peak:
                    peak,worst=q,(a,b,pose)
        print(label,round_volume(peak),flush=True)
        results[label]=dict(pair_poses=count,peak_new_material_intersection_mm3=round_volume(peak),worst=worst)
    motion("key_0_to_0.70mm",["Key cap"],["Housing","Retainer"],[i*.05 for i in range(15)],lambda s,d:s.translate((0,-d,0)))
    motion("grip_screw_retraction_0_to_5.30mm",["Grip lock screw"],["Housing","Removable rod grip","Grip screw keeper","Receiver nut keeper"],[i*5.3/20 for i in range(21)],lambda s,d:s.translate((0,0,-d)))
    for k in ["Removable rod grip","Grip screw keeper","Grip lock screw"]:
        motion("slide_0_to_43mm_"+k,[k],["Housing","Receiver nut","Receiver nut keeper"],range(44),lambda s,d:s.translate((0,-d,-5.3 if k=="Grip lock screw" else 0)))
    def fold(s,d):
        return s.rotate((53.6,7.8,14.8),(53.6,7.8,15.8),d) if d else s
    def rotate(s,d):
        return s.rotate((58.5,0,14.8),(59.5,0,14.8),d) if d else s
    move_fold=["Stem","Grip","reel1","H5"]
    motion("crank_fold_0_to_90deg",move_fold,["Rotor","Housing","Bezel","Collar","reel0","H3-1","H3-2"],range(0,91,5),fold)
    for d in (0,90):
        for k in [*move_fold,"Rotor","Collar","reel0","reel2","H3-1","H3-2"]:
            motion(f"rotate_0_to_350deg_at_fold_{d}_"+k,[k],["Housing","Bezel","Removable rod grip",*[s for s in new if s.startswith("A2-")]],range(0,360,10),lambda s,a:rotate(fold(s,d) if k in move_fold else s,a))
    # A material subtraction can defeat a functional stop even if the travel stays clear.
    grip=new["Removable rod grip"]; shell=new["Housing"]; screw=new["Grip lock screw"]
    retention={"locked_backslide_1mm":overlap(screw.translate((0,-1,0)),shell),
               "rear_lift_1.2mm":overlap(grip.translate((0,0,-1.2)),shell),
               "blind_stop_overshoot_0.5mm":overlap(grip.translate((0,.5,0)),shell),
               "screw_keeper_over_retract_0.75mm":overlap(screw.translate((0,0,-6.05)),new["Grip screw keeper"])}
    return results,{k:round_volume(v) for k,v in retention.items()}



def distances(old,new):
    pairs=[("A1-touch","Bezel"),("A2-sockets","Housing"),("A2-chip","reel2"),
           ("Speaker","Housing"),("A2-pcb","Rotor"),("Grip","Stem"),("Rotor","Housing"),
           ("Rotor","Bezel"),("Grip lock screw","Removable rod grip"),("Receiver nut","Housing")]
    for key in ["pack0","pack1","drawingTail0","drawingTail1","altTail0","altTail1",
                "batt0","batt1","shrink0","shrink1","ph","packplug","keyPCB"]:
        if key in new:
            pairs.extend([(key,"bridge"),(key,"Housing")])
    records={}
    for a,b in pairs:
        records[a+" / "+b]={"R0007_mm":round(old[a].distance(old[b]),4),
                             "R0008_mm":round(new[a].distance(new[b]),4)}
    return records


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--cache",type=Path,required=True)
    p.add_argument("--prepare-only",action="store_true")
    args=p.parse_args()
    old=baseline(args.archive,args.cache)
    if args.prepare_only:
        print("Reference solids",len(old),sorted(old),flush=True)
        return
    new=old.copy()
    for stem,name in IDS.items():
        new[name]=cq.Shape.importBrep(str(REV/"CAD"/(stem+".brep")))
    def save(name,data):
        (HERE/name).write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    add,delta=changed_material(old,new)
    save("cad-changes.json",delta)
    print("CAD changes",delta,flush=True)
    hits=added_checks(add,new)
    save("new-contact.json",hits)
    save("seated-gaps.json",distances(old,new))
    print("Static comparison complete",flush=True)
    q=battery_qualification(new)
    save("battery-and-key.json",q)
    print("Battery tests complete",flush=True)
    movements,retention=mechanism(old,new,add)
    save("mechanism.json",dict(movements=movements,retention=retention))
    print("Motion tests complete",flush=True)
    assert not hits, hits
    assert all(r["peak_new_material_intersection_mm3"]<=EPS for r in movements.values())
    assert min(retention.values())>.02
    assert all(v<=EPS for row in q["insertion_sweep_overlap_mm3"].values() for v in row.values())
    assert all(max(r["shell_mm3"],r["bridge_mm3"])<=EPS for r in q["rigid_placement_corners"])
    assert all(max(r["housing_mm3"],r["keeper_mm3"])<=EPS for r in q["key_stroke"])
    assert min(q["wall_section_mm"].values())>=1.45
    assert all(v<=EPS for v in q["clearance_box_intersections_mm3"].values())


if __name__=="__main__":
    main()
