"""Replace just the R0015 plate-1 housing in the editable X1C project and slice locally."""
import argparse
from copy import deepcopy
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree as ET
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PREV = HERE.parent.with_name("TW-A-0001-R0015") / "Printing"
sys.path.insert(0, str(HERE.parent.with_name("TW-A-0001-R0014") / "Printing"))
from make_project import CORE, HOUSING, MODEL, PROD, SETTINGS, digest, encode, value

PARENT = PREV / "Thai-Waters-R0015-PCB-Fit-X1C.3mf"
PROJECT = HERE / "Thai-Waters-R0016-PCB-Fit-X1C.3mf"
STL = HERE.parent / "Print/housing-battery-bay.stl"
BASELINE_HASH = "c98ef59656fcfca2e18dfe6434898e9352af7256d4c4ce2c88b64b31dde26d83"


BLOCKER_ID = "301"
BLOCKER_LOW = np.array([-44.2, -18.2, 11.55])
BLOCKER_HIGH = np.array([-39.4, 3.3, 23.0])
LAYER_CONFIG = "Metadata/layer_config_ranges.xml"


def build(output=PROJECT, *, automatic_only=False):
    assert digest(PARENT) == BASELINE_HASH
    mesh = trimesh.load_mesh(STL)
    assert mesh.is_volume
    with ZipFile(PARENT) as archive:
        files = {k: archive.read(k) for k in archive.namelist()}
    housing = ET.fromstring(files[HOUSING])
    cfg = ET.fromstring(files[SETTINGS])
    definition = cfg.find("object[@id='2']")
    part = definition.find("part")
    assert value(part, "source_file") == STL.name
    offset = np.array([float(value(part, "source_offset_" + k)) for k in "xyz"])
    container = housing.find(f".//{CORE}mesh")
    verts, faces = container.find(CORE+"vertices"), container.find(CORE+"triangles")
    verts.clear()
    faces.clear()
    for x, y, z in mesh.vertices - offset:
        ET.SubElement(verts, CORE+"vertex", x=f"{x:.8f}", y=f"{y:.8f}", z=f"{z:.8f}")
    for a, b, c in mesh.faces:
        ET.SubElement(faces, CORE+"triangle", v1=str(a), v2=str(b), v3=str(c))
    for node in (definition.find("metadata[@face_count]"), part.find("mesh_stat")):
        node.set("face_count", str(len(mesh.faces)))
    if not automatic_only:
        # A negative support volume leaves auto supports elsewhere, including
        # beneath the existing projecting USB ledge. Coordinates are installed.
        root_model = ET.fromstring(files[MODEL])
        components = root_model.find(f".//{CORE}object[@id='2']/{CORE}components")
        component = deepcopy(components[0])
        component.set("objectid", BLOCKER_ID)
        component.set(PROD + "UUID", "013d0000-b206-40ff-9872-83e8017abed1")
        components.append(component)
        resource = housing.find(CORE + "resources")
        obj = ET.SubElement(resource, CORE+"object", id=BLOCKER_ID, type="model")
        obj.set(PROD+"UUID", "013d0000-81cb-4c03-9d28-80fed5dfa1dc")
        local = ET.SubElement(obj, CORE+"mesh")
        v, f = ET.SubElement(local, CORE+"vertices"), ET.SubElement(local, CORE+"triangles")
        block = trimesh.creation.box(extents=BLOCKER_HIGH-BLOCKER_LOW)
        mid = (BLOCKER_LOW + BLOCKER_HIGH)/2 + [0,0,3.200001004]
        for x,y,z in block.vertices + mid - offset:
            ET.SubElement(v, CORE+"vertex", x=f"{x:.8f}", y=f"{y:.8f}", z=f"{z:.8f}")
        for a,b,c in block.faces:
            ET.SubElement(f, CORE+"triangle", v1=str(a), v2=str(b), v3=str(c))
        metadata = ET.SubElement(definition, "part", id=BLOCKER_ID, subtype="support_blocker",
                                 uuid="79e8b0a7-3176-49ed-960e-adbbcd674951")
        ET.SubElement(metadata, "metadata", key="name", value="USB1 service-edge entry support blocker")
        metadata.append(deepcopy(part.find("metadata[@key='matrix']")))
        files[MODEL] = encode(root_model)
        # Housing is the first object in the saved build. Use fine layers only
        # around the bearing so the 0.20 mm profile does not round it up 0.10 mm.
        assert root_model.find(f".//{CORE}build/{CORE}item").get("objectid") == "2"
        ranges = ET.Element("objects")
        r = ET.SubElement(ET.SubElement(ranges, "object", id="1"), "range", min_z="14.4", max_z="15.0")
        ET.SubElement(r, "option", opt_key="layer_height").text = "0.10"
        files[LAYER_CONFIG] = encode(ranges)
    files[HOUSING], files[SETTINGS] = encode(housing), encode(cfg)
    with ZipFile(output, "w") as out:
        for key, data in sorted(files.items()):
            out.writestr(ZipInfo(key,(2026,11,23,0,0,0)), data, compress_type=ZIP_DEFLATED)
    print("Wrote", output, digest(output), flush=True)


def slice_local(slicer, scratch):
    for name, index in (("all",0),("reopen",1)):
        folder = (scratch/name).resolve()
        folder.mkdir(parents=True, exist_ok=False)
        with (folder/"native.log").open("wb") as log:
            subprocess.run([str(slicer.resolve()), "--slice", str(index), "--outputdir", str(folder),
                            "--export-3mf", "sliced.3mf", str(PROJECT)], check=True, cwd=folder,
                           stdout=log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        print("Sliced", name, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slicer", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--automatic-only-control", type=Path,
                        help="Also save the final mesh with the parent automatic supports to this file.")
    args = parser.parse_args()
    build()
    if args.automatic_only_control:
        build(args.automatic_only_control, automatic_only=True)
    if args.slicer:
        if args.scratch is None:
            parser.error("--slicer requires --scratch")
        slice_local(args.slicer, args.scratch)
