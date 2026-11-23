"""Append the PCB fit gauges to the verified six-plate Bambu X1C enclosure project."""
import argparse
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import re
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree as ET
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
BASE_SHA = "510fe8e2f1930c18298fb90d9a3b1edf74ac57c71bcb89fc985bed1fc49af50f"
PROJECT = "Thai-Waters-R0013-PCB-Fit-X1C.3mf"
# Coordinates are bounding-box centers in the local coordinate system of plate 7.
GAUGES = [
    ("A1-display", "A1 display and controller", 83, 150),
    ("A2-sensor", "A2 reel sensor", 164, 166),
    ("A3-haptic", "A3 haptic board", 205, 166),
    ("A4-integration", "A4 integration board", 164, 128),
    ("A5-power", "A5 USB power board", 205, 128),
    ("KEY-switch", "Top power switch board", 135, 95),
    ("USB-PCB1", "USB indicator LED board", 165, 95),
    ("USB-PCB2", "USB lamp resistor board", 194, 95),
]
SPACERS = [
    ("A3-floor-shim", f"A3 floor spacer {i+1}", x, 68) for i,x in enumerate((65,78))
] + [
    ("A4-display-shim", f"A4 display spacer {i+1}", x, 68) for i,x in enumerate((107,118,129))
] + [
    ("A5-display-shim", f"A5 display spacer {i+1}", x, 68) for i,x in enumerate((158,169,180))
]
C = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
P = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
MODEL = "3D/3dmodel.model"
CONFIG = "Metadata/model_settings.config"
RELS = "3D/_rels/3dmodel.model.rels"


def uid(name):
    return str(uuid5(NAMESPACE_URL, "thai-waters/pcb-fit-r0013/" + name))


def xml(node):
    return ET.tostring(node, encoding="UTF-8", xml_declaration=True)


def put(node, key, value):
    ET.SubElement(node, "metadata", key=key, value=str(value))


def make(baseline, mesh_dir, output):
    if sha256(baseline.read_bytes()).hexdigest() != BASE_SHA:
        raise ValueError("Expected the released six-plate X1C enclosure project")
    # Keep all source model payloads and their native settings. Strip old slicer
    # products: this editable project should be sliced with its seven-plate layout.
    with ZipFile(baseline) as source:
        files = {k: source.read(k) for k in source.namelist()
                 if not re.match(r"Metadata/(plate_\d+\.|_rels/model_settings|slice_info|filament_sequence)", k)}
    profile_file="Metadata/project_settings.config"
    profile=json.loads(files[profile_file])
    # The parent declares three materials but only one swatch. Bambu then
    # silently stops after layer one on the two plates using slots 2 and 3.
    assert profile["filament_colour"]==["#00AE42"]
    profile["filament_colour"]+=["#E0F1F5","#14161A"]
    files[profile_file]=json.dumps(profile,ensure_ascii=False,indent=4).encode()
    main, cfg, rels = [ET.fromstring(files[k]) for k in (MODEL, CONFIG, RELS)]
    build = main.find(C+"build")
    parts = main.find(C+"resources")
    assert len(cfg.findall("plate")) == 6 and len(build) == 19
    for prop in cfg.findall("plate/metadata[@key='gcode_file']"):
        prop.getparent().remove(prop)
    plate = deepcopy(cfg.findall("plate")[-1])
    for instance in plate.findall("model_instance"):
        plate.remove(instance)
    plate.find("metadata[@key='plater_id']").set("value","7")
    plate.find("metadata[@key='plater_name']").set("value","07 PCB fit gauges - R0013")
    plate.find("metadata[@key='bed_type']").set("value","Engineering Plate")
    cfg.findall("plate")[-1].addnext(plate)
    for i,(stem,name,cx,cy) in enumerate(GAUGES+SPACERS):
        m = trimesh.load_mesh(mesh_dir/(stem+".stl"))
        if not m.is_volume or len(m.split(only_watertight=False)) != 1:
            raise ValueError(f"{name}: expected one watertight body")
        lo,hi=m.bounds
        if abs(lo[2])>.01:
            raise ValueError(f"{name}: gauge lacks a bed datum")
        mid=(lo+hi)/2
        m.apply_translation(-mid)
        pid,oid=str(101+2*i),str(102+2*i)
        resource=f"3D/Objects/gauge_{oid}.model"
        local=ET.Element(C+"model",nsmap=main.nsmap,unit="millimeter")
        local_obj=ET.SubElement(ET.SubElement(local,C+"resources"),C+"object",id=pid,type="model")
        local_obj.set(P+"UUID",uid(name+"/mesh"))
        mesh=ET.SubElement(local_obj,C+"mesh")
        verts=ET.SubElement(mesh,C+"vertices")
        for x,y,z in m.vertices:
            ET.SubElement(verts,C+"vertex",x=f"{x:.8f}",y=f"{y:.8f}",z=f"{z:.8f}")
        tris=ET.SubElement(mesh,C+"triangles")
        for a,b,c in m.faces:
            ET.SubElement(tris,C+"triangle",v1=str(a),v2=str(b),v3=str(c))
        files[resource]=xml(local)
        ET.SubElement(rels,REL+"Relationship",Target="/"+resource,Id=f"gauge-{i+1}",Type=rels[0].get("Type"))
        wrapper=ET.SubElement(parts,C+"object",id=oid,type="model")
        wrapper.set(P+"UUID",uid(name+"/wrapper"))
        comp=ET.SubElement(ET.SubElement(wrapper,C+"components"),C+"component",objectid=pid)
        comp.set(P+"path","/"+resource)
        comp.set(P+"UUID",uid(name+"/component"))
        origin_y=cy-2*307.2
        placement=f"1 0 0 0 1 0 0 0 1 {cx} {origin_y:.4f} {mid[2]:.8f}"
        item=ET.SubElement(build,C+"item",objectid=oid,transform=placement,printable="1")
        item.set(P+"UUID",uid(name+"/instance"))
        definition=ET.Element("object",id=oid)
        cfg.find("plate").addprevious(definition)
        for key,value in {"name":name,"extruder":"1","enable_support":"0","brim_type":"no_brim",
                          "wall_generator":"arachne","wall_loops":"3"}.items():
            put(definition,key,value)
        part=ET.SubElement(definition,"part",id=pid,subtype="normal_part",uuid=uid(name+"/part"))
        put(part,"name",name)
        put(part,"matrix",f"1 0 0 {cx} 0 1 0 {cy} 0 0 1 {mid[2]:.8f} 0 0 0 1")
        ET.SubElement(part,"mesh_stat",face_count=str(len(m.faces)),edges_fixed="0",degenerate_facets="0",
                      facets_removed="0",facets_reversed="0",backwards_edges="0")
        row=ET.SubElement(plate,"model_instance")
        for key,value in {"object_id":oid,"instance_id":"0","identify_id":str(1701+i)}.items():
            put(row,key,value)
    files.update({MODEL:xml(main),CONFIG:xml(cfg),RELS:xml(rels)})
    output.parent.mkdir(exist_ok=True,parents=True)
    with ZipFile(output,"w") as z:
        for k,data in sorted(files.items()):
            z.writestr(ZipInfo(k,(2026,11,23,0,0,0)),data,compress_type=ZIP_DEFLATED)
    print(output,sha256(output.read_bytes()).hexdigest())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("enclosure",type=Path)
    parser.add_argument("--mesh-dir",type=Path,default=HERE/"meshes")
    parser.add_argument("--out",type=Path,default=HERE/PROJECT)
    args=parser.parse_args()
    make(args.enclosure,args.mesh_dir,args.out)
