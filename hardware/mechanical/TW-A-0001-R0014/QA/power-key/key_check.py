"""Recheck rigid power-board and keeper installation on the R13/R14/R15 open cases."""
from pathlib import Path
import json
import sys

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh
from OCP.BRepAdaptor import BRepAdaptor_Surface
from scipy.optimize import differential_evolution

HERE = Path(__file__).resolve().parent
MECH = HERE.parents[2]
ROOT = MECH.parents[1]
GAUGES = MECH / "pcb-fit-r0013"
R11 = MECH / "TW-A-0001-R0011"
R14 = MECH / "TW-A-0001-R0014"
SWITCH = ROOT / "hardware/components/omron-b3f-1002-g"
TRAVEL = 24
OFFSETS = [[0, 0, 0], [0, 0, TRAVEL]]
CAD_EPS = 1e-6
# The original registered STL has micrometre-scale coordinate rounding at the
# tangential rail seats. Record that full swept residual separately.
PRINT_EPS = .0001

sys.path.insert(0, str(GAUGES))
from check_assembly_fit import digest, solid


def read(path):
    return json.loads(path.read_bytes())


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def box(xlo, xhi, ylo, yhi, zlo, zhi):
    return cq.Solid.makeBox(xhi-xlo, yhi-ylo, zhi-zlo, cq.Vector(xlo, ylo, zlo))


def volume(first, second):
    return sum(s.Volume() for s in first.intersect(second).Solids())


def pair(first, second):
    return dict(common_mm3=round(volume(first, second), 7), gap_mm=round(first.distance(second), 6))


def path_key(path):
    return path.resolve().relative_to(ROOT).as_posix()


def registered_print(base, name, sources):
    row = read(base / "part-orientations.json")[name]
    path = base / row["print_stl"]
    sources[path_key(path)] = digest(path)
    assert sources[path_key(path)] == row["sha256"]
    mesh = trimesh.load_mesh(path)
    mesh.apply_transform(np.linalg.inv(row["assembly_to_print"]))
    return mesh


def cad_mesh(shape):
    pts, triangles = shape.tessellate(.003, .1)
    return trimesh.Trimesh([p.toTuple() for p in pts], triangles)


def all_geometry():
    sources = {}
    cad_dir = MECH / "TW-A-0001-R0009/CAD"
    paths = {"Key cap": cad_dir / "power-cap.brep", "Retainer": cad_dir / "key-board-retainer-west.brep",
             "Key PCB": ROOT / "hardware/electronics/power-key-r0009/Key PCB.brep"}
    for name in ("Switch case", "Switch plunger", "Trimmed terminals"):
        paths[name] = SWITCH / (name + ".brep")

    records = read(R14 / "installed-step.json")["components"]
    cad = {}
    for name, path in paths.items():
        sources[path_key(path)] = digest(path)
        shape = cq.Shape.importBrep(str(path))
        row = records[name]
        assert shape.isValid() and len(shape.Solids()) == row["solids"]
        assert abs(shape.Volume()-row["volume_mm3"]) < .0001
        np.testing.assert_allclose(bounds(shape), row["bounds_mm"], rtol=0, atol=.0001)
        cad[name] = shape

    row = read(GAUGES / "geometry.json")["parts"]["KEY-switch"]
    path = GAUGES / row["file"]
    sources[path_key(path)] = digest(path)
    assert sources[path_key(path)] == row["sha256"]
    mesh = trimesh.load_mesh(path)
    transform = np.eye(4)
    transform[:3] = row["print_to_installed_3x4"]
    mesh.apply_transform(transform)
    np.testing.assert_allclose(mesh.bounds, row["installed_min_max_mm"], atol=.00001)
    # All original gauge STL triangles, remade as planar CAD faces in installed XYZ.
    faces = [cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*p) for p in tri], close=True))
             for tri in mesh.triangles]
    gauge = cq.Solid.makeSolid(cq.Shell.makeShell(faces))
    assert gauge.isValid() and abs(gauge.Volume()-mesh.volume) < .00001
    cad["KEY gauge"] = gauge
    meshes = {k:cad_mesh(s) for k,s in cad.items() if k not in ("Key cap","Retainer","KEY gauge")}
    meshes["KEY gauge"] = mesh
    meshes["Key cap"] = registered_print(R11, "power-cap", sources)
    meshes["Retainer"] = registered_print(R11, "key-board-retainer-west", sources)
    return cad, meshes, sources


