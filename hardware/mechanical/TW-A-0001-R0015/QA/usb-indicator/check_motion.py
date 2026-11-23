"""Check step 12 against registered print meshes and both representations of USB1.

Run verify_trapped_board.py first to regenerate the legacy interval certificate.
Then run this script with the project CAD Python. Default tests R0013 through R0016.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
MECH = HERE.parents[2]
ROOT = MECH.parents[1]
GAUGES = MECH / "pcb-fit-r0013"
BASE = MECH / "TW-A-0001-R0011"
sys.path.insert(0, str(GAUGES))
import check_assembly_fit as fit


def read(path):
    return json.loads(path.read_bytes())


def record(path, sources, expected=None):
    path = path.resolve()
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected and checksum != expected:
        raise ValueError(f"Unregistered geometry: {path}")
    sources[path.relative_to(ROOT).as_posix()] = checksum
    return path


def part(revision, key, sources):
    manifest = record(revision / "part-orientations.json", sources)
    row = read(manifest)[key]
    path = record(revision / row["print_stl"], sources, row["sha256"])
    return fit.solid(trimesh.load_mesh(path)).transform(np.linalg.inv(row["assembly_to_print"])[:3])


def gauge(key, sources):
    row = read(record(GAUGES / "geometry.json", sources))["parts"][key]
    path = record(GAUGES / row["file"], sources, row["sha256"])
    return fit.solid(trimesh.load_mesh(path)).transform(row["print_to_installed_3x4"])


def box(lo, hi):
    return mf.Manifold.cube(np.subtract(hi, lo)).translate(lo)


def xyz_bounds(shape):
    return np.array(shape.bounding_box()).reshape(2, 3)


def volume(shape):
    if shape.status() != mf.Error.NoError:
        raise ValueError(f"Unresolved solid: {shape.status()}")
    return max(0., shape.volume())


def common(a, b):
    return round(volume(a ^ b), 7)


def components(sources, rev):
    parts = {}
    directory = ROOT / "hardware/electronics/usb-status-r0003/placed"
    ledger = read(record(rev / "installed-step.json", sources))["components"]
    for name in ["USB-PCB1", "USB-D1"]:
        source = cq.Shape.importBrep(str(record(directory / (name + ".brep"), sources)))
        # The lamp contains multiple solids. Tessellate each and union for common-volume tests.
        members = []
        for solid in source.Solids():
            vertices, triangles = solid.tessellate(.002, .05)
            members.append(fit.solid(trimesh.Trimesh([v.toTuple() for v in vertices], triangles)))
        shape = mf.Manifold.batch_boolean(members, mf.OpType.Add)
        b = source.BoundingBox()
        ext = [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]
        np.testing.assert_allclose(ext, ledger[name]["bounds_mm"], atol=.0001, rtol=0)
        assert abs(source.Volume() - ledger[name]["volume_mm3"]) < .0001
        parts[name] = shape
    return parts


def ray_contact(shape, housing, clear, blocked):
    """Bisect one known contiguous entry into material; brackets supplied from the opening geometry."""
    assert common(shape.translate((0,0,clear)), housing) < 1e-6
    assert common(shape.translate((0,0,blocked)), housing) > 1e-4
    while abs(clear - blocked) > .0001:
        mid = (clear + blocked) / 2
        if common(shape.translate((0,0,mid)), housing) > 1e-6:
            blocked = mid
        else:
            clear = mid
    return [round(clear, 5), round(blocked, 5)]


def leg_sweep(envelopes, start, end):
    # Each lobe is bounded by its own box. Extrusion of these boxes through an
    # axis-aligned translation equals their endpoint union's bounding box.
    assert np.count_nonzero(np.subtract(start, end)) == 1
    return mf.Manifold.batch_boolean([
        box(lo + np.minimum(start, end), hi + np.maximum(start, end)) for lo, hi in envelopes
    ], mf.OpType.Add)


def bounds_gap(a, b):
    return float(np.linalg.norm(np.maximum(0, np.maximum(a[0]-b[1], b[0]-a[1]))))


def run(revision, waypoints=None):
    sources = {}
    rev = MECH / f"TW-A-0001-R{revision:04}"
    housing = part(BASE if revision == 13 else rev, "housing-battery-bay", sources)
    optical = part(BASE, "status-usb-guide", sources)
    printed = gauge("USB-PCB1", sources)
    ledger_dir = rev if (rev / "installed-step.json").exists() else HERE.parents[1]
    real = components(sources, ledger_dir)
    population = mf.Manifold.batch_boolean(list(real.values()), mf.OpType.Add)

    prior = {name: part(BASE, fit.COMPANIONS[name], sources)
             for name in ["Rotor", "Collar", "Key cap", "Key keeper", "C guide", "P guide"]}
    prior.update({name: gauge(name, sources) for name in ["A2-sensor", "A3-haptic", "KEY-switch"]})
    # Installed bounds of the four illustrative A2 shim annuli from the actual guide.
    scene = read(ROOT / "docs/handbook/pcb-assembly/scene.json")["parts"]
    shim_bounds = {}
    for key in [f"A2s{i}" for i in range(1,5)]:
        shim_bounds[key] = scene[key]["bounds"]
        prior[key] = box(*shim_bounds[key])
    # Use each registered solid's bounding box, including purchased parts which
    # project past the dry-fit kit. The C/P optical guides use their actual meshes.
    ledger = read(ledger_dir / "installed-step.json")["components"]
    for name, item in ledger.items():
        if name.startswith(("A2-", "A3-J1-", "speaker", "reel")) or name in {
            "Speaker", "usbSurround", "usbEscutcheonLip", "drvBoard", "drvParts",
            "Key PCB", "Switch case", "Switch plunger", "Trimmed terminals", "Keeper screw",
        }:
            lo,hi = np.array(item["bounds_mm"]).reshape(3,2).T
            prior["installed " + name] = box(lo-.0001,hi+.0001)
    if revision == 13:
        for index, (x,y) in enumerate(fit.SUPPORTS["A3-floor-shim"][1], 1):
            path = record(GAUGES / "meshes/A3-floor-shim.stl", sources,
                          read(GAUGES / "assembly-fit.json")["dry_spacer_stl_sha256"]["A3-floor-shim"])
            prior[f"A3 loose shim {index}"] = fit.solid(trimesh.load_mesh(path)).translate((x,y,2.5))

    # Local crop only accelerates Boolean tests. All tested paths are enclosed with margin.
    moving_region = box((-48,-24,6),(-27,6,46))
    case = housing ^ moving_region
    movers = {"print_gauge": printed, "populated_board": population}
    nominal_envelope = [np.array([[-42.1,-2.4,11.5],[-41.5,2.4,14.7]]),
                        np.array([[-42.352,-.8,12.7],[-42.09,.8,13.5]])]
    # One nanometre on all faces encloses both the native part and STL quantization.
    envelope = [bounds + np.array([[-1e-6],[1e-6]]) for bounds in nominal_envelope]
    envelope_shape = mf.Manifold.batch_boolean([box(lo,hi) for lo,hi in envelope], mf.OpType.Add)
    for shape in movers.values():
        assert volume(shape - envelope_shape) < 1e-9

    old_offsets = {"handbook_start": [0,0,5], "lower_shroud": [0,0,1.5],
                   "upper_roof": [0,0,11], "seated": [0,0,0]}
    vertical = {key: {"offset_mm": offset, "housing_common_mm3":
                {name: common(shape.translate(offset), case) for name, shape in movers.items()}}
                for key, offset in old_offsets.items()}
    for key in ["upper_roof", "lower_shroud"]:
        assert min(vertical[key]["housing_common_mm3"].values()) > .05
    assert max(vertical["seated"]["housing_common_mm3"].values()) < 1e-6
    vertical.update(first_contact_offset_z_from_above_mm=ray_contact(printed,case,14,12),
                    first_contact_offset_z_from_handbook_start_mm=ray_contact(printed,case,4,3))
    lateral = {}
    for offset in [(1,0,0), (1,0,-.11), (0,0,-.15)]:
        lateral[str(offset)] = {key: common(shape.translate(offset),case) for key,shape in movers.items()}
    report = dict(assembly=rev.name, units="millimetres, cubic millimetres",
        frame="Installed XYZ; +X toward reel, +Z toward removed display. Offsets relative to registered PCB/LED.",
        status="blocked" if waypoints is None else "clear",
        waypoints_offset_mm=waypoints or [], waypoint_order="from above the housing to the registered seat",
        rejected_vertical=vertical, rejected_horizontal=lateral, sources_sha256=sources,
        seated_guide_gap_mm=round(real["USB-D1"].min_gap(optical,1),6),
        scope="Rigid leadless gauge or rigid PCB and LED. Flexible wiring, hand/tool access, printed tolerances and physical retention are separate.")
    if waypoints is None:
        trap = HERE / "legacy-trap.json"
        proof = read(trap)
        assert rev.name in proof["assemblies"] and len(proof["boundary_faces"]) == 12
        assert all(sources[path] == value for path,value in proof["sources_sha256"].items() if path in sources)
        report["all_rigid_routes"] = dict(evidence=trap.name, sha256=hashlib.sha256(trap.read_bytes()).hexdigest(),
                                         result=proof["result"])
        report["disposition"] = "The pocket traps the rigid board at the registered pose. A collision-free insertion into this unmodified housing is impossible."
        assert all(min(row.values()) > .02 for row in lateral.values())
    else:
        assert revision == 16
        row = read(rev / "part-orientations.json")["housing-battery-bay"]
        housing_brep = cq.Shape.importBrep(str(record(rev / row["assembly_brep"], sources)))
        assert waypoints[-1] == [0,0,0]
        report["above_rim_start_gap_mm"] = round(xyz_bounds(printed)[0,2]+waypoints[0][2]-xyz_bounds(housing)[1,2],5)
        assert report["above_rim_start_gap_mm"] > 0
        legs = []
        for start, end in zip(waypoints, waypoints[1:]):
            swept = leg_sweep(envelope,start,end)
            assert volume(swept-moving_region) < 1e-8
            nearby = {"housing":case, "U guide":optical}
            distant = {}
            for name, part_shape in prior.items():
                gap = bounds_gap(xyz_bounds(swept), xyz_bounds(part_shape))
                if gap > .01:
                    distant[name] = round(gap,5)
                else:
                    nearby[name] = part_shape
            overlaps = {key: common(swept,shape) for key,shape in nearby.items()}
            gaps = {key: round(swept.min_gap(shape,10),6) for key,shape in nearby.items()}
            floor_sliver = box((-43,-3,11.499998),(-40,3,11.500002))
            stop_sliver = box((-43,2.399998,11),(-40,2.400002,15))
            outside = round(volume((swept ^ case) - (floor_sliver + stop_sliver)), 9)
            # Intersections of the expanded envelope with nominal contact planes
            # must fit within the two two-nanometre contact bands.
            assert outside < 1e-7 and max(v for k,v in overlaps.items() if k != "housing") < 1e-7
            cad_sweeps = []
            for lo,hi in nominal_envelope:
                low, high = lo + np.minimum(start,end), hi + np.maximum(start,end)
                cad_sweeps.append(cq.Solid.makeBox(*(high-low), cq.Vector(*low)))
            cad_sweep = cad_sweeps[0].fuse(cad_sweeps[1])
            cad_common = abs(cad_sweep.intersect(housing_brep).Volume())
            assert cad_common < 1e-8, (start,end,cad_common)
            legs.append(dict(start_offset_mm=start, end_offset_mm=end, common_mm3=overlaps,
                             native_housing_nominal_envelope_common_mm3=round(cad_common,9),
                             mesh_common_outside_intended_contacts_mm3=outside,
                             gap_mm_capped_at_10=gaps, other_installed_parts_bounds_gap_mm=distant))
        report["continuous_sweep"] = legs
        report["a2_dry_shim_bounds_from_guide_mm"] = shim_bounds
        report["method"] = "Each axial leg uses the full continuous prisms swept by the PCB and LED bounding boxes. The CAD sweep uses nominal dimensions. The 0.000001 mm expanded mesh sweep encloses the real tessellated and printed parts. Only the bearing plane Z11.50 and stop Y2.40 admit mesh contact within 0.000002 mm."
    output = HERE / f"R{revision:04}.json"
    output.write_bytes((json.dumps(report,indent=2)+"\n").encode())
    print(f"{rev.name} {report['status']}",flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", type=int, action="append")
    parser.add_argument("--waypoints", type=json.loads, help="Installation offsets in mm as a JSON array")
    args = parser.parse_args()
    for number in args.revision or [13, 14, 15, 16]:
        route = args.waypoints or ([[0,-15,24],[0,-15,0],[0,0,0]] if number == 16 else None)
        run(number, route)
