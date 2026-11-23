"""Use the bench display gauge with integral lands on the current fit-guide steps."""
import hashlib
import json
from pathlib import Path

def apply_fixed_display(scene, steps, root):
    kit=root/"hardware/mechanical/pcb-fit-display-r0002"
    report=json.loads((kit/"fit.json").read_bytes())
    if hashlib.sha256((kit/"display-gauge-with-seats.stl").read_bytes()).hexdigest()!=report["stl_sha256"]:
        raise ValueError("Regenerate the fixed-seat display gauge evidence")
    ids=[]
    for board in ("A4","A5"):
        seats=[s for s in report["seats"] if s["board"].startswith(board)]
        assert len(seats)==3
        for i,seat in enumerate(seats,1):
            key=f"{board}s{i}"
            ids.append(key)
            x,y=seat["installed_center_xy_mm"]
            z=seat["bearing_z_mm"]
            bounds=[[x-1.5,y-1.5,z],[x+1.5,y+1.5,21.0]]
            assert all(abs(v-w)<.0011 for row,other in zip(scene["parts"][key]["bounds"],bounds)
                       for v,w in zip(row,other))
    scene["fixedDisplaySeats"]=ids
    for step in steps:
        if "A1" in step["visible"]:
            step["visible"]+= [k for k in ids if k not in step["visible"]]
        if step["title"]=="Turn A1 glass-face down":
            step["instruction"]="Use the inert display gauge with six printed-in seats. Rest its glass side down. With an original Plate 7 A1 gauge, use the six loose PETG blocks at the same marked positions."
            step["check"]="The four corner mounting holes locate A1 in the enclosure. There are no spacer screw holes at the highlighted A4 or A5 positions."
        if step["title"].startswith("Place the three") and step["active"][0] in ids:
            board=step["active"][0][:2]
            step["title"]=f"Find the three {board} seats"
            step["offset"]=[0,0,0]
            step["moving"]=[]
            size,block=("2.465","2.00") if board=="A4" else ("3.160","2.70")
            step["instruction"]=f"These three 3 × 3 mm lands are part of the printed display gauge. Their nominal height is {size} mm. The original Plate 7 kit uses three separate PETG blocks here."
            step["facing"]=f"The real {board} design uses three {block} mm insulating blocks bonded on both faces. The block material and adhesive still require selection and testing."
            step["check"]="Use the printed gauge for an unpowered fit check. Keep the real display free of glue and drill marks."
        if step["title"]=="Rest A4 on the short spacers":
            step["title"]="Seat A4 on the short lands"
            step["instruction"]="Set the integration-board gauge on its three seats. The real A4 connects the remote power button, speaker attenuation resistors and sensor-bus pull-ups to the main controller."
        if step["title"]=="Rest A5 on the tall spacers":
            step["title"]="Support A5 on the tall lands"
            step["instruction"]="Hold the power-board gauge level on its three seats, 2.00 mm from A4. The real A5 detects USB-C source capability and limits the feed to the controller’s power-management chip."
            step["check"]="Support the free edge by hand. The solid gauge’s calculated centre of mass falls outside the support footprint. When you let go it can tip."
        if step["title"]=="Lower the display onto its four seats":
            step["instruction"]="Support the loose A4, A5 and USB2 gauges while turning the display over. Lower the assembly onto the four housing seats. The fixed display lands move with A1."
        if "checklist" in step:
            step["checklist"][-1]="Count all eight board gauges and four removable A2 shims. The new display gauge carries all six A4/A5 lands. Count six loose blocks only if using the original Plate 7 display."
        if step["title"]=="Inspect the integral A3 rails":
            step["instruction"]="Find the two rails printed into the housing floor. Reuse the R0013 plate 7 board gauges. Set aside the loose A3 strips. Use the A4/A5 blocks only with the original plain display gauge."
