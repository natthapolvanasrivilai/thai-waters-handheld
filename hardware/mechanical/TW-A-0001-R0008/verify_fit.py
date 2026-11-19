"""Verify R0008 installed print geometry against the drawing-max Rev G reference assembly."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import cadquery as cq
import numpy as np

from build import HERE, PARTS, V, box, cyl, roof

sys.path.insert(0,str(HERE.parent/"rev-G"))
import geometry as G
from qualification import run as run_battery

EPS=.002


def overlap(a,b):
    return max(0.,a.intersect(b).Volume())


def save(name, data):
    (HERE/name).write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")


def bounds(s):
    b=s.BoundingBox()
    return (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)


def near(a,b):
    return all(a[i]<b[i+1]-.00001 and b[i]<a[i+1]-.00001 for i in (0,2,4))


def parts_from_step(path, cache):
    cache.mkdir(parents=True,exist_ok=True)
    reference_hash="965a6b4f455eebc89e03b8f740c3abd0208579df28b36185e6c0600b2e0a6b93"
    if hashlib.sha256(path.read_bytes()).hexdigest()!=reference_hash:
        raise ValueError("Use the decompressed drawing-maximum Rev G release STEP")
    stamp=cache/"source-sha256.txt"
    if not stamp.exists() or stamp.read_text().strip()!=reference_hash or len(list(cache.glob("*.brep")))!=79:
        for n in cq.Assembly.load(str(path)).children:
            n.obj.moved(n.loc).exportBrep(str(cache/(n.name+".brep")))
        stamp.write_text(reference_hash+"\n")
    return {p.stem:cq.Shape.importBrep(str(p)) for p in cache.glob("*.brep")}


def check(step,cache):
    previous=parts_from_step(step,cache)
    allparts=previous.copy()
    for stem,(key,*_) in PARTS.items():
        if key:
            allparts[key]=cq.Shape.importBrep(str(HERE/"CAD"/(stem+".brep")))
    # Catalog and supplier alternative have independent factory-lead swept solids.
    allparts["Cell"]=box(G.CX-17.,G.CY-31.,G.Z,34,62,5)
    allparts["cellAlt"]=cq.importers.importStep(str(HERE.parent/"rev-F/review/inputs/Adafruit-258.step")).val().translate((G.CX,G.CY,G.Z))
    for variant,prefix in [("catalog","pack"),("alt","altTail")]:
        for i in range(2):
            allparts[prefix+str(i)],_=G.factory_lead(variant,i)
    result=run_battery(allparts)
    assert all(v<EPS for row in result["insertion_sweep_overlap_mm3"].values() for v in row.values())
    assert all(v<EPS for v in result["clearance_box_intersections_mm3"].values())
    assert all(max(row["housing_mm3"],row["keeper_mm3"])<EPS for row in result["key_stroke"])
    assert all(max(row["shell_mm3"],row["bridge_mm3"])<EPS for row in result["rigid_placement_corners"])
    assert min(result["wall_section_mm"].values())>=1.45
    print("battery, key and lead verification passed",flush=True)

    # Difference-based proof: an intersection absent from the baseline can only
    # occur in newly added material of at least one of the changed parts.
    deltas={}
    fixed_bounds={key:bounds(s) for key,s in allparts.items()}
    for name,(key,update,*_) in PARTS.items():
        if not key or not update:
            continue
        new,old=allparts[key],previous[key]
        extra=new.cut(old)
        delta=dict(added_mm3=round(extra.Volume(),6),removed_mm3=round(old.cut(new).Volume(),6),
                   compared_parts=len(allparts)-1,overlap_in_added_material_mm3={})
        # Work on connected difference pieces, preserving analytical surfaces.
        for block in extra.Solids():
            bb=bounds(block)
            for k,s in allparts.items():
                if k==key or not near(bb,fixed_bounds[k]):
                    continue
                for item in s.Solids():
                    if near(bb,bounds(item)):
                        volume=overlap(block,item)
                        if volume>.000001:
                            d=delta["overlap_in_added_material_mm3"]
                            d[k]=round(d.get(k,0)+volume,6)
        assert not any(v>EPS for v in delta["overlap_in_added_material_mm3"].values()),(key,delta)
        deltas[key]=delta
    result["installed_material_changes"]=deltas
    print("new material clearance passed",flush=True)
    case,rod,keeper,nutcap,screw,nut=[allparts[k] for k in ("Housing","Removable rod grip","Grip screw keeper","Receiver nut keeper","Grip lock screw","Receiver nut")]
    static=cq.Compound.makeCompound([case,nut,nutcap])
    unlocked=screw.translate((0,0,-5.30))
    moving=cq.Compound.makeCompound([rod,keeper,unlocked])
    slide=max(overlap(moving.translate((0,dy,0)),static) for dy in range(-43,1))
    unlock=max(overlap(screw.translate((0,0,-dz)),target) for dz in np.linspace(0,5.30,21) for target in [case,rod,keeper,nutcap])
    captures={n:round(overlap(a,b),5) for n,a,b in [
        ("locked after 1mm backslide",screw.translate((0,-1,0)),case),
        ("rails after 1.2mm lift",rod.translate((0,0,-1.2)),case),
        ("mechanical stop after 0.5mm overtravel",rod.translate((0,.5,0)),case),
        ("keeper after extra 0.75mm withdrawal",unlocked.translate((0,0,-.75)),keeper)]}
    assert max(slide,unlock)<EPS and min(captures.values())>.02
    result["rod_grip"]={"slide_samples":44,"slide_stroke_mm":43,"slide_peak_overlap_mm3":round(slide,6),
                        "unlock_samples":21,"unlock_stroke_mm":5.30,"unlock_peak_overlap_mm3":round(unlock,6),"capture_interference_mm3":captures}
    print("rod motion passed",flush=True)
    # Complete 360-degree rotational envelope is tighter than the folded outline
    # at every axial station. The 90-degree fold uses sampled positions for
    # internal moving-to-moving clearances, plus the preserved baseline sweep.
    env=cyl(4.5501,5.4002,(43.5999,0,14.8),(1,0,0)).fuse(cyl(13.0501,8.5002,(48.9999,0,14.8),(1,0,0)))
    rotor=allparts["Rotor"]; stem=allparts["Stem"]; sleeve=allparts["Grip"]
    excess=max(0,rotor.cut(env).Volume())
    rotor_fixed={k:round(overlap(env,allparts[k]),6) for k in ("Housing","Bezel","A1-touch","A2-pcb","A2-chip")}
    assert excess<EPS and max(rotor_fixed.values())<EPS
    foldmax=0
    for angle in np.linspace(0,90,19):
        for item in [stem,sleeve]:
            folded=item.rotate((53.6,7.8,14.8),(53.6,7.8,15.8),float(angle))
            foldmax=max(foldmax,overlap(folded,rotor),overlap(folded,case),overlap(folded,allparts["Bezel"]))
    assert foldmax<EPS
    result["reel"]={"rotor_outside_continuous_axial_envelope_mm3":round(excess,6),"360_degree_envelope_overlap_mm3":rotor_fixed,
                    "fold_0_to_90_degree_samples":19,"fold_peak_overlap_mm3":round(foldmax,6),
                    "journal_radial_clearance_mm":.30,"collar_radial_clearance_mm":.15,"sleeve_radial_clearance_mm":.24}
    # The active touch aperture through the cover is 76.8 by 52.2 with R1.6 corners.
    touch=G.round_box(0,0,28.76,76.798,52.198,5,1.60)
    touch_hit=overlap(touch,allparts["Bezel"])
    assert touch_hit<EPS
    result["active_touch_aperture_overlap_mm3"]=round(touch_hit,6)
    result["nominal_radial_gaps_mm"]={"power cap in outer guide":.25,"power flange in inside counterbore":.30,
         "M3 shank in rod through-bore":.28,"M3 cap head in sliding chamber":.37,"keeper in rod counterbore":.12}
    # Test both long connector block withdrawal and installed clearance after shell edits.
    plug=allparts["packplug"].BoundingBox()
    corridor=box(plug.xmin-4,plug.ymin,plug.zmin,plug.xlen+4,plug.ylen,plug.zlen)
    result["connector_withdrawal_4mm_mm3"]={k:round(overlap(corridor,allparts[k]),6) for k in ("Housing","cellDrawing","bridge","drvBoard","Receiver nut keeper","batt0","batt1")}
    assert max(result["connector_withdrawal_4mm_mm3"].values())<EPS
    save("fit-verification.json",result)
    print("rotor, touch and connector passed",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--reference-step",type=Path,required=True)
    parser.add_argument("--cache",type=Path,required=True,help="dedicated, empty or extracted Rev G assembly cache")
    args=parser.parse_args()
    check(args.reference_step,args.cache)
