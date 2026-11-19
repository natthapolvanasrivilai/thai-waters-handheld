"""Certify the empty-case straight-line SP1 installation and check its routed leads."""
import argparse
import itertools
import json
import math
from pathlib import Path
import sys
import cadquery as cq

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import speaker

def xyz(a,b,t):
    return tuple(x+(y-x)*t for x,y in zip(a,b))

def sweep(start,end,part,case):
    # For a rigid translation, clearance can fall by at most the travel
    # distance. Accept each interval only where midpoint gap exceeds its
    # maximum distance to either end. This bounds every intermediate pose.
    length=math.dist(start,end)
    todo=[(0.,1.)];certified=[];checks=0
    while todo:
        lo,hi=todo.pop()
        mid=(lo+hi)/2;half=(hi-lo)*length/2
        pose=part.translate(xyz(start,end,mid))
        d=pose.distance(case);checks+=1
        if d>half+1e-5:
            certified.append(d-half)
        elif half<.002:
            raise ValueError((start,end,mid,d,"uncertified segment"))
        else:todo.extend(((lo,mid),(mid,hi)))
    return dict(start_offset_mm=start,end_offset_mm=end,translation_mm=length,midpoint_queries=checks,
                certified_minimum_gap_mm=round(min(certified),6))

def main(reference):
    case=cq.Shape.importBrep(str(HERE/"CAD/housing-battery-bay.brep"))
    pieces=speaker.speaker_parts()
    sp=cq.Compound.makeCompound(list(pieces.values()))
    hard=HERE.parents[1]
    fitted={}
    for folder in (hard/"electronics/usb-status-r0003/placed",hard/"electronics/haptic-r0009/placed",hard/"components/standard-fasteners/placed"):
        for f in folder.glob("*.brep"):fitted[f.stem]=cq.Shape.importBrep(str(f))
    for k in ("cellDrawing","batt0","batt1","shrink0","shrink1","drawingTail0","drawingTail1","w30","w31","packplug","ph","A1-J9","A1-usb","j9plug","A1-boot","A1-carrier","A1-J7","A1-k3"):
        fitted[k]=cq.Shape.importBrep(str(reference/(k+".brep")))
    for folder in (hard/"electronics/harness-r0003/placed",hard/"components/te-rnf-100"):
        for f in folder.glob("*.brep"):fitted[f.stem]=cq.Shape.importBrep(str(f))
    # Source A1 population contains hundreds of solids. Test every component inside
    # the west speaker/lead region; use its own CAD bounding box as a broad phase.
    for n,part in enumerate(cq.Shape.importBrep(str(reference/"A1-population.brep")).Solids()):
        bb=part.BoundingBox()
        if bb.xmin<1. and bb.xmax>-52 and bb.ymin<17 and bb.ymax>-23 and bb.zmin<20:
            fitted["A1-population-"+str(n)]=part
    fitted["bridge"]=cq.Shape.importBrep(str(HERE/"CAD/battery-wire-bridge.brep"))
    fitted["Housing"]=case
    sources={"SP1":sp,**{f"spk{i}":speaker.route(i)[0] for i in (0,1)}}
    report={"nominal_seated_gaps_mm":{},"intentional_connector_contact":{},"route_lengths_mm":{},"tolerance_corners_mm":[]}
    for source,s in sources.items():
        data=report["nominal_seated_gaps_mm"][source]={}
        for k,other in fitted.items():
            d=s.distance(other);data[k]=round(d,5)
            if d<.0001:
                v=s.intersect(other).Volume()
                if k in ("j9plug","J9-C1","J9-C2") and source.startswith("spk"):
                    report["intentional_connector_contact"][source]=round(v,5)
                elif v>.0008:raise ValueError((source,k,v))
    for i in (0,1):
        report["route_lengths_mm"]["spk"+str(i)]=speaker.route(i)[1]["centerline_length_mm"]
    report["wire_to_wire_gap_mm"]=round(sources["spk0"].distance(sources["spk1"]),6)
    assert report["wire_to_wire_gap_mm"]>.25
    for p in itertools.product((-.15,.15),repeat=3):
        gap=sp.translate(p).distance(case)
        assert gap>.01,(p,gap)
        report["tolerance_corners_mm"].append(dict(offset_mm=p,gap_mm=round(gap,5)))
    points=[(24,0,35),(24,0,.65),(0,0,.65),(0,0,0)]
    report["continuous_empty_housing_install"]= [sweep(a,b,sp,case) for a,b in zip(points,points[1:])]
    report["assembly_order"]="Fit SP1 and acoustic gasket before cell, bridge, controller and harness. Top entry 24 mm east; slide west with 0.65 mm lift, then lower to gasket."
    (HERE/"QA/speaker-fit.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print("Certified SP1 fit",report["continuous_empty_housing_install"],flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("reference",type=Path);main(p.parse_args().reference)
