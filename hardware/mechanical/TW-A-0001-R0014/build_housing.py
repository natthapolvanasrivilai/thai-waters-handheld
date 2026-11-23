"""Replace the two installed A3 foam footprints with grooved, integral PETG rails."""
import hashlib
import json
import sys
from pathlib import Path

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
BASE = HERE.with_name("TW-A-0001-R0011")
OLD = HERE.with_name("TW-A-0001-R0013")
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / ".agents/skills/thai-waters-hardware-verification"))
from flat_exterior import audit

NAME = "housing-battery-bay"
PART = "TW-P-0001-R0011"
CENTERS = (18.0, 26.0)
FLOOR = 2.5
TOP = 4.6
RELIEF = 4.2


def read(path):
    return json.loads(path.read_bytes())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest(path):
    with path.open("rb") as src:
        return hashlib.file_digest(src, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(src.read()).hexdigest()


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def rail(x, bottom=FLOOR):
    outer = box(x-1.5, -12, bottom, 3, 12, TOP-bottom)
    groove = box(x-.6, -8, RELIEF, 1.2, 8.1, .5)
    return outer.cut(groove).clean()


def manifold(mesh):
    value = mf.Manifold(mf.Mesh64(np.ascontiguousarray(mesh.vertices),
                                 np.ascontiguousarray(mesh.faces, dtype=np.uint64)))
    assert value.status() == mf.Error.NoError and not value.is_empty()
    return value


def build():
    prior = read(BASE / "part-orientations.json")[NAME]
    base_path = BASE / prior["assembly_brep"]
    previous_stl = BASE / prior["print_stl"]
    assert digest(previous_stl) == prior["sha256"]
    h = cq.Shape.importBrep(str(base_path))
    regions = HERE / "floor-regions.json"
    region_list = read(regions)["regions"]
    before = audit(h, region_list)
    assert before["pass"]
    foam_path = ROOT / "hardware/electronics/haptic-r0009/placed/adhH.brep"
    foam = cq.Shape.importBrep(str(foam_path))
    pads = sorted(foam.Solids(), key=lambda s:s.Center().x)
    assert len(pads) == len(CENTERS)
    for x, pad in zip(CENTERS, pads):
        expected = box(x-1.5, -12, FLOOR, 3, 12, TOP-FLOOR)
        assert abs(pad.intersect(expected).Volume()-75.6) < 1e-5
        assert abs(pad.Volume()-75.6) < 1e-5
    nominal = [rail(x) for x in CENTERS]
    # Penetrate the existing floor by 50 microns while fusing. The portion
    # below the inside floor is already solid and adds zero net material.
    fused = h.fuse(*[rail(x, FLOOR-.05) for x in CENTERS]).clean()
    increase = fused.Volume()-h.Volume()
    assert fused.isValid() and len(fused.Solids()) == 1
    assert abs(increase-sum(r.Volume() for r in nominal)) < .0001
    brep = HERE / "CAD" / (NAME+".brep")
    step = brep.with_suffix(".step")
    fused.exportBrep(str(brep))
    cq.exporters.export(fused, str(step))
    # Preserve the production tessellation everywhere outside the change.
    original = trimesh.load_mesh(previous_stl)
    meshbase = manifold(original)
    delta = prior["assembly_to_print"][2][3]
    mesh = meshbase
    for x in CENTERS:
        core = mf.Manifold.cube((3,12,TOP-FLOOR+.05)).translate((x-1.5,-12,FLOOR-.05+delta))
        groove = mf.Manifold.cube((1.2,8.1,.5)).translate((x-.6,-8,RELIEF+delta))
        mesh = mesh + (core - groove)
    assert mesh.status() == mf.Error.NoError and len(mesh.decompose()) == 1
    raw = mesh.to_mesh64()
    model = trimesh.Trimesh(vertices=raw.vert_properties[:,:3], faces=raw.tri_verts, process=False)
    stl = HERE / "Print" / (NAME+".stl")
    model.export(stl)
    returned = trimesh.load_mesh(stl)
    actual = manifold(returned)
    assert returned.is_watertight and returned.is_winding_consistent and len(actual.decompose()) == 1
    assert np.max(abs(returned.bounds - original.bounds)) < .00001
    assert abs(actual.volume()-meshbase.volume()-increase) < .001
    metadata = {**prior, "part_revision":PART, "assembly_brep": "CAD/"+brep.name,
                "original_stl":"../"+BASE.name+"/Print/"+stl.name, "print_stl":"Print/"+stl.name,
                "sha256":digest(stl), "assembly_volume_mm3":round(fused.Volume(),5)}
    save(HERE/"part-orientations.json", {NAME:metadata})
    print("PRINT READY", stl, digest(stl), flush=True)
    returned_solid = cq.importers.importStep(str(step)).val()
    after = audit(returned_solid, region_list)
    assert after["pass"]
    additions = returned_solid.cut(h)
    removed = h.cut(returned_solid)
    rails = cq.Compound.makeCompound(nominal)
    addition_outside = additions.cut(rails).Volume()
    assert abs(removed.Volume()) < .0001 and abs(addition_outside) < .0001
    assert abs(rails.cut(additions).Volume()) < .0001
    assert len(returned_solid.Solids()) == 1 and returned_solid.isValid()
    save(HERE/"QA/housing-geometry.json", dict(
        parent_brep_sha256=digest(base_path),previous_stl_sha256=digest(previous_stl),
        removed_foam_brep_sha256=digest(foam_path), housing_step_sha256=digest(step),
        housing_brep_sha256=digest(brep),print_stl_sha256=digest(stl),witness_sha256=digest(regions),
        step_valid_single_solid=True, print_watertight_single_component=True, units="mm",
        installed_centers_xy=[[x,-6] for x in CENTERS], rail_envelope_mm=[3,12,2.1],
        visible_rail_z_mm=[FLOOR,TOP], groove_width_length_depth_mm=[1.2,8,.4],
        groove_open_direction="+Y", added_PETG_mm3=round(increase,6),
        real_foam_replaced_mm3=round(foam.Volume(),6), gross_foot_area_each_mm2=36,
        hard_bearing_top_area_each_mm2=26.4, groove_capacity_each_mm3=3.84,
        global_original_material_removed_mm3=round(removed.Volume(),6),
        global_added_material_outside_two_interior_rails_mm3=round(addition_outside,6),
        print_volume_increase_mm3=round(actual.volume()-meshbase.volume(),6),
        baseline_exterior=before, released_exterior=after))


if __name__ == "__main__":
    build()
