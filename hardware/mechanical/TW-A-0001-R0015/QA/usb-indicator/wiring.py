"""Check the seated blue lamp and a necessary length condition for lifting the wired display."""
from hashlib import sha256
import json
import math
from pathlib import Path

import cadquery as cq


HERE = Path(__file__).resolve().parent
MECH = HERE.parents[2]
ROOT = MECH.parents[1]
ELECTRONICS = ROOT / "hardware/electronics"
LAMP = ELECTRONICS / "usb-status-r0003/placed"
FIXED = ELECTRONICS / "usb-entry-r0006/installed-leads"
OLD_CAD = MECH / "TW-A-0001-R0009/CAD"
DISPLAY_LIFT = 18.0  # A1 displacement in the dry fit guide.


def load(path):
    return json.loads(path.read_bytes())


def read_shape(path, record):
    record[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    shape = cq.Shape.importBrep(str(path))
    if not shape.isValid():
        raise ValueError(f"Invalid CAD: {path}")
    return shape


def installed(shape, ledger):
    bb = shape.BoundingBox()
    bounds = [getattr(bb, s) for s in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")]
    if (not math.isclose(shape.Volume(), ledger["volume_mm3"], abs_tol=0.0001)
            or len(shape.Solids()) != ledger["solids"]
            or max(abs(a - b) for a, b in zip(bounds, ledger["bounds_mm"])) > 0.00011):
        raise ValueError("Source body differs from the registered installed pose")


def length_bound(points, moving, fixed):
    # These endpoints are the far tips of the solder tails. Count the whole tail
    # at both ends as usable wire, even though solder arrests part of each tail.
    spline = cq.Edge.makeSpline([cq.Vector(*p) for p in points])
    length = spline.Length() + math.dist(points[0], moving) + math.dist(points[-1], fixed)
    lifted = (*moving[:2], moving[2] + DISPLAY_LIFT)
    required = math.dist(lifted, fixed)
    max_lift = math.sqrt(length**2 - math.dist(moving[:2], fixed[:2])**2) - (moving[2] - fixed[2])
    if required <= length:
        raise ValueError("The retained 18 mm overextension control no longer fails")
    return {
        "moving_display_solder_tip_mm": moving, "fixed_lamp_solder_tip_mm": fixed,
        "full_conductor_length_mm": round(length, 5),
        "straight_distance_at_18_mm_lift_mm": round(required, 5),
        "minimum_length_deficit_mm": round(required - length, 5),
        "upper_bound_on_pure_vertical_lift_mm": round(max_lift, 5),
    }


def main():
    hashes = {}
    files = {
        "statusUsbGuide": OLD_CAD / "status-usb-guide.brep",
        **{name: LAMP / (name + ".brep") for name in ("USB-PCB1", "USB-D1", "USB-W4B", "USB-W4B-Cu")},
        **{name: FIXED / (name + ".brep") for name in ("USB-W4C", "USB-W4C-Cu")},
    }
    parts = {name: read_shape(path, hashes) for name, path in files.items()}
    revisions = {}
    for revision in (13, 14, 15, 16):
        path = MECH / f"TW-A-0001-R{revision:04}"
        ledger = load(path / "installed-step.json")["components"]
        housing_path = (OLD_CAD if revision == 13 else path / "CAD") / "housing-battery-bay.brep"
        housing = read_shape(housing_path, hashes)
        installed(housing, ledger["Housing"])
        # Crop around the seated paths. The complete checked geometry is inside
        # this box with > 2 mm margin (the guide intentionally crosses the wall).
        local_wall = housing.intersect(cq.Solid.makeBox(43, 35, 27, cq.Vector(-54, -7, 6)))
        distances = {}
        for name, part in parts.items():
            installed(part, ledger[name])
            distance = part.distance(local_wall)
            if revision == 16 and name == "USB-PCB1":
                # The new shelf and far stop locate two faces of the substrate.
                assert distance < 1e-6 and abs(part.intersect(local_wall).Volume()) < 1e-7
            elif distance < 1e-6:
                raise ValueError(f"Inspect seated contact: {revision} {name}")
            distances[name] = round(distance, 6)
        guide = parts["statusUsbGuide"]
        # Octagonal U pipe is prismatic along X. Extend its complete footprint
        # outward to model every point on a 12 mm insertion from the west face.
        west_face = min(guide.Faces(), key=lambda face: face.Center().x)
        sweep = cq.Solid.extrudeLinear(west_face.outerWire(), [], cq.Vector(19.32, 0, 0))
        sweep = sweep.translate((-12, 0, 0))
        guide_insertion = sweep.distance(housing)
        if guide_insertion < 1e-6:
            raise ValueError(f"Inspect U pipe exterior insertion: {revision}")
        revisions[path.name] = {
            "seated_distance_to_housing_mm": distances,
            "west_to_east_U_pipe_12_mm_sweep_housing_clearance_mm": round(guide_insertion, 6),
            "seated_emitter_to_light_guide_mm": round(parts["USB-D1"].distance(guide), 6),
        }

    control_path = LAMP / "placement.json"
    hashes[control_path.relative_to(ROOT).as_posix()] = sha256(control_path.read_bytes()).hexdigest()
    points = load(control_path)["wire_control_points"]
    bounds = {
        "USB-W4B": length_bound(points["USB-W4B"], (-22.02, 18.47, 18.23), (-42.14, 1.7, 13.1)),
        "USB-W4C": length_bound(points["USB-W4C"], (-16.52, 19.82, 20.75), (-42.14, -1.7, 13.1)),
    }
    report = {
        "scope": "R0006 nominal seated lamp, supplier emitter, U light pipe, jackets and stripped ends. Lamp solder fillets, manufacturing variation, retention forces and optical output are unmeasured.",
        "axis": "Lens faces west (-X). W4B anode and W4C cathode exit inboard (+X), at Y +1.70 and -1.70 mm respectively.",
        "wiring": "W4B terminates at USB2, bonded to the fixed J8 housing. W4C terminates at J8-3 and is tapped by A5-W3. A5-W7 feeds USB2 in R0006.",
        "service": "The leadless gauge can move independently. The finished lamp is tethered to A1. Support the lamp and display together during handling. A coordinated installation/removal, strain relief, tool access and final retention require a separate full assembly check.",
        "display_rigid_vertical_translation_with_seated_USB1_mm": DISPLAY_LIFT,
        "length_check_assumptions": "Fixed X and Y; lamp stays seated. Chords ignore all obstructions, bending, the W3 side tap and strain relief. Both entire solder tails count toward available conductor. Each deficit rules out that pose even under these generous assumptions.",
        "lead_length_negative_control": bounds, "revisions": revisions, "input_sha256": hashes,
    }
    (HERE / "wiring.json").write_bytes((json.dumps(report, indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
