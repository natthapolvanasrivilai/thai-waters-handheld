"""Verify both straight legs of the inside-loading cap path in installed coordinates."""
import hashlib
import json
from argparse import ArgumentParser
from pathlib import Path

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh
from OCP.BRepAdaptor import BRepAdaptor_Surface


HERE = Path(__file__).resolve().parent
R14 = HERE.parents[1]
MECH = R14.parent
ROOT = MECH.parents[1]
R11 = MECH / "TW-A-0001-R0011"
GAUGES = MECH / "pcb-fit-r0013"
OFFSETS = [(0, 0, 0), (0, -2.5, 0), (0, -2.5, 24)]
TOL_MM3 = 0.000001
V = cq.Vector


def read(path):
    return json.loads(path.read_bytes())


def checked_file(path, expected, sources):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == expected, f"Source changed: {path}"
    sources[path.resolve().relative_to(ROOT).as_posix()] = digest
    return str(path)


def load_cad(name, path, expected, installed, sources):
    shape = cq.Shape.importBrep(checked_file(path, expected, sources))
    datum = installed[name]
    box = shape.BoundingBox()
    bounds = [getattr(box, k) for k in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")]
    assert shape.isValid() and len(shape.Solids()) == datum["solids"], name
    np.testing.assert_allclose(bounds, datum["bounds_mm"], rtol=0, atol=.0001)
    assert abs(shape.Volume() - datum["volume_mm3"]) < .002, name
    return shape


def load_print(base, name, sources):
    pose = read(base / "part-orientations.json")[name]
    path = base / pose["print_stl"]
    mesh = trimesh.load_mesh(checked_file(path, pose["sha256"], sources))
    mesh.apply_transform(np.linalg.inv(pose["assembly_to_print"]))
    solid = mf.Manifold(mf.Mesh64(np.ascontiguousarray(mesh.vertices),
                                  np.ascontiguousarray(mesh.faces, dtype=np.uint64)))
    assert solid.status() == mf.Error.NoError and not solid.is_empty(), name
    return solid


def cylinder(y, length, radius):
    return cq.Solid.makeCylinder(radius, length, V(-36, y, 12.5), V(0, 1, 0))


def cad_sweeps(cap):
    # The union of these two coaxial cylinders encloses the controlled cap
    # (proved below), including the engraved and filleted face. Extending each
    # cylinder along its axis covers *all* intermediate horizontal positions.
    _, inside, above = OFFSETS
    pull = -inside[1]
    seated_bound = cylinder(33, .54, 3.85).fuse(cylinder(33.54, .78, 2.75))
    assert abs(cap.cut(seated_bound).Volume()) < TOL_MM3
    slide = cylinder(33 - pull, .54 + pull, 3.85).fuse(
        cylinder(33.54 - pull, .78 + pull, 2.75))
    # Enclose both ends' bounding boxes, and therefore the entire straight drop.
    b = cap.translate(inside).BoundingBox()
    drop = cq.Solid.makeBox(b.xlen, b.ylen, b.zlen + above[2], V(b.xmin, b.ymin, b.zmin))
    return {"drop": drop, "slide": slide}


def mesh_sweeps(cap):
    # Convex hulls of two translated copies contain every interpolated vertex
    # and triangle. Split the flange at its shoulder to preserve the stepped
    # profile during the outward slide. Both halves participate in the proof.
    _, inside, above = OFFSETS
    def envelope(part, a, b):
        return mf.Manifold.batch_hull([part.translate(a), part.translate(b)])
    front, flange = cap.split_by_plane((0, 1, 0), 33.540001)
    assert not front.is_empty() and not flange.is_empty()
    slide = envelope(front, inside, OFFSETS[0]) + envelope(flange, inside, OFFSETS[0])
    return {"drop": envelope(cap, above, inside), "slide": slide}


def coaxial_radii(part, y):
    radii = []
    for face in part.Faces():
        if face.geomType() != "CYLINDER":
            continue
        surface = BRepAdaptor_Surface(face.wrapped).Cylinder()
        center, direction = surface.Location(), surface.Axis().Direction()
        box = face.BoundingBox()
        if (abs(center.X()+36) < .0001 and abs(center.Z()-12.5) < .0001
                and abs(direction.Y()) > .99999 and box.ymin < y < box.ymax):
            radii.append(surface.Radius())
    radius, = radii
    return radius


def verify(assembly=R14):
    sources = {}
    reg = read(assembly / "installed-step.json")
    installed = reg["components"]
    housing = installed["Housing"]
    case = load_cad("Housing", assembly / housing["source_brep"], housing["source_sha256"],
                    installed, sources)
    previous = {r["id"]: r for r in read(MECH / "TW-A-0001-R0009/assembly-parts.json")}
    parts = {}
    for name in ("Key cap", "Retainer", "Key PCB", "Switch case", "Switch plunger", "Trimmed terminals"):
        row = previous[name]
        parts[name] = load_cad(name, ROOT / row["source"], row["geometrySha256"], installed, sources)
    cap = parts.pop("Key cap")
    cap_mesh = load_print(R11, "power-cap", sources)
    case_mesh = load_print(assembly, "housing-battery-bay", sources)
    sweeps = cad_sweeps(cap)
    print_sweeps = mesh_sweeps(cap_mesh)

    phases = {}
    for name, envelope in sweeps.items():
        print_envelope = print_sweeps[name]
        overlap = print_envelope ^ case_mesh
        assert print_envelope.status() == overlap.status() == mf.Error.NoError
        gap = envelope.distance(case)
        print_gap = print_envelope.min_gap(case_mesh, 2.0)
        common = abs(envelope.intersect(case).Volume())
        print_common = abs(overlap.volume())
        assert min(gap, print_gap) > .001 and max(common, print_common) < TOL_MM3, name
        phases[name] = dict(cad_envelope_gap_mm=round(gap, 6), cad_common_mm3=round(common, 8),
                            print_envelope_gap_mm=round(print_gap, 6),
                            print_common_mm3=round(print_common, 8))

    upper = cap.translate(OFFSETS[-1]).BoundingBox()
    clear = upper.zmin - case.BoundingBox().zmax
    assert clear > 4.8
    flange, face = coaxial_radii(cap, 33.15), coaxial_radii(cap, 33.8)
    bore, hole = coaxial_radii(case, 33.2), coaxial_radii(case, 34.1)
    assert bore > flange > hole > face
    # Every fixed item in the guide's preinstalled group is on the +X side
    # of the cap. A separating axis suffices throughout both translation legs.
    xmax = max(s.BoundingBox().xmax for s in sweeps.values())
    xmin = {k: installed[k]["bounds_mm"][0] for k in ("Rotor", "Collar")}
    gauges = read(GAUGES / "geometry.json")["parts"]
    for k in ("A2-sensor", "A3-haptic"):
        xmin[k] = gauges[k]["installed_min_max_mm"][0][0]
    # The four illustrated 0.25 mm shims occupy the land face at X41.05.
    xmin["Four A2 shims"] = 41.05
    separation = {k: round(v - xmax, 5) for k, v in xmin.items()}
    assert min(separation.values()) > 40
    seated = {name: round(cap.distance(part), 6) for name, part in parts.items()}
    assert min(seated.values()) > 0 and abs(seated["Switch plunger"] - .05) < .00001

    # The +6 mm exterior route used by the former animation necessarily
    # includes this offset. The second control uses the real fixed switch.
    wrong = cap.translate((0, .5, 0))
    outside = abs(wrong.intersect(case).Volume())
    mesh_control = cap_mesh.translate((0, .5, 0)) ^ case_mesh
    assert mesh_control.status() == mf.Error.NoError and mesh_control.volume() > 8
    inside = cap.translate((0, -1, 0))
    keeper_hit = abs(inside.intersect(parts["Retainer"]).Volume())
    plunger_hit = abs(inside.intersect(parts["Switch plunger"]).Volume())
    assert outside > 8 and keeper_hit > .28 and plunger_hit > 12
    return dict(
        assembly=assembly.name, part="cap", frame="Installed XYZ, millimetres; +Y outward at the key, +Z toward the display.",
        removal_offsets_mm=OFFSETS, insertion="Read offsets in reverse; hold orientation and interpolate each leg separately.",
        prerequisites="Open housing; cap precedes upright KEY board, switch, keeper, keeper screw, display and bezel.",
        sources_sha256=sources, installed_assembly_step_sha256=reg["step_sha256"],
        approach_above_entire_housing_mm=round(clear, 6),
        capture=dict(flange_diameter_mm=2*flange, cap_face_diameter_mm=2*face,
                     inner_counterbore_diameter_mm=2*bore, outer_hole_diameter_mm=2*hole,
                     flange_radial_overlap_with_outer_hole_mm=round(flange-hole, 5)),
        insertion_legs=phases, limiting_pair="Cap flange to housing counterbore shoulder at seated end of +Y slide.",
        other_fixed_parts_x_separation_lower_bounds_mm=separation, seated_cap_gaps_mm=seated,
        controls=dict(exterior_offset_mm=[0,.5,0], exterior_cap_to_housing_common_mm3=round(outside, 6),
                      exterior_print_common_mm3=round(mesh_control.volume(), 6),
                      obstructed_interior_offset_mm=[0,-1,0],
                      cap_to_installed_keeper_common_mm3=round(keeper_hit, 6),
                      cap_to_installed_stationary_plunger_common_mm3=round(plunger_hit, 6)),
        numerical_volume_threshold_mm3=TOL_MM3,
        scope="Continuous, conservative rigid envelopes on the installed nominal BREP and registered original print meshes. Nominal distances; physical seating, print tolerance, hand access and press feel require a dry fit.")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", type=Path, default=R14, help="Registered R0014 or derived enclosure directory")
    assembly = parser.parse_args().assembly.resolve()
    result = verify(assembly)
    out = assembly / "QA/power-key/cap-path.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(result["insertion_legs"], result["controls"])
