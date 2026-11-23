"""Bound the R0013 service motion relative to both new A3 rails throughout each interval."""
import math
import sys

import numpy as np

from build_housing import CENTERS, HERE, OLD, ROOT, TOP, cq, digest, rail, read, save
sys.path.insert(0, str(OLD))
from intervals import pole_motion, ribbon
from stroke import new_leads
from service_check import model, tri, meshgap

def run():
    wires = new_leads()
    directory = ROOT / "hardware/electronics/harness-r0006"
    paths = read(directory/"routing.json")
    prior = read(OLD/"QA/interval-clearance.json")
    assert digest(directory/"loop-forms.json") == prior["form_sha256"]
    assert digest(OLD/"overlay.json") == prior["overlay_sha256"]
    count = prior["intervals"]
    obstacles = [model(*tri(rail(x))) for x in CENTERS]
    results = {net:(float("inf"),) for net in wires.NET_PIN}
    parameters = wires.bernstein(7,np.linspace(0,1,97))
    for i in range(count):
        start, end = wires.STROKE*i/count, wires.STROKE*(i+1)/count
        for net in wires.NET_PIN:
            tx, _, z = paths[net]["tap_center_mm"]
            poles, movement = pole_motion(wires,net,tx,z,start,end)
            degree = len(poles)-1
            chord = degree*(degree-1)*np.linalg.norm(np.diff(poles,n=2,axis=0),axis=1).max()/(8*96**2)
            pts = parameters @ poles
            barrel = [pts[0,0],-5.35+(start+end)/2,10.36]
            path = ribbon(np.concatenate([[barrel],pts]))
            for cx, obstacle in zip(CENTERS,obstacles):
                gap = meshgap(path,obstacle)
                conservative = gap - (wires.JACKET_OD/2+chord+movement+.00001)
                results[net] = min(results[net],(conservative,start,end,cx))
    records = {net:dict(lower_bound_mm=math.floor(t[0]*1e5)/1e5,travel_interval_mm=list(t[1:3]),
                        rail_center_x_mm=t[3]) for net,t in results.items()}
    assert min(r["lower_bound_mm"] for r in records.values()) > 0
    # The rigid plug, contacts and crimp ends translate along Y. Bound the
    # rocker separately throughout its rotation about X using its swept radius.
    old_nodes = read(OLD/"installed-step.json")["components"]
    plug_geometry = ROOT/"hardware/electronics/harness-r0005/placed/A3-J1-plug.brep"
    plug = cq.Shape.importBrep(str(plug_geometry))
    _, latch = wires.split_latch(plug)
    lb = latch.BoundingBox()
    radius = max(math.hypot(y-wires.PIVOT[1],z-wires.PIVOT[2])
                 for y in (lb.ymin,lb.ymax) for z in (lb.zmin,lb.zmax))
    latch_min_z = min(wires.actuate(latch,i/8).BoundingBox().zmin for i in range(9))
    latch_clear = latch_min_z-radius*abs(math.radians(wires.RELEASE_DEG))/16-TOP
    moving = read(OLD/"clearance.json")["rigid_members"][1:]
    other_min_z = min([plug.BoundingBox().zmin]+[old_nodes[k]["bounds_mm"][4] for k in moving])-.0001
    overall = min(other_min_z-TOP,latch_clear)
    assert overall > 0
    # Previous continuous clearances apply to the same electrodes, pack options
    # and seated anchor poses because the new housing+empty grooves occupies a
    # strict subset of the old housing+foam. assemble.py proves this with solids.
    service = read(OLD/"clearance.json")
    save(HERE/"QA/rail-service-motion.json",dict(
        source_step_sha256=read(OLD/"installed-step.json")["step_sha256"],local_rail_brep_sha256=digest(HERE/"CAD/housing-battery-bay.brep"),
        source_form_sha256=prior["form_sha256"],source_overlay_sha256=prior["overlay_sha256"],
        interval_count=count,withdrawal_mm=wires.STROKE,latch_actuation_degrees=wires.RELEASE_DEG,
        wire_jacket_diameter_mm=wires.JACKET_OD,flex_rail_bound_by_net=records,
        rocker_to_rail_vertical_bound_mm=round(latch_clear-.00001,5),
        all_rigid_members_to_rail_vertical_bound_mm=round(overall-.00001,5),
        translating_members=["A3-J1-plug body",*moving],pressed_then_withdrawn=True,
        inherited_installed_rigid_lower_bound_mm=service["continuous_rigid_to_seated_mesh_lower_mm"],
        inherited_rigid_vs_W1_lower_bound_mm=service["continuous_rigid_W1_lower_bound_mm"],
        inherited_W4_to_seated_lower_bound_mm=prior["flex_to_seated_mesh"]["lower_bound_mm"],
        inherited_W4_pair_lower_bound_mm=prior["flex_to_flex"]["lower_bound_mm"],
        scope="Nominal geometry. Rails modeled with empty channels; adhesive must remain confined within the groove volume and below the bearing plane. Tube radius, chord error and pole motion are subtracted from the 3D gap to the rail at each interval midpoint. Fixed and moving members retain the R0013 datums. Socket/terminal internals, physical flex and grip access remain subject to the prior supplier-model limitations."))
    print(records, flush=True)


if __name__ == "__main__":
    run()
