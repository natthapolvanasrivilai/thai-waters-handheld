"""Regenerate the handbook viewer from registered fit STLs. Run with the CAD Python environment."""
import base64
import json
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MECHANICAL = ROOT / "hardware/mechanical"
GAUGES = MECHANICAL / "pcb-fit-r0013"
R20 = MECHANICAL / "pocket-reel-r19b-removal-trial"
sys.path.insert(0, str(GAUGES))
import check_assembly_fit as fit


BOARD_IDS = {
    "A1-display": "A1", "A2-sensor": "A2", "A3-haptic": "A3", "A4-integration": "A4",
    "A5-power": "A5", "KEY-switch": "KEY", "USB-PCB1": "USB1", "USB-PCB2": "USB2",
}
CASE_IDS = {
    "Housing": "housing", "Bezel": "bezel", "Rotor": "rotor", "Collar": "collar",
    "Bridge": "bridge", "Key keeper": "keeper", "Key cap": "cap", "Service cover": "serviceCover",
    "U guide": "uGuide", "C guide": "cGuide", "P guide": "pGuide", "PKCELL": "pkcell",
    "Adafruit": "adafruit",
}
SCALE = .001


def read(path):
    return json.loads(path.read_bytes())


def checked_mesh(path, expected):
    if fit.digest(path) != expected:
        raise ValueError(f"Source differs from controlled mesh: {path}")
    return trimesh.load_mesh(path)


def affine(rows):
    matrix = np.eye(4)
    matrix[:3] = rows
    return matrix


def encode(array, dtype):
    return base64.b64encode(np.asarray(array, dtype=dtype).tobytes()).decode("ascii")


class Scene:
    def __init__(self):
        self.parts = {}
        self.solids = {}

    def add(self, name, mesh, source, pose, tolerance=.009, illustration=False):
        # Work in the installed frame throughout. Keep original solids for the checks.
        mesh.apply_transform(pose)
        shape = fit.solid(mesh)
        self.solids[name] = shape
        display = shape.simplify(tolerance).to_mesh64()
        vertices = np.rint(display.vert_properties[:, :3] / SCALE).astype("<i4")
        faces = np.asarray(display.tri_verts, dtype="<u4")
        bounds = np.array([vertices.min(0), vertices.max(0)]) * SCALE
        np.testing.assert_allclose(bounds, mesh.bounds, atol=tolerance + SCALE, rtol=0)
        # Verify the actual serialized mesh, including the coordinate quantization.
        decoded = fit.solid(trimesh.Trimesh(vertices * SCALE, faces, process=False))
        if abs(decoded.volume() / shape.volume() - 1) > .006:
            raise ValueError(f"Viewer geometry volume drift: {name}")
        self.parts[name] = {
            "source": source.resolve().relative_to(ROOT).as_posix(),
            "sourceSha256": fit.digest(source),
            "illustration": illustration, "simplifyToleranceMm": tolerance,
            "bounds": bounds.round(3).tolist(),
            "v": encode(vertices, "<i4"), "f": encode(faces, "<u4"),
        }
        return mesh


