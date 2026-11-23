"""Measure the PCB gauges at their registered poses in each fit fixture."""
import argparse
import itertools
import json
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import manifold3d as mf
import numpy as np
import trimesh
from scipy.spatial import cKDTree


HERE = Path(__file__).resolve().parent
HOUSING = HERE.with_name("TW-A-0001-R0011")
CARRIER = HERE.with_name("pocket-reel-r19b-removal-trial") / "Print/R20 keyed encoder carrier.stl"
COMPANIONS = {
    "Housing": "housing-battery-bay",
    "Bezel": "bezel",
    "Rotor": "rotor",
    "Collar": "collar",
    "Bridge": "battery-wire-bridge",
    "Key keeper": "key-board-retainer-west",
    "Key cap": "power-cap",
    "Service cover": "service-cover",
    "U guide": "status-usb-guide",
    "C guide": "status-charge-guide",
    "P guide": "status-power-guide",
    "PKCELL": "PKCELL-max-body-with-wire-sockets",
    "Adafruit": "Adafruit-258-CAD-with-PCM-and-stubs",
}
# Installed XY centers of adhesive and spacer footprints in R0013.
SUPPORTS = {
    "A3-floor-shim": (2.5, [(18,-6), (26,-6)]),
    "A4-display-shim": (18.535, [(15.5,-10), (33.5,-9.5), (33.5,-1.5)]),
    "A5-display-shim": (17.840, [(17.5,16.5), (28.5,14.1), (32.5,17.3)]),
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def solid(mesh):
    shape = mf.Manifold(mf.Mesh64(np.ascontiguousarray(mesh.vertices),
                                  np.ascontiguousarray(mesh.faces, dtype=np.uint64)))
    if shape.status() != mf.Error.NoError or shape.is_empty():
        raise ValueError("Invalid solid mesh")
    return shape


def baseline_parts(project):
    pose = json.loads((HOUSING / "part-orientations.json").read_bytes())
    if digest(project) != "510fe8e2f1930c18298fb90d9a3b1edf74ac57c71bcb89fc985bed1fc49af50f":
        raise ValueError("Use the exact published R0011 six-plate X1C project")
    installed = {}
    errors = {}
    with ZipFile(project) as z:
        settings = ET.fromstring(z.read("Metadata/model_settings.config"))
        graph = ET.fromstring(z.read("3D/3dmodel.model"))
        for label, name in COMPANIONS.items():
            row = pose[name]
            path = HOUSING / row["print_stl"]
            if digest(path) != row["sha256"]:
                raise ValueError(path)
            mesh = trimesh.load_mesh(path)
            # Verify the centered native vertices bidirectionally before using
            # the controlled STL and its recorded inverse print transformation.
            obj = next(o for o in settings.findall("object") if
                       o.find("metadata[@key='name']").get("value") == name + "_1")
            comp = graph.find(f".//{{*}}object[@id='{obj.get('id')}']/{{*}}components/{{*}}component")
            resource = next(v for k,v in comp.attrib.items() if k.endswith("}path"))
            doc = ET.fromstring(z.read(resource.lstrip("/")))
            vertices = np.array([[float(v.get(k)) for k in "xyz"]
                                 for v in doc.findall(".//{*}vertices/{*}vertex")])
            centered = vertices - (vertices.min(0) + vertices.max(0))/2
            source = mesh.vertices - mesh.bounds.mean(0)
            error = max(cKDTree(centered).query(source)[0].max(),
                        cKDTree(source).query(centered)[0].max())
            if error > 0.0001:
                raise ValueError(f"{label} native point sets differ by {error} mm")
            errors[label] = round(float(error),8)
            mesh.apply_transform(np.linalg.inv(row["assembly_to_print"]))
            if label in ("PKCELL","Adafruit"):
                mesh.apply_translation((-10.4,-0.65,3.6))
            installed[label] = solid(mesh)
    return installed, errors


def common(a, b):
    overlap = a ^ b
    if overlap.status() != mf.Error.NoError:
        raise ValueError("Unresolved mesh Boolean")
    return round(max(0.0, overlap.volume()),6)


def seat_contact(shim, bottom, under, above):
    top = shim.bounding_box()[5]
    patch = shim.slice(bottom + 0.001)
    # Move one micron inside each neighboring solid to avoid an ambiguous
    # coplanar section. This checks coverage on both faces of each dry spacer.
    return {
        "installed_bottom_top_mm": [round(bottom,4), round(top,4)],
        "footprint_mm2": round(patch.area(),4),
        "lower_coverage_mm2": round((patch ^ under.slice(bottom - 0.001)).area(),4),
        "upper_coverage_mm2": round((patch ^ above.slice(top + 0.001)).area(),4),
    }


def r20_interface(carrier_mesh, gauge, transform):
    native = solid(carrier_mesh)
    matrix = np.eye(4)
    matrix[:3] = transform
    board = gauge.transform(np.linalg.inv(matrix)[:3])
    seat_z, tip_z = 5.95, float(carrier_mesh.bounds[1,2])
    height = (tip_z + seat_z) / 2
    board_section = board.slice(height).to_polygons()
    installed = []
    for polygon in native.slice(height).to_polygons():
        limits = np.vstack((polygon.min(0), polygon.max(0)))
        center = limits.mean(0)
        # Find the smallest board section enclosing each pin center by its bounds.
        holes = [p for p in board_section if (p.min(0) < center).all() and (p.max(0) > center).all()]
        hole = min(holes,key=lambda p: np.prod(p.max(0)-p.min(0)))
        hole_center = (hole.max(0)+hole.min(0))/2
        pose = matrix @ [*center,seat_z,1]
        installed.append({
            "installed_YZ_mm": np.round(pose[1:3],4).tolist(),
            "hole_to_pin_center_offset_mm": round(float(np.linalg.norm(center-hole_center)),5),
            "pin_diameter_across_xy_mm": np.round(limits[1]-limits[0],4).tolist(),
            "gauge_bore_diameter_across_xy_mm": np.round(hole.max(0)-hole.min(0),4).tolist(),
        })
    # Verify coplanar annular contact at all four support heads, including
    # the clipped corner relief. Clear material immediately above and below
    # the datum is measured separately from the pin intersection.
    seats = []
    for x,y in itertools.product((-10.16,10.16),(-4.555,8.145)):
        window = mf.CrossSection.square((5,5),center=True).translate((x,y))
        patch = window ^ native.slice(seat_z-.001) ^ board.slice(seat_z+.001)
        seats.append({"installed_YZ_mm": [-x,round(y+13.005,4)],"contact_patch_mm2":round(patch.area(),4)})
    for pin in installed:
        if (pin["hole_to_pin_center_offset_mm"] > .005
                or not np.allclose(pin["pin_diameter_across_xy_mm"], 2.05, atol=.005)
                or not np.allclose(pin["gauge_bore_diameter_across_xy_mm"], 2.50, atol=.005)):
            raise ValueError("R20 pin-to-A2 registration or diameter changed")
    if len(installed) != 2 or min(s["contact_patch_mm2"] for s in seats) < 1:
        raise ValueError("Missing locating pin or PCB seat in R20 comparison")
    return {"r20_seat_height_print_Z_mm":seat_z, "r20_pin_tip_print_Z_mm":round(tip_z,4),
            "pin_depth_mm": round(tip_z-seat_z,4), "diagonal_pins":installed, "board_support":seats}


def integral_lands(housing, board, transform):
    # Reuse the carrier coordinate frame solely to take sections normal to
    # the sensor plane. The integral-case design has its own head position.
    matrix = np.eye(4)
    matrix[:3] = transform
    to_seat = np.linalg.inv(matrix)[:3]
    case, gauge = housing.transform(to_seat), board.transform(to_seat)
    rows = []
    for x,y in itertools.product((-10.16,10.16),(-4.555,8.145)):
        region = mf.CrossSection.square((4.2,4.2),center=True).translate((x,y))
        land = case.slice(5.699) ^ region
        # Between the shoulder and seated component-side face only pins remain.
        in_gap = case.slice(5.825) ^ region
        occupied = case.slice(6.60) ^ region
        hole_side = gauge.slice(5.951) ^ region
        rows.append({"installed_YZ_mm": [-x,round(y+13.005,4)],
                     "shoulder_extent_mm": round(land.bounds()[2]-land.bounds()[0],4),
                     "pin_extent_mm": round(occupied.bounds()[2]-occupied.bounds()[0],4) if occupied.area() else 0,
                     "shim_supported_board_area_mm2": round(((land-in_gap) ^ hole_side).area(),4)})
    return rows


def check(r0011, gauges):
    fixtures, errors = baseline_parts(r0011)
    ids = list(gauges)
    seating = {}
    for name, (bottom, centers) in SUPPORTS.items():
        shim = solid(trimesh.load_mesh(HERE / "meshes" / (name + ".stl")))
        for i,(x,y) in enumerate(centers, start=1):
            key = f"{name}-{i}"
            fixtures[key] = shim.translate((x,y,bottom))
            board = {"A3-floor-shim":"A3-haptic","A4-display-shim":"A4-integration",
                     "A5-display-shim":"A5-power"}[name]
            under, above = ((fixtures["Housing"], gauges[board]) if name == "A3-floor-shim"
                            else (gauges[board], gauges["A1-display"]))
            seating[key] = seat_contact(fixtures[key],bottom,under,above)

    pairs = {g: {f: common(gauges[g],s) for f,s in fixtures.items()} for g in ids}
    board_pairs = {f"{a} / {b}": common(gauges[a],gauges[b])
                   for a,b in itertools.combinations(ids,2)}
    # Registration maps the released STL's local print XYZ into device XYZ.
    transform = json.loads((HERE.with_name("TW-A-0001-R0013") /
                            "QA/r20-carrier-fit.json").read_bytes())["installed_transform"]
    carrier_mesh = trimesh.load_mesh(CARRIER)
    carrier = solid(carrier_mesh).transform(transform)
    a2_only = common(carrier,gauges["A2-sensor"])
    # Shift the dummy along device Y, forcing material into the two locating pins.
    displaced = common(carrier,gauges["A2-sensor"].translate((0,1.5,0)))
    if displaced < 0.1:
        raise RuntimeError("A2 shifted-hole negative control failed")
    return {
        "units": "mm and mm3",
        "source_3mf_sha256": digest(r0011),
        "geometry_json_sha256": digest(HERE/"geometry.json"),
        "gauge_stl_sha256": {k:digest(HERE/"meshes"/(k+".stl")) for k in ids},
        "dry_spacer_stl_sha256": {k:digest(HERE/"meshes"/(k+".stl")) for k in SUPPORTS},
        "r0011_centered_vertex_set_max_error_mm": errors,
        "final_gauges_to_full_case_parts_common_mm3": pairs,
        "final_gauge_pairs_common_mm3": board_pairs,
        "r20_carrier_stl_sha256": digest(CARRIER),
        "r20_to_a2_gauge_common_mm3": a2_only,
        "r20_gauge_interfaces": r20_interface(carrier_mesh,gauges["A2-sensor"],transform),
        "r0011_integral_lands_0p25mm_dry_shim": integral_lands(fixtures["Housing"],gauges["A2-sensor"],transform),
        "dry_spacer_coverage_at_faces": seating,
        "r20_to_a2_negative_control_plus_1p5_y_common_mm3": displaced,
        "scope": "Nominal final mesh solids in registered poses. Pack variants tested separately. The compliant USB diaphragm, harness, fasteners, tolerance, insertion forces and motion are outside this screen."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("r0011", type=Path)
    args = parser.parse_args()
    ledger = json.loads((HERE/"geometry.json").read_bytes())
    poses = ledger["parts"]
    gauges = {}
    for name,row in poses.items():
        world = np.eye(4)
        world[:3] = row["print_to_installed_3x4"]
        path = HERE / row["file"]
        if digest(path) != row["sha256"]:
            raise ValueError(f"Gauge digest differs from installed pose ledger: {name}")
        mesh = trimesh.load_mesh(path)
        mesh.apply_transform(world)
        gauges[name] = solid(mesh)
    report = check(args.r0011, gauges)
    (HERE/"assembly-fit.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    # Fractional micrometre overlaps on nominally coplanar STL surfaces
    # contribute less than this numerical volume allowance.
    tolerance = 0.0001
    volumes = [vol for row in report["final_gauges_to_full_case_parts_common_mm3"].values()
               for vol in row.values()]
    volumes.extend(report["final_gauge_pairs_common_mm3"].values())
    volumes.append(report["r20_to_a2_gauge_common_mm3"])
    if max(volumes) > tolerance:
        raise ValueError(f"Installed gauge interference exceeds {tolerance} mm3: {max(volumes)}")
    for s in report["dry_spacer_coverage_at_faces"].values():
        if abs(s["footprint_mm2"] - min(s["lower_coverage_mm2"],s["upper_coverage_mm2"])) > .001:
            raise ValueError("A support misses a gauge face")
