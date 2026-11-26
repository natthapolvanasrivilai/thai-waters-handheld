"""Measure the six lands in native print paths and check the balance of the loose gauges."""
from pathlib import Path
import json
import sys

import numpy as np
import trimesh
from shapely.geometry import box, Point, Polygon
from shapely import union_all

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.with_name("TW-A-0001-R0014")/"Printing"))
from rail_paths import footprints
from make_project import digest

def audit(folder, seats):
    plate=json.loads((folder/"result.json").read_bytes())["sliced_plates"][0]
    assert len(plate["objects"])==1 and not plate["warning_message"]
    layers=footprints(folder/"plate_1.gcode",box(79,91,176,159),7,11.2,object_id="1701")
    assert all("support" not in role for role in layers.values())
    results=[]
    # Build centre (128,128), physical nozzle shift (0,-2), mirrored installed Y.
    for seat in seats:
        x,y=seat["installed_center_xy_mm"]
        x,y=x+128,126-y
        area=box(x-1.25,y-1.25,x+1.25,y+1.25)
        coverage={z:roles.get("model",Polygon()).intersection(area).area/area.area for z,roles in layers.items()}
        top=max(z for z,v in coverage.items() if v>.7)
        nominal=28.5-seat["bearing_z_mm"]
        assert abs(top-nominal)<=.101
        # Continuous deposit over the seat perimeter, including the junction with A1.
        perimeter=area.difference(area.buffer(-.22))
        zs=[round(z/5,2) for z in range(38,round(top*5)+1)]
        backing=min(layers[z]["model"].intersection(perimeter).area/perimeter.area for z in zs)
        assert backing>.80 and coverage[top]>.94,(seat,backing,coverage[top])
        results.append(dict(component=seat["board"],centre_xy_gcode_mm=[x,y],bearing_layer_mm=top,
                            cad_bearing_mm=round(nominal,3),top_coverage=round(coverage[top],4),
                            minimum_perimeter_coverage=round(backing,4)))
    return dict(seats=results,warnings=plate["warning_message"],gcode_sha256=digest(folder/"plate_1.gcode"),
                estimated_seconds=round(plate["total_predication"]),estimated_g=round(plate["filaments"][0]["total_used_g"],2))

if __name__=="__main__":
    seats=json.loads((HERE/"fit.json").read_bytes())["seats"]
    results=[audit(Path(p),seats) for p in sys.argv[1:]]
    assert len(results)==2 and results[0]["seats"]==results[1]["seats"]
    base=HERE.with_name("pcb-fit-r0013")
    ledger=json.loads((base/"geometry.json").read_bytes())["parts"]
    balance={}
    for name in ("A4-integration","A5-power"):
        mesh=trimesh.load_mesh(base/ledger[name]["file"])
        pose=np.eye(4)
        pose[:3]=ledger[name]["print_to_installed_3x4"]
        mesh.apply_transform(pose)
        points=[r["installed_center_xy_mm"] for r in seats if r["board"]==name]
        region=union_all([box(x-1.5,y-1.5,x+1.5,y+1.5) for x,y in points]).convex_hull
        balance[name]=dict(uniform_solid_centroid_xy_mm=mesh.center_mass[:2].round(4).tolist(),
                           distance_outside_support_polygon_mm=round(region.distance(Point(*mesh.center_mass[:2])),4))
    (HERE/"native-check.json").write_text(json.dumps(dict(slices=results,nominal_gauge_balance=balance),indent=2)+"\n")
