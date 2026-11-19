"""Build the removable service cover in its print and installed datums."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.with_name("TW-A-0001-R0009")
STEM = "service-cover"
CENTER_X = -17.0
CENTER_Z = 20.5
OUTER_FACE_Y = -35.7
PART = "TW-P-0027-R0001"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_solid():
    # The print face is z=0. Wall entry and exit are z=1.20 and 3.20.
    face = (cq.Workplane("XY").box(28.8, 8.8, 1.2, centered=(True, True, False))
            .edges("|Z").fillet(1.15).edges("<Z").chamfer(0.28))
    # A thumbnail relief under the left lip ends 0.60 mm outside the opening.
    relief = (cq.Workplane("XY").workplane(offset=0.72).center(-14.8, 0)
              .ellipse(1.20, 1.85).extrude(1.0))
    face = face.cut(relief)
    # The paired stops control lateral travel while allowing the hooks to flex.
    for end in (-1, 1):
        stop = (cq.Workplane("XY").box(0.9, 3.6, 1.65, centered=(True, True, False))
                .edges(">Z").chamfer(0.22).translate((12.3 * end, 0, 1.2)))
        face = face.union(stop)
    # Each hook is a separate free tongue. The two ramps permit installation
    # and progressive removal by peeling from the relieved end.
    profile = [(1.90, 1.20), (2.74, 1.20), (2.74, 3.12),
               (3.40, 3.78), (3.40, 3.98), (2.76, 4.52), (1.90, 4.52)]
    for x_start in (-10.5, 5.5):
        for side in (-1, 1):
            tongue = (cq.Workplane("YZ", origin=(x_start, 0, 0))
                      .polyline([(side * v, h) for v, h in profile])
                      .close().extrude(5.0))
            face = face.union(tongue)
    part = face.val().clean()
    assert part.isValid() and len(part.Solids()) == 1
    return part


def installed(print_part):
    return print_part.rotate((0, 0, 0), (1, 0, 0), -90).translate((CENTER_X, OUTER_FACE_Y, CENTER_Z))


def main(work):
    sys.path.insert(0, str(BASE))
    from package import shape_mesh
    work.mkdir(parents=True, exist_ok=True)
    for folder in ("Print", "CAD"):
        (HERE / folder).mkdir(exist_ok=True)
    print_part = print_solid()
    cover = installed(print_part)
    stl = HERE / "Print" / (STEM + ".stl")
    brep = HERE / "CAD" / (STEM + ".brep")
    cq.exporters.export(print_part, str(stl), tolerance=.012, angularTolerance=.065)
    cover.exportBrep(str(brep))
    meta = json.loads((BASE / "part-orientations.json").read_text())
    for r in meta.values():
        for field in ("assembly_brep", "print_stl"):
            r[field] = "../" + BASE.name + "/" + r[field]
    meta[STEM] = dict(viewer_id="serviceCover", coordinate_frame="assembly",
                      assembly_brep="CAD/service-cover.brep", print_stl="Print/service-cover.stl",
                      assembly_to_print=[[1,0,0,17], [0,0,-1,20.5], [0,1,0,35.7], [0,0,0,1]],
                      build_up_assembly=[0,1,0], bed_face="Flat outer face",
                      brim="None", material="Opaque TPU 95A, case colour",
                      assembly_volume_mm3=round(cover.Volume(), 4),
                      extents_mm=[28.8,8.8,4.52], sha256=digest(stl))
    write_json(HERE / "part-orientations.json", meta)
    row = dict(id="serviceCover", name="Lower service key cover", ref="P17",
               group="Enclosure", kind="R0010 manufactured CAD", stage=7, delta=[0,-23,0],
               note="Opaque TPU cover. Peel the short west edge to reach the recessed PWR, RESET and BOOT switches.",
               color="#91a994", finish="rubber", source="hardware/mechanical/"+HERE.name+"/CAD/service-cover.brep",
               option="", added=True, productEligible=True, geometrySha256=digest(brep))
    row.update(shape_mesh(cover))
    write_json(work / "viewer-rows.json", [row])
    manifest = json.loads((BASE / "assembly-parts.json").read_text(encoding="utf-8"))
    manifest.append({k:v for k,v in row.items() if k not in ("v","t","c")})
    write_json(HERE / "assembly-parts.json", manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    main(parser.parse_args().work)