def seated_boxes(pieces):
    # Split rim and central button because their widths and heights above the
    # board differ. The source solids and every STL triangle must lie within
    # the union. Each box extends upward through the entire assembly motion.
    boxes = {
        "substrate": box(-41.5,-30.5,27.65,28.65,7.5,17.5),
        "switch case": box(-39.65,-32.35,28.65,32.001,9.5,15.5),
        "stationary rim": box(-39,-33,31.99,32.551,9.5,15.5),
        "actuator": box(-37.75,-34.25,31.99,32.951,10.75,14.25),
    }
    for i, pin in enumerate(pieces["Trimmed terminals"].Solids(), 1):
        for label, lo, hi in (("rear",26.85,27.65),("board",27.65,28.65)):
            clipped = pin.intersect(box(-45,-25,lo,hi,7,20))
            boxes[f"terminal {i} {label}"] = box(*bounds(clipped))
    all_boxes = list(boxes.values())
    envelope = all_boxes[0].fuse(*all_boxes[1:])
    for name, shape in pieces.items():
        assert sum(s.Volume() for s in shape.cut(envelope).Solids()) < CAD_EPS, name
    return boxes


def vertical_boxes(boxes):
    out = {}
    for name, shape in boxes.items():
        b = bounds(shape)
        b[-1] += TRAVEL
        out[name] = box(*b)
    return out


def keeper_sweep(shape):
    # Every nonvertical leading face of this part is planar. Extruding each
    # such face, including its holes, and unioning with the start solid gives
    # the occupied set throughout the vertical translation.
    prisms = []
    for face in shape.Faces():
        if face.geomType() == "CYLINDER":
            axis = BRepAdaptor_Surface(face.wrapped).Cylinder().Axis().Direction()
            assert abs(axis.Z()) > 1-1e-8
        else:
            assert face.geomType() == "PLANE"
            if face.normalAt().z > 1e-8:
                prisms.append(cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(), cq.Vector(0,0,TRAVEL)))
    return shape.fuse(*prisms).clean()


def mesh_sweep(mesh):
    prisms = [solid(mesh)]
    step = np.array([0., 0., TRAVEL])
    for tri, normal in zip(mesh.triangles, mesh.face_normals):
        if normal[2] > 1e-8:
            prisms.append(mf.Manifold.hull_points(np.vstack((tri, tri+step))))
    swept = mf.Manifold.batch_boolean(prisms, mf.OpType.Add)
    assert swept.status() == mf.Error.NoError and not swept.is_empty()
    return swept


def mesh_common(a, b):
    common = a ^ b
    assert common.status() == mf.Error.NoError
    return round(abs(common.volume()), 7)


def oblique_search(meshes, case, cap):
    # Explore the transition while both board edges still engage the shallow
    # rail slots. This numerical search cannot exclude every rigid-body path.
    from scipy.optimize import Bounds
    fixture = (case ^ mf.Manifold.cube([20,12,24]).translate([-46,24,5])) + cap
    center = np.array([-36.,28.15,12.5])
    models = {k:solid(v) for k,v in meshes.items() if k not in ("Key cap","Retainer")}
    real = mf.Manifold.batch_boolean([s for k,s in models.items() if k != "KEY gauge"], mf.OpType.Add)
    out = {}
    for name, assembly in (("KEY gauge",models["KEY gauge"]),("populated PCB",real)):
        local = assembly.translate(-center)
        def objective(q):
            x,y,rx,ry,rz = q
            placed = local.rotate((rx,ry,rz)).translate(center+[x,y,2.])
            return max(0.,(placed ^ fixture).volume())
        result = differential_evolution(objective, Bounds([-.7,-.4,-6,-8,-6],[.7,.4,6,8,6]),
                                        seed=53,popsize=7,maxiter=38,tol=.0005,polish=True)
        out[name] = dict(best_overlap_mm3=round(float(result.fun),6),
                         tested_xy_mm_xyz_degrees=np.round(result.x,6).tolist(), evaluations=result.nfev)
        assert result.fun > .01
    return dict(center_xyz_mm=center.tolist(), fixed_lift_mm=2, offset_xy_limits_mm=[.7,.4],
                rotation_xyz_limits_degrees=[6,8,6], lowest_overlap_found=out,
                scope="Finite numerical search of rigid poses with both board edges engaged. Other trajectories are unverified.")