def build():
    scene = Scene()
    ledger_path = GAUGES / "geometry.json"
    report = read(GAUGES / "assembly-fit.json")
    if fit.digest(ledger_path) != report["geometry_json_sha256"]:
        raise ValueError("Gauges and fit evidence belong to different builds")
    for name, row in read(ledger_path)["parts"].items():
        path = GAUGES / row["file"]
        mesh = checked_mesh(path, row["sha256"])
        mesh = scene.add(BOARD_IDS[name], mesh, path, affine(row["print_to_installed_3x4"]), .002)
        np.testing.assert_allclose(mesh.bounds, row["installed_min_max_mm"], atol=.0001, rtol=0)

    orientations = read(fit.HOUSING / "part-orientations.json")
    for label, original in fit.COMPANIONS.items():
        row = orientations[original]
        path = fit.HOUSING / row["print_stl"]
        mesh = checked_mesh(path, row["sha256"])
        pose = np.linalg.inv(row["assembly_to_print"])
        if label in ("Adafruit", "PKCELL"):
            pose[:3, 3] += (-10.4, -.65, 3.6)
        scene.add(CASE_IDS[label], mesh, path, pose)

    fixture_ids = dict(CASE_IDS)
    for original, (bottom, centers) in fit.SUPPORTS.items():
        path = GAUGES / "meshes" / (original + ".stl")
        for index, (x, y) in enumerate(centers, 1):
            name = f"{original[:2]}s{index}"
            mesh = checked_mesh(path, report["dry_spacer_stl_sha256"][original])
            mesh = scene.add(name, mesh, path, trimesh.transformations.translation_matrix((x,y,bottom)))
            recorded = report["dry_spacer_coverage_at_faces"][f"{original}-{index}"]
            fixture_ids[f"{original}-{index}"] = name
            np.testing.assert_allclose(mesh.bounds[:,2], recorded["installed_bottom_top_mm"], atol=.0001)
            under, above = (("housing","A3") if original.startswith("A3") else (original[:2],"A1"))
            contact = fit.seat_contact(scene.solids[name], bottom, scene.solids[under], scene.solids[above])
            if contact != recorded:
                raise ValueError(f"Support registration or face contact changed: {name}")

    # Use original, unsimplified solids for the same pairwise checks as the
    # controlled fit ledger. Both battery alternatives are checked in turn.
    for board, recorded in report["final_gauges_to_full_case_parts_common_mm3"].items():
        for fixture, volume in recorded.items():
            actual = fit.common(scene.solids[BOARD_IDS[board]], scene.solids[fixture_ids[fixture]])
            if abs(actual - volume) > .00001:
                raise ValueError(f"Installed fit changed for {board} against {fixture}")
    for pair, volume in report["final_gauge_pairs_common_mm3"].items():
        first, second = pair.split(" / ")
        actual = fit.common(scene.solids[BOARD_IDS[first]], scene.solids[BOARD_IDS[second]])
        if abs(actual - volume) > .00001:
            raise ValueError(f"Gauge fit changed for {pair}")

    path = fit.CARRIER
    carrier = checked_mesh(path, report["r20_carrier_stl_sha256"])
    carrier_pose = read(MECHANICAL / "TW-A-0001-R0013/QA/r20-carrier-fit.json")["installed_transform"]
    r20_reference = read(R20 / "QA/nominal-fit.json")
    np.testing.assert_equal(carrier_pose, r20_reference["carrier_print_to_installed_mm"])
    contact = fit.r20_interface(carrier, scene.solids["A2"], carrier_pose)
    if contact != report["r20_gauge_interfaces"]:
        raise ValueError("R20 pins and A2 holes differ from the reviewed fit")
    scene.add("carrier", carrier, path, affine(carrier_pose), .002)
    path = R20 / "Print/R20 floor pocket section.stl"
    floor = checked_mesh(path, "1d425ca10c66ff473e2fb067f349049dd0b82c5f547d3a58d9765e2e12180566")
    # R20 build.floor_sample crops installed XY and Z0.1..2.5. Its STL export
    # preserves XY and drops the lowest Z to the print bed.
    floor = scene.add("floor", floor, path, trimesh.transformations.translation_matrix((0,0,.1)), .002)
    np.testing.assert_allclose(floor.bounds, [[40,-11,.1],[48,11,2.5]], atol=.00001)
    floor_shape, carrier_shape = scene.solids["floor"], scene.solids["carrier"]
    if fit.common(floor_shape, carrier_shape) != r20_reference["nominal_carrier_floor_sample_intersection_mm3"]:
        raise ValueError("R20 carrier intersects its floor coupon")
    if fit.common(floor_shape, carrier_shape.translate((0,4,0))) < .5:
        raise ValueError("Displaced keys did not intersect the floor coupon")
    if fit.common(carrier_shape, scene.solids["A2"]) != report["r20_to_a2_gauge_common_mm3"]:
        raise ValueError("R20 carrier intersects A2")

    # Illustrative measured stock. An annulus clears the locating pin and
    # reproduces the available bearing footprint on each drilled PCB corner.
    land_rows = fit.integral_lands(scene.solids["housing"], scene.solids["A2"], carrier_pose)
    if land_rows != report["r0011_integral_lands_0p25mm_dry_shim"]:
        raise ValueError("Integral housing shim seats differ from the controlled assembly")
    stock = mf.CrossSection.circle(1.85, 128) - mf.CrossSection.circle(1.25, 128)
    shape = stock.extrude(.25).rotate((0,90,0)).to_mesh64()
    for i, row in enumerate(land_rows, 1):
        y, z = row["installed_YZ_mm"]
        mesh = trimesh.Trimesh(shape.vert_properties[:,:3], shape.tri_verts, process=False)
        pose = trimesh.transformations.translation_matrix((41.05,y,z))
        scene.add(f"A2s{i}", mesh, GAUGES / "assembly-fit.json", pose, .001, illustration=True)
        for neighbor in ("housing", "A2"):
            if fit.common(scene.solids[f"A2s{i}"], scene.solids[neighbor]) > .0001:
                raise ValueError("Stock intersects its neighbor")

    return {
        "units": "mm", "scale": SCALE, "assembly": "TW-A-0001-R0013",
        "frame": "Installed XYZ: +X reel, +Y power cap, +Z display",
        "encoding": "v: base64 little-endian int32 XYZ times scale; f: base64 little-endian uint32 triangle indices",
        "parts": scene.parts,
    }


if __name__ == "__main__":
    scene = build()
    target = HERE / "scene.json"
    target.write_bytes((json.dumps(scene, separators=(",",":"), allow_nan=False) + "\n").encode())
    print(f"Wrote {len(scene['parts'])} registered meshes, {target.stat().st_size:,} bytes")
