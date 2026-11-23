"""Inspect transverse slices of the marked rim and native support at model-island starts."""
from collections import defaultdict
from pathlib import Path
import json
import sys
import numpy as np
from shapely.geometry import box, LineString, GeometryCollection
from shapely.ops import unary_union
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "TW-A-0001-R0014/Printing"))
from rail_paths import footprints

def rim(folder):
    mat = np.array(json.loads((HERE/"rotor-geometry.json").read_bytes())["installed_to_print"])
    traces = defaultdict(list)
    paths = footprints(folder/"plate_2.gcode",box(75,129,92,135),7.6,13.,traces,"387")
    rows = []
    for z,groups in sorted(paths.items()):
        x_inst = (z - mat[2,2]*14.8 - mat[2,3])/mat[2,0]
        if not (49.1 <= x_inst <= 57.5) or "model" not in groups:
            continue
        x = (mat @ [x_inst,0,14.8,1])[0] + 84.999413
        witness = LineString([(x,143-12.95),(x,143-10.7)])
        points = unary_union([p.intersection(witness) for p in traces[z]])
        n = sum(1 for q in getattr(points,"geoms",[points]) if q.geom_type == "Point" and not q.is_empty)
        rows.append({"z":z,"installed_x":round(x_inst,3),"model_width_mm":round(groups["model"].intersection(witness).length,3),"crossings":n})
    return rows

def run(root):
    results={s:rim(root/s) for s in ("before","all","reopen")}
    assert results["all"]==results["reopen"] and len(results["all"])>=10
    paths=json.loads((HERE/"part-paths.json").read_bytes())
    hits=[]
    for row in paths:
        for island in row["model_component_backing"]["fully_unbacked_components"]:
            z=island["z"]
            bbox=box(*island["bbox"])
            item=next(r for r in json.loads((HERE/"deposition.json").read_bytes())["objects"] if r["name"]==row["name"])
            patches=footprints(root/"all"/f"plate_{row['plate']}.gcode",bbox,z-.85,z,object_id=item["object_id"])
            model=patches[z]["model"]
            support=[(level,g["support"].intersection(model).area) for level,g in patches.items() if level<z and "support" in g]
            hits.append(dict(name=row["name"],z=z,model_start_area_mm2=island["area_mm2"],bbox=island["bbox"],
                             support_intersection_by_z={level:round(a,4) for level,a in support if a>1e-6}))
    old = {row["z"]:row for row in results["before"]}
    new = {row["z"]:row for row in results["all"]}
    assert old[7.6]["model_width_mm"] < .1 and new[7.6]["model_width_mm"] > 1.5
    assert all(new[z]["model_width_mm"] >= 1.80 and old[z]["model_width_mm"] < .55 for z in new if z >= 8.0)
    from path_evidence import inspect
    rod,_=inspect(root/"oldrod"/"plate_3.gcode",track_layers=True,focus={"396"})
    results["original_rod_starts"]=rod["396"]["model_component_backing"]["fully_unbacked_components"]
    assert results["original_rod_starts"] and not next(r for r in paths if r["name"]=="rod-grip_1")["model_component_backing"]["fully_unbacked_components"]
    results["island_support"]=hits
    (HERE/"local-paths.json").write_text(json.dumps(results,indent=2)+"\n")

if __name__=="__main__":
    run(Path(sys.argv[1]))