def run():
    all_cad, meshes, base_sources = all_geometry()
    cap, keeper = all_cad.pop("Key cap"), all_cad.pop("Retainer")
    keeper_path = keeper_sweep(keeper)
    board_sweeps = vertical_boxes(seated_boxes(all_cad))
    mesh_paths = {k:mesh_sweep(v) for k,v in meshes.items() if k != "Key cap"}
    mesh_parts = {k:solid(v) for k,v in meshes.items()}
    mesh_cap = mesh_parts["Key cap"]
    mesh_keeper_path = mesh_paths["Retainer"]
    for number in (13,14,15):
        assembly = MECH / f"TW-A-0001-R{number:04}"
        base = R11 if number == 13 else assembly
        sources = base_sources.copy()
        pose = read(base / "part-orientations.json")["housing-battery-bay"]
        path = base / pose["assembly_brep"]
        sources[path_key(path)] = digest(path)
        case = cq.Shape.importBrep(str(path))
        mesh_case = solid(registered_print(base, "housing-battery-bay", sources))
        assert case.isValid() and abs(case.Volume()-pose["assembly_volume_mm3"]) < .001
        keep = {k:pair(keeper_path,s) for k,s in {"Housing":case,"Key cap":cap,**all_cad}.items()}
        keep_print = {k:mesh_common(mesh_keeper_path,s) for k,s in {"Housing":mesh_case,**mesh_parts}.items()
                      if k != "Retainer"}
        assert max(v["common_mm3"] for v in keep.values()) < CAD_EPS
        assert max(keep_print.values()) < PRINT_EPS
        keep_control = volume(keeper.translate((0,0,-.25)),case)
        assert keep_control > 1
        print_board = {k:dict(housing_mm3=mesh_common(s,mesh_case),cap_mm3=mesh_common(s,mesh_cap))
                       for k,s in mesh_paths.items() if k != "Retainer"}
        controls = {k:pair(all_cad[k].translate((0,0,9)),case) for k in ("KEY gauge","Switch plunger")}
        board_report = dict(
            status="clear" if number == 15 else "blocked",
            removal_offsets_mm=OFFSETS if number == 15 else [],
            installed_to_free_lowest_point_above_case_mm=round(7.5+TRAVEL-bounds(case)[-1],4),
            straight_sweep_print_common_mm3=print_board,
            vertical_offset_9mm_CAD=controls,
            preassembled_undeformed_pin_to_plated_PCB_common_mm3=round(volume(all_cad["Trimmed terminals"],all_cad["Key PCB"]),6))
        cad_pairs = {k:dict(housing=pair(s,case),cap=pair(s,cap)) for k,s in board_sweeps.items()}
        if number == 15:
            assert max(p["common_mm3"] for v in cad_pairs.values() for p in v.values()) < CAD_EPS
            assert max(p for v in print_board.values() for p in v.values()) < PRINT_EPS
            board_report["continuous_CAD_bounds"] = cad_pairs
            board_report["limiting_interfaces"] = "Substrate touches the nominal rail bearing faces. The fixed outer switch rim has at least 0.249 mm to the relieved wall; central actuator to parked cap has at least 0.049 mm."
        else:
            assert controls["KEY gauge"]["common_mm3"] > .54 and controls["Switch plunger"]["common_mm3"] > .094
            assert print_board["KEY gauge"]["housing_mm3"] > .54 and print_board["Switch plunger"]["housing_mm3"] > .094
            board_report["rejected_removal_offsets_mm"] = OFFSETS
            board_report["limiting_interfaces"] = "PCB slots limit inboard shift; stationary switch rim and gauge upper land enter the inner wall at Y32.50. Cap remains parked and clear."
        if number == 14:
            board_report["exploratory_tipped_poses"] = oblique_search(meshes, mesh_case, mesh_cap)
        ex = max(bounds(keeper_path)[1], *(bounds(s)[1] for s in board_sweeps.values()))
        installed = read(R14/"installed-step.json")["components"]
        gauges = read(GAUGES/"geometry.json")["parts"]
        earlier = {k:installed[k]["bounds_mm"][0] for k in ("Rotor","Collar")}
        earlier.update({k:gauges[k]["installed_min_max_mm"][0][0] for k in ("A2-sensor","A3-haptic")})
        earlier["A2 dry shims"] = 41.05
        fixed = {k:round(x-ex,4) for k,x in earlier.items()}
        assert min(fixed.values()) > 30
        report = dict(assembly=assembly.name, sources_sha256=sources,
            frame="Installed XYZ in mm, +Z toward removed display. Reverse offsets for installation. Cap held against outer counterbore shoulder.",
            prerequisites="Open housing. Cap seated first, upright KEY gauge or populated PCB next, west keeper last. M2 screw is absent during installation. Bezel and display are off.",
            other_previously_installed_parts_x_separation_lower_bound_mm=fixed,
            pcb=board_report,keeper=dict(status="clear",removal_offsets_mm=OFFSETS,
                prerequisite="With the board already seated; legacy housing board entry is blocked.",
                free_lowest_point_above_case_mm=round(bounds(keeper)[4]+TRAVEL-bounds(case)[-1],4),
                exact_continuous_CAD=keep, continuous_print_common_mm3=keep_print,
                down_0p25mm_housing_control_mm3=round(keep_control,6)),
            threshold_mm3=dict(CAD=CAD_EPS,registered_print=PRINT_EPS),
            scope="Nominal rigid geometry. CAD uses containment-checked swept boxes for the board and extruded leading faces for the keeper. Print checks sweep original oriented mesh faces, including triangles on the actual board components. Gauge and populated PCB are alternatives. Dry tests omit wire dressing, solder fillets, print tolerances and hand/tool access. Undeformed pin fit in the PCB is a separate existing interference.")
        dest = assembly / "QA/power-key/key-path.json"
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print(assembly.name,board_report["status"],controls,keep["KEY gauge"],flush=True)


if __name__ == "__main__":
    run()
