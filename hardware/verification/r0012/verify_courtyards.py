"""Measure the A3 housing-to-component distances for the unresolved 2D courtyard findings."""
import hashlib
import json
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
PARTS = HERE.parents[1] / "electronics/harness-r0005/placed"
header_file = PARTS / "A3-J1-header.brep"
parts_file = PARTS / "drvParts.brep"
header = cq.Shape.importBrep(str(header_file))
components = cq.Shape.importBrep(str(parts_file)).Solids()
assert len(header.Solids()) == 6 and len(components) == 14
body = max(header.Solids(), key=lambda solid: solid.Volume())
families = {"C1": [], "U1": [], "C2": []}
for solid in components:
    x = solid.Center().x
    # Capacitors are the only solids at the two outer populated positions.
    families["C1" if x < 18.2 else "C2" if x > 24 else "U1"].append(solid)
assert [len(families[k]) for k in ("C1","C2","U1")] == [1,1,12]
results = {}
for name,solids in families.items():
    component = cq.Compound.makeCompound(solids)
    results[name] = {"body_gap_mm":round(body.distance(component),5),
                     "intersection_mm3":round(body.intersect(component).Volume(),7)}
    assert results[name]["body_gap_mm"]>0 and results[name]["intersection_mm3"]==0
report = {"installed_source_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (header_file,parts_file)},
          "support_nominal_mm":1.4,"housing_to_populated_parts":results,"R1":"DNP",
          "scope":"Rigid nominal installed housing only. Overlap of the J1 courtyard with C1/U1/R1 remains reported."}
# KiCad 10 footprint courtyard bounds, including the courtyard line width.
# Return the supplier housing to PCB axes, where exported STEP uses negative Y.
native = body.translate((37.95,135.15,-4.60)).rotate((0,0,0),(0,0,1),-90)
boxes = {"C1":(125.275,53.775,126.825,56.825),"R1":(125.275,61.400,126.825,64.450),
         "U1":(125.020,57.005,131.380,60.595)}
shadow = {}
for ref,(left,top,right,bottom) in boxes.items():
    prism = cq.Solid.makeBox(right-left, bottom-top, 30, cq.Vector(left,-bottom,-5))
    material = native.intersect(prism).Volume()
    assert material > 0
    shadow[ref] = {"courtyard_xy_mm":[left,top,right,bottom],
                   "housing_inside_vertical_prism_mm3":round(material,5),
                   "minimum_shift_to_clear_positive_x_mm":round(129.445-left,3)}
report["plan_view_relocation_study"] = shadow
print(json.dumps(report,indent=2))
