"""Machine the USB lamp's end-loading slot in the parent geometry, then check the print mesh and enclosed USB well."""
from pathlib import Path
import sys

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PREV = HERE.with_name("TW-A-0001-R0015")
BASE = HERE.with_name("TW-A-0001-R0014")
sys.path.insert(0, str(BASE))
from build_housing import box, audit, digest, manifold, read, save

NAME = "housing-battery-bay"
PART = "TW-P-0001-R0013"
# Opposite (-Y) mouth below the USB well. Clear the LED projection through the
# approach. Limit the relief over the board to preserve stock below the socket.
CUTS = [
    ((-42.56,-17.75,11.38),(-41.26,2.405,14.85)),
    ((-41.53,-3.10,11.38),(-40.30,-2.23,14.85)),
]
# Widen the supported floor beneath the inboard lip, set the final PCB datum,
# then add the guide lip below the axial wire exits. The far wall stops +Y travel.
ADDS = [
    # Close the top of the obsolete Z-loading slot below the USB throat.
    ((-42.31,-2.65,14.85),(-41.28,2.65,15.43)),
    ((-42.16,-2.91,10.84),(-40.37,2.91,11.44)),
    ((-42.16,-2.48,11.37),(-41.27,2.46,11.50)),
    ((-41.27,-2.90,11.38),(-40.38,2.90,12.25)),
    ((-42.15,2.40,11.38),(-41.43,2.65,14.70)),
]


def bounds_box(region):
    a,b = map(np.array, region)
    return box(*a, *(b-a))


def mesh_box(region, pose):
    a,b = map(np.array, region)
    return mf.Manifold.cube(b-a).translate(a).transform(pose[:3])


def run():
    for folder in ("CAD","Print","QA"):
        (HERE/folder).mkdir(exist_ok=True)
    row = read(PREV/"part-orientations.json")[NAME]
    src = PREV/row["assembly_brep"]
    raw = PREV/row["print_stl"]
    assert digest(src) == read(PREV/"installed-step.json")["components"]["Housing"]["source_sha256"]
    assert digest(raw) == row["sha256"]
    parent = cq.Shape.importBrep(str(src))
    new = parent
    pose = np.array(row["assembly_to_print"])
    mesh = trimesh.load_mesh(raw)
    solid = manifold(mesh)
    for region in CUTS:
        new = new.cut(bounds_box(region))
        solid = solid - mesh_box(region,pose)
    for region in ADDS:
        new = new.fuse(bounds_box(region))
        solid = solid + mesh_box(region,pose)
    new = new.clean()
    assert new.isValid() and len(new.Solids()) == 1 and len(solid.decompose()) == 1
    brep = HERE/row["assembly_brep"]
    step = brep.with_suffix(".step")
    new.exportBrep(str(brep))
    cq.exporters.export(new,str(step))
    result = solid.to_mesh64()
    stl = HERE/row["print_stl"]
    trimesh.Trimesh(result.vert_properties[:,:3],result.tri_verts,process=False).export(stl)
    loaded = trimesh.load_mesh(stl)
    assert loaded.is_volume and len(manifold(loaded).decompose()) == 1
    np.testing.assert_allclose(loaded.bounds,mesh.bounds,atol=.00002,rtol=0)
    assert abs((loaded.volume-mesh.volume)-(new.Volume()-parent.Volume())) < .05
    save(HERE/"part-orientations.json",{NAME:{**row,"part_revision":PART,"original_stl":"../"+PREV.name+"/"+row["print_stl"],"assembly_volume_mm3":round(new.Volume(),5),"sha256":digest(stl)}})
    print("Exported candidate",digest(stl),flush=True)
    restored = cq.importers.importStep(str(step)).val()
    add = restored.cut(parent)
    remove = parent.cut(restored)
    assert abs(restored.Volume()-new.Volume()) < .0001 and restored.isValid()
    for change,regions in ((add,ADDS),(remove,CUTS)):
        outside = change
        for region in regions:
            outside = outside.cut(bounds_box(region))
        assert abs(outside.Volume()) < .0001
    # The bridge under the flat part of the USB well must still have continuous
    # material through three 0.20 mm layer heights at the central slot.
    roof = box(-42.45,-2.4,14.8501,1.0,4.8,.5998)
    assert roof.cut(restored).Volume() < .0001
    floor = audit(restored,read(BASE/"floor-regions.json")["regions"])
    assert floor["pass"]
    save(HERE/"QA/housing-geometry.json",dict(assembly=HERE.name,housing_part=PART,
        parent_brep_sha256=digest(src),parent_print_sha256=digest(raw),housing_brep_sha256=digest(brep),
        housing_step_sha256=digest(step),print_stl_sha256=digest(stl),cuts_xyz_mm=CUTS,additions_xyz_mm=ADDS,
        removed_mm3=round(remove.Volume(),6),added_mm3=round(add.Volume(),6),change_outside_defined_regions_mm3=0,
        sealed_central_throat_floor_witness_mm=.5998,pcb_floor_datum_mm=11.50,far_board_stop_y_mm=2.40,
        inboard_lip_width_mm=.89,inboard_lip_top_mm=12.25,exterior_checks=floor,
        scope="Nominal housing and reopened print. Sideways withdrawal and as-printed retention require physical qualification."))


if __name__ == "__main__":
    run()
