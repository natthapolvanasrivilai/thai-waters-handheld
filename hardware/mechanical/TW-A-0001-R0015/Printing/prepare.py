"""Replace just the R0014 plate-1 housing in the editable X1C project and slice locally."""
import argparse
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree as ET
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PREV = HERE.parent.with_name("TW-A-0001-R0014") / "Printing"
sys.path.insert(0, str(PREV))
from make_project import CORE, HOUSING, SETTINGS, digest, encode, value

PARENT = PREV / "Thai-Waters-R0014-PCB-Fit-X1C.3mf"
PROJECT = HERE / "Thai-Waters-R0015-PCB-Fit-X1C.3mf"
STL = HERE.parent / "Print/housing-battery-bay.stl"
BASELINE_HASH = "b8cfc8f26e83b67a921a41a9f0a6d779213486098d7de82f9b7936236d67407f"


def build():
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
    files[HOUSING], files[SETTINGS] = encode(housing), encode(cfg)
    with ZipFile(PROJECT, "w") as out:
        for key, data in sorted(files.items()):
            out.writestr(ZipInfo(key,(2026,11,23,0,0,0)), data, compress_type=ZIP_DEFLATED)
    print("Wrote", PROJECT, digest(PROJECT), flush=True)


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
    args = parser.parse_args()
    build()
    if args.slicer:
        if args.scratch is None:
            parser.error("--slicer requires --scratch")
        slice_local(args.slicer, args.scratch)
