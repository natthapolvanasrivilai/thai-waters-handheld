"""Build the current seven-plate X1C verification project, preserving native placements."""
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import hashlib
import sys
import json
import numpy as np
import trimesh
from lxml import etree as E
from rotor import HERE,MECH

sys.path.insert(0,str(MECH.parents[0]/"electronics/case-board-r0001"))
from print_fit import replace_mesh
from make_project import MODEL,SETTINGS,RELATIONSHIPS,CORE,PROD,value,encode

PROJECT=HERE/"Thai-Waters-DFM-R0001-X1C.3mf"
BASE=MECH/"TW-A-0001-R0016/Printing/Thai-Waters-R0016-PCB-Fit-X1C.3mf"
CAP=MECH/"TW-A-0001-R0017/Print/R0017-keyed-power-cap-X1C.3mf"
KIT=MECH.parent/"electronics/case-board-r0001/Case-board-R0001-X1C-fit.3mf"

def build():
    with ZipFile(BASE) as z: files={n:z.read(n) for n in z.namelist()}
    root,cfg,rels=[E.fromstring(files[k]) for k in (MODEL,SETTINGS,RELATIONSHIPS)]
    for file,ids in [(KIT,["2","108"]),(CAP,["14"])]:
        with ZipFile(file) as z:
            donor=E.fromstring(z.read(SETTINGS))
            donor_model=E.fromstring(z.read(MODEL))
            for id_ in ids:
                old=cfg.find(f"object[@id='{id_}']")
                old.getparent().replace(old,donor.find(f"object[@id='{id_}']"))
                old=root.find(f".//{CORE}resources/{CORE}object[@id='{id_}']")
                new=donor_model.find(f".//{CORE}resources/{CORE}object[@id='{id_}']")
                old.getparent().replace(old,new)
                for c in new.findall(f".//{CORE}component"):
                    path=c.get(PROD+"path").lstrip("/")
                    files[path]=z.read(path)
    plate=cfg.findall("plate")[6]
    plate.find("metadata[@key='plater_name']").set("value","07 PCB gauges - case board")
    for id_ in ["110","122","124","126","128","130","132"]:
        obj=root.find(f".//{CORE}resources/{CORE}object[@id='{id_}']")
        path=obj.find(f".//{CORE}component").get(PROD+"path")
        del files[path.lstrip("/")]
        rels.remove(next(c for c in rels if c.get("Target")==path))
        for n in (obj,root.find(f".//{CORE}build/{CORE}item[@objectid='{id_}']"),
                  cfg.find(f"object[@id='{id_}']"),next(n for n in plate.findall("model_instance") if value(n,"object_id")==id_)):
            n.getparent().remove(n)
    item=root.find(f".//{CORE}build/{CORE}item[@objectid='108']")
    item.set("transform"," ".join(item.get("transform").split()[:-1]+["0.4"]))
    xml=E.fromstring(files["3D/Objects/object_3.model"])
    obj=cfg.find("object[@id='6']")
    part=obj.find("part[@id='5']")
    mesh=trimesh.load_mesh(HERE/"rotor.stl")
    offset=np.array([float(value(part,"source_offset_"+k)) for k in "xyz"])
    mesh.vertices=mesh.vertices-offset
    replace_mesh(xml,"5",mesh)
    for m in (obj.find("metadata[@face_count]"),part.find("mesh_stat")):m.set("face_count",str(len(mesh.faces)))
    for m in (obj.find("metadata[@key='name']"),part.find("metadata[@key='name']")):m.set("value","Reel rotor - reinforced pocket")
    files.update({MODEL:encode(root),SETTINGS:encode(cfg),RELATIONSHIPS:encode(rels),"3D/Objects/object_3.model":encode(xml)})
    # Layer ranges address the one-based build order in Bambu Studio.
    items=root.findall(f".//{CORE}build/{CORE}item")
    order=next(i for i,item in enumerate(items,1) if item.get("objectid")=="24")
    ranges=E.fromstring(files["Metadata/layer_config_ranges.xml"])
    region=E.SubElement(E.SubElement(ranges,"object",id=str(order)),"range",min_z="32.8",max_z="35.2")
    E.SubElement(region,"option",opt_key="layer_height").text="0.10"
    files["Metadata/layer_config_ranges.xml"]=encode(ranges)
    cuts=E.fromstring(files["Metadata/cut_information.xml"])
    assert all(n.find("cut_id").get("connectors_cnt")=="0" for n in cuts)
    for n in list(cuts)[len(items):]:
        cuts.remove(n)
    files["Metadata/cut_information.xml"]=encode(cuts)
    with ZipFile(PROJECT,"w") as out:
        for k,b in sorted(files.items()):out.writestr(ZipInfo(k,(2026,11,23,0,0,0)),b,compress_type=ZIP_DEFLATED)
    print(PROJECT,flush=True)
if __name__=="__main__":build()
