"""Replace the registered housing and remove the two superseded plate 7 spacers."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree as ET
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
MECH = HERE.parent.parent
PARENT = MECH / "pcb-fit-r0013/Thai-Waters-R0013-PCB-Fit-X1C.3mf"
PARENT_HASH = "e97c448f1dbbbbe49d49afe43a7d4f6c8b63d1ed3aaf768ee8efb73ced1df806"
MESH = HERE.parent / "Print/housing-battery-bay.stl"
PROJECT = HERE / "Thai-Waters-R0014-PCB-Fit-X1C.3mf"
MODEL = "3D/3dmodel.model"
SETTINGS = "Metadata/model_settings.config"
RELATIONSHIPS = "3D/_rels/3dmodel.model.rels"
HOUSING = "3D/Objects/object_1.model"
CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
PROD = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
REMOVED = {"118": "A3 floor spacer 1", "120": "A3 floor spacer 2"}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def value(node, key):
    return node.find(f"metadata[@key='{key}']").attrib["value"]


def encode(node):
    return ET.tostring(node, encoding="UTF-8", xml_declaration=True)


def remove(node):
    node.getparent().remove(node)


def build(stl, output):
    if digest(PARENT) != PARENT_HASH:
        raise ValueError("R0013 project digest mismatch")
    with ZipFile(PARENT) as archive:
        files = {key: archive.read(key) for key in archive.namelist()}
    main, cfg, rels, housing = [ET.fromstring(files[key]) for key in (MODEL, SETTINGS, RELATIONSHIPS, HOUSING)]
    plate = cfg.findall("plate")[6]
    assert value(plate, "plater_id") == "7"
    plate.find("metadata[@key='plater_name']").set("value", "07 PCB fit gauges - R0014")
    for idx, name in REMOVED.items():
        wrapper = main.find(f".//{CORE}object[@id='{idx}']")
        item = main.find(f".//{CORE}item[@objectid='{idx}']")
        part = cfg.find(f"object[@id='{idx}']")
        assert value(part, "name") == name
        target = wrapper.find(f"{CORE}components/{CORE}component").attrib[PROD+"path"]
        del files[target.lstrip("/")]
        relation = rels.find(f"{{*}}Relationship[@Target='{target}']")
        instance, = [r for r in plate.findall("model_instance") if value(r, "object_id") == idx]
        for node in (wrapper, item, part, relation, instance):
            remove(node)

    definition = cfg.find("object[@id='2']")
    info = definition.find("part")
    assert value(info, "source_file") == stl.name
    # Bambu centers the STL on import. Preserve the existing local origin even
    # if a subsequent CAD tessellator changes the outer bounds by a few microns.
    origin = np.array([float(value(info, "source_offset_"+axis)) for axis in "xyz"])
    mesh = trimesh.load_mesh(stl)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
    assert len(mesh.split(only_watertight=False)) == 1
    native = housing.find(f".//{CORE}mesh")
    verts, faces = native.find(CORE+"vertices"), native.find(CORE+"triangles")
    verts.clear()
    faces.clear()
    for x, y, z in mesh.vertices - origin:
        ET.SubElement(verts, CORE+"vertex", x=f"{x:.8f}", y=f"{y:.8f}", z=f"{z:.8f}")
    for a, b, c in mesh.faces:
        ET.SubElement(faces, CORE+"triangle", v1=str(a), v2=str(b), v3=str(c))
    for node in (definition.find("metadata[@face_count]"), info.find("mesh_stat")):
        node.set("face_count", str(len(mesh.faces)))
    for key, root in ((MODEL,main), (SETTINGS,cfg), (RELATIONSHIPS,rels), (HOUSING,housing)):
        files[key] = encode(root)
    output.parent.mkdir(exist_ok=True, parents=True)
    with ZipFile(output, "w") as archive:
        for key, data in sorted(files.items()):
            archive.writestr(ZipInfo(key, (2026,11,23,0,0,0)), data, compress_type=ZIP_DEFLATED)
    print(output, digest(output))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", type=Path, default=MESH)
    parser.add_argument("--output", type=Path, default=PROJECT)
    args = parser.parse_args()
    build(args.mesh, args.output)
