"""Produce an unpowered two-piece fit kit using the saved X1C housing profile."""
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import json
import sys
import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh
from lxml import etree as ET
from build import HERE,OUTLINE,MOUNTS,REST
from fit import support

MECH=HERE.parents[1]/"mechanical"
BASE=MECH/"TW-A-0001-R0016"
sys.path.insert(0,str(MECH/"TW-A-0001-R0014/Printing"))
from make_project import CORE,PROD,MODEL,SETTINGS,RELATIONSHIPS,HOUSING,value,encode,digest
PROJECT=HERE/"Case-board-R0001-X1C-fit.3mf"

def replace_mesh(doc,obj,mesh):
    meshnode=doc.find(f".//{CORE}object[@id='{obj}']/{CORE}mesh")
    v=meshnode.find(CORE+"vertices")
    t=meshnode.find(CORE+"triangles")
    v.clear()
    t.clear()
    for x,y,z in mesh.vertices:
        ET.SubElement(v,CORE+"vertex",x=f"{x:.8f}",y=f"{y:.8f}",z=f"{z:.8f}")
    for a,b,c in mesh.faces:
        ET.SubElement(t,CORE+"triangle",v1=str(a),v2=str(b),v3=str(c))

def run():
    row=json.loads((BASE/"part-orientations.json").read_bytes())["housing-battery-bay"]
    src=BASE/row["print_stl"]
    assert digest(src)==row["sha256"]
    parent=trimesh.load_mesh(src)
    housing=mf.Manifold(mf.Mesh64(np.asarray(parent.vertices),np.asarray(parent.faces,dtype=np.uint64)))
    transform=np.array(row["assembly_to_print"])[:3,:]
    for i,(x,y) in enumerate([*[(x-87,y-114) for x,y in MOUNTS],REST]):
        v,f=support(x,y,i+1).tessellate(.005,.07)
        post=trimesh.Trimesh([p.toTuple() for p in v],f)
        assert post.is_volume
        mesh=mf.Manifold(mf.Mesh64(np.asarray(post.vertices),np.asarray(post.faces,dtype=np.uint64)))
        housing=housing+mesh.transform(transform)
    assert len(housing.decompose())==1 and housing.status()==mf.Error.NoError
    h=housing.to_mesh64()
    body=trimesh.Trimesh(h.vert_properties[:,:3],h.tri_verts,process=False)
    assert body.is_volume
    np.testing.assert_allclose(body.bounds,parent.bounds,atol=.00005)
    gauge=cq.Workplane("XY").polyline(OUTLINE).close().extrude(.8).val()
    for x,y in MOUNTS:gauge=gauge.cut(cq.Solid.makeCylinder(1.15,1,cq.Vector(x,y,-.1)))
    vertices,faces=gauge.tessellate(.015,.10)
    g=trimesh.Trimesh([v.toTuple() for v in vertices],faces)
    assert g.is_volume
    # Place the printed outline in the same handedness as the installed board, holes up.
    g.vertices-=g.bounds.mean(axis=0)
    name="3D/Objects/gauge_108.model"
    parent_file=BASE/"Printing/Thai-Waters-R0016-PCB-Fit-X1C.3mf"
    with ZipFile(parent_file) as z:
        files={key:z.read(key) for key in z.namelist() if not key.startswith("3D/Objects/") or key in {HOUSING,name}}
    root,cfg,rels=[ET.fromstring(files[k]) for k in (MODEL,SETTINGS,RELATIONSHIPS)]
    for wrapper in root.findall(f".//{CORE}resources/{CORE}object"):
        if wrapper.get("id") not in ("2","108"):wrapper.getparent().remove(wrapper)
    for item in root.findall(f".//{CORE}build/{CORE}item"):
        if item.get("objectid")=="108":item.set("transform","1 0 0 0 1 0 0 0 1 435.2 128 0.4")
        elif item.get("objectid")!="2":item.getparent().remove(item)
    for child in list(rels):
        if child.get("Target","").lstrip("/") not in (HOUSING,name):rels.remove(child)
    for obj in cfg.findall("object"):
        if obj.get("id") not in ("2","108"):cfg.remove(obj)
    for plate in cfg.findall("plate"):
        if value(plate,"plater_id")=="7":
            for inst in plate.findall("model_instance"):
                if value(inst,"object_id")!="108":plate.remove(inst)
            plate.find("metadata[@key='plater_id']").set("value","2")
            plate.find("metadata[@key='plater_name']").set("value","Combined PCB outline gauge")
        elif value(plate,"plater_id")!="1":cfg.remove(plate)
    for key,file,obj,mesh,label in [("2",HOUSING,"1",body,"Case with integral board mounts"),
                                    ("108",name,"107",g,"Case-mounted PCB outline gauge")]:
        objcfg=cfg.find(f"object[@id='{key}']")
        part=objcfg.find(f"part[@id='{obj}']")
        for meta in (objcfg.find("metadata[@key='name']"),part.find("metadata[@key='name']")):
            meta.set("value",label)
        if key=="2":
            mesh.vertices=mesh.vertices-np.array([float(value(part,"source_offset_"+k)) for k in "xyz"])
        else:
            part.find("metadata[@key='matrix']").set("value","1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")
        for meta in (objcfg.find("metadata[@face_count]"),part.find("mesh_stat")):
            if meta is not None:meta.set("face_count",str(len(mesh.faces)))
        xml=ET.fromstring(files[file])
        replace_mesh(xml,obj,mesh)
        files[file]=encode(xml)
    files.update({MODEL:encode(root),SETTINGS:encode(cfg),RELATIONSHIPS:encode(rels)})
    with ZipFile(PROJECT,"w",ZIP_DEFLATED) as zipout:
        for k,b in sorted(files.items()):
            zipout.writestr(ZipInfo(k,(2026,11,23,0,0,0)),b,compress_type=ZIP_DEFLATED)

if __name__=="__main__": run()
