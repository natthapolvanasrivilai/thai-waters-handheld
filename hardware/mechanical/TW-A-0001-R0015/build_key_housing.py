"""Relieve the inboard wall for the upright KEY board while preserving the flange shoulder."""
import sys
from pathlib import Path

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.with_name("TW-A-0001-R0014")
sys.path.insert(0, str(PREVIOUS))
from build_housing import audit, box, digest, manifold, read, save

NAME = "housing-battery-bay"
PART = "TW-P-0001-R0012"
# Installed coordinates. The rear wall begins at Y32.50, the counterbore
# shoulder is Y33.55 and the exterior face is Y34.50. The box ends at Y32.80.
LOW = np.array([-39.30, 32.30, 9.25])
HIGH = np.array([-32.70, 32.80, 28.20])


def run():
    row = read(PREVIOUS / "part-orientations.json")[NAME]
    previous_shape = PREVIOUS / row["assembly_brep"]
    previous_mesh = PREVIOUS / row["print_stl"]
    assert digest(previous_shape) == read(PREVIOUS / "installed-step.json")["components"]["Housing"]["source_sha256"]
    assert digest(previous_mesh) == row["sha256"]
    source = cq.Shape.importBrep(str(previous_shape))
    cutter = box(*LOW, *(HIGH - LOW))
    removed = source.intersect(cutter)
    new = source.cut(cutter).clean()
    assert new.isValid() and len(new.Solids()) == 1 and removed.Volume() > 0
    brep = HERE / "CAD" / (NAME + ".brep")
    step = brep.with_suffix(".step")
    new.exportBrep(str(brep))
    cq.exporters.export(new, str(step))
    # Subtract the same analytic rectangular relief from the original print
    # mesh in its registered print orientation. All other triangles retain
    # the original tessellation, including the A3 rails and receiver soles.
    pose = np.array(row["assembly_to_print"])
    mesh = trimesh.load_mesh(previous_mesh)
    parent_mesh = manifold(mesh)
    mesh_cutter = mf.Manifold.cube(HIGH - LOW).translate(LOW).transform(pose[:3])
    result = parent_mesh - mesh_cutter
    assert result.status() == mf.Error.NoError and len(result.decompose()) == 1
    raw = result.to_mesh64()
    stl = HERE / "Print" / (NAME + ".stl")
    trimesh.Trimesh(raw.vert_properties[:, :3], raw.tri_verts, process=False).export(stl)
    reloaded = trimesh.load_mesh(stl)
    print_shape = manifold(reloaded)
    assert reloaded.is_volume and len(print_shape.decompose()) == 1
    np.testing.assert_allclose(mesh.bounds, reloaded.bounds, rtol=0, atol=.00002)
    removed_print = parent_mesh.volume() - print_shape.volume()
    assert abs(removed_print - removed.Volume()) < .04
    save(HERE / "part-orientations.json", {NAME: {**row, "part_revision":PART,
        "original_stl":"../" + PREVIOUS.name + "/" + row["print_stl"],
        "assembly_volume_mm3":round(new.Volume(), 5), "sha256":digest(stl)}})
    print("CANDIDATE GEOMETRY AVAILABLE", flush=True)
    reopened = cq.importers.importStep(str(step)).val()
    added = abs(reopened.cut(source).Volume())
    wrong_removal = abs(source.cut(reopened).cut(cutter).Volume())
    assert reopened.isValid() and len(reopened.Solids()) == 1
    assert max(added, wrong_removal, abs(source.Volume() - reopened.Volume() - removed.Volume())) < .0001
    # This cut is entirely inboard of the external face and shoulder. Validate
    # the complete stepped hole and shoulder from the inner end of the retained
    # counterbore through the outside surface, without masking the opening.
    preserve = box(-41, 32.801, 7.5, 10, 2.0, 10)
    prior_capture, capture = source.intersect(preserve), reopened.intersect(preserve)
    unchanged = abs(prior_capture.cut(capture).Volume()) + abs(capture.cut(prior_capture).Volume())
    assert unchanged < .0001
    regions = PREVIOUS / "floor-regions.json"
    exterior = audit(reopened, read(regions)["regions"])
    assert exterior["pass"]
    save(HERE / "QA/housing-geometry.json", dict(
        assembly=HERE.name, housing_part=PART, parent_assembly=PREVIOUS.name,
        parent_brep_sha256=digest(previous_shape), parent_print_sha256=digest(previous_mesh),
        housing_brep_sha256=digest(brep), housing_step_sha256=digest(step), print_stl_sha256=digest(stl),
        relief_box_installed_xyz_mm=[LOW.tolist(), HIGH.tolist()], units="mm",
        removed_material_mm3=round(removed.Volume(), 6), print_volume_removed_mm3=round(removed_print, 6),
        step_valid_single_solid=True, mesh_watertight_single_solid=True, original_bounds_preserved=True,
        global_new_material_mm3=round(added, 8), global_removal_outside_stated_box_mm3=round(wrong_removal, 8),
        protected_bore_window_mm=[[-41,32.801,7.5],[-31,34.801,17.5]],
        protected_outer_bore_and_capture_shoulder_symmetric_difference_mm3=round(unchanged,8),
        nominal_distance_from_relief_plane_to_outer_face_mm=1.70,
        retained_axial_counterbore_depth_from_relief_plane_to_shoulder_mm=.75,
        floor_regions_sha256=digest(regions), exterior=exterior,
        scope="Open-housing key insertion. Exterior floor check inherited from R0014; global solid subtraction establishes that every change lies in the specified inside wall box."))


if __name__ == "__main__":
    run()
