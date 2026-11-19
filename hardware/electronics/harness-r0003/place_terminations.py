"""Extend insulated leads to the conductors inside the registered crimp and solder interfaces."""
import json
from pathlib import Path
import cadquery as cq

out = Path(__file__).resolve().parent / "placed"
terminals = json.loads((out / "terminals.json").read_text())
ends = []
def tip(key, start, end, target, diameter):
    a, b = cq.Vector(*start), cq.Vector(*end)
    span = b - a
    shape = cq.Solid.makeCylinder(diameter / 2, span.Length, a, span.normalized())
    shape.exportBrep(str(out / ("termination-" + key + ".brep")))
    ends.append(dict(id=key, start_mm=start, end_mm=end, contact=target, diameter_mm=diameter))

for site, loom, sign in [("J7", "W2", 1), ("J9", "W5", -1)]:
    for i, start in enumerate(terminals["wire_exit_faces_mm"][site]):
        x, y, z = start
        # J9 faces opposite J7. Select the contact by its physical cavity X.
        contact = min((key for key in terminals["items"] if key.startswith(site+"-C")),
                      key=lambda key: abs(sum(terminals["items"][key]["bbox_mm"][:2])/2-x))
        tip(f"{loom}-{i+1}", start, (x,y+sign*1.8,z), contact, .32)
for net, wire in json.loads((out / "w1.json").read_text())["wires"].items():
    tip("W1-"+net, wire["pad_end_and_route_mm"][-1], wire["stripped_tinned_tip_mm"], "W1-P", .25)
(out / "conductor-ends.json").write_text(json.dumps(ends, indent=2)+"\n")
