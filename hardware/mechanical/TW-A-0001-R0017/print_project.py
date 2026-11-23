"""Pack the registered mesh and R0016 X1C PETG settings into a cap-only editable plate."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from lxml import etree as ET
import trimesh
import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.with_name("TW-A-0001-R0016")
PROJECT = HERE/"Print/R0017-keyed-power-cap-X1C.3mf"
CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
def xml(node):
    return ET.tostring(node,encoding="utf-8",xml_declaration=True)

def build():
    with ZipFile(next((PARENT/"Printing").glob("*.3mf"))) as archive:
        files={k:archive.read(k) for k in archive.namelist()}
    model, obj, settings, rels="3D/3dmodel.model","3D/Objects/object_7.model","Metadata/model_settings.config","3D/_rels/3dmodel.model.rels"
    root, child, cfg, links=(ET.fromstring(files[name]) for name in (model,obj,settings,rels))
    mesh=trimesh.load_mesh(HERE/"Print/power-cap.stl")
    vertices, faces=(child.find(".//"+CORE+t) for t in ("vertices","triangles"))
    vertices.clear()
    faces.clear()
    for x,y,z in mesh.vertices-np.array([0,0,.660000026]):
        ET.SubElement(vertices,CORE+"vertex",x=str(x),y=str(y),z=str(z))
    for a,b,c in mesh.faces:
        ET.SubElement(faces,CORE+"triangle",v1=str(a),v2=str(b),v3=str(c))
    def prune(nodes,keep):
        for node in nodes:
            if not keep(node):
                node.getparent().remove(node)
    prune(root.findall(".//"+CORE+"object"),lambda o:o.get("id")=="14")
    prune(root.findall(".//"+CORE+"item"),lambda o:o.get("objectid")=="14")
    root.find(".//"+CORE+"item").set("transform","1 0 0 0 1 0 0 0 1 128 128 .660000026")
    prune(cfg.findall("object"),lambda o:o.get("id")=="14")
    prune(cfg.findall("plate"),lambda p:p.find("metadata[@key='plater_id']").get("value")=="2")
    cfg.find("plate/metadata[@key='plater_id']").set("value","1")
    cfg.find("plate/metadata[@key='plater_name']").set("value","R0017 keyed cap - PETG")
    prune(cfg.findall("plate/model_instance"),lambda i:i.find("metadata[@key='object_id']").get("value")=="14")
    for n in cfg.xpath(".//*[@face_count]"): n.set("face_count",str(len(mesh.faces)))
    for n in cfg.findall(".//metadata[@key='name']"): n.set("value","R0017 keyed power cap")
    cfg.find(".//metadata[@key='matrix']").set("value","1 0 0 128 0 1 0 128 0 0 1 .660000026 0 0 0 1")
    ET.SubElement(cfg.find("object"),"metadata",key="layer_height",value="0.12")
    prune(list(links),lambda n:n.get("Target","").endswith("object_7.model"))
    keep={name:files[name] for name in ("[Content_Types].xml","_rels/.rels","Metadata/project_settings.config")}
    keep.update(dict(zip((model,obj,settings,rels),map(xml,(root,child,cfg,links)))))
    with ZipFile(PROJECT,"w") as out:
        for name,data in sorted(keep.items()):
            out.writestr(ZipInfo(name,(2026,11,23,0,0,0)),data,compress_type=ZIP_DEFLATED)
if __name__=="__main__":
    build()
