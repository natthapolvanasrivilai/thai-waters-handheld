"""Inspect model extrusion through each integral support and its blind pilot."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from shapely.geometry import Point
from build import HERE,MOUNTS,REST
sys.path.insert(0,str(HERE.parents[1]/"mechanical/TW-A-0001-R0014/Printing"))
from rail_paths import footprints,DX,DY

def run(folder):
    project=HERE/"Case-board-R0001-X1C-fit.3mf"
    native=json.loads((folder/"result.json").read_bytes())
    assert native["return_code"]==0 and len(native["sliced_plates"])==2
    assert not any(p["warning_message"] for p in native["sliced_plates"])
    report={"project_sha256":hashlib.sha256(project.read_bytes()).hexdigest(),"bosses":[]}
    for i,(x,y) in enumerate([*[(x-87,y-114) for x,y in MOUNTS],REST]):
        centre=Point(x+DX,y+DY)
        witness=centre.buffer(1.75).difference(centre.buffer(1.20))
        region=centre.buffer(2).union(Point(centre.x,centre.y+2.5).buffer(2)).convex_hull if i==1 else centre.buffer(2)
        records=footprints(folder/"plate_1.gcode",region=region,zmin=5.5,zmax=21.1)
        model=sorted((z,layer["model"]) for z,layer in records.items() if "model" in layer)
        heights=[z for z,_ in model]
        from shapely.affinity import translate
        ratios=[s.intersection(translate(witness,yoff=2.5*min(1,max(0,(15.3-z)/5)) if i==1 else 0)).area/witness.area for z,s in model]
        assert len(heights)>70 and max(b-a for a,b in zip(heights,heights[1:]))<.201
        assert min(ratios)>.50 and abs(heights[-1]-20.9)<=.11
        upper=[s for z,s in model if z>17]
        if i<2:assert all(s.intersection(centre.buffer(.45)).area<.0001 for s in upper)
        report["bosses"].append(dict(center=[x,y],model_layers=len(model),height_range_mm=[heights[0],heights[-1]],min_annulus_coverage=round(min(ratios),3),pilot_core_open=i<2))
    for i in (1,2):
        gcode=folder/f"plate_{i}.gcode"
        header=gcode.read_text(encoding="utf8").splitlines()[:11]
        report[f"plate_{i}"]={"gcode_sha256":hashlib.sha256(gcode.read_bytes()).hexdigest(),"header":header[:7]}
    assert report["plate_2"]["header"][3].endswith(": 4")
    (HERE/"toolpaths.json").write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("slice_folder",type=Path)
    run(p.parse_args().slice_folder)
