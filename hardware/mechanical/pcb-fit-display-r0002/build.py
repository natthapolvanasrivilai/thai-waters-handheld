"""Build the inert display gauge with the existing six dry-fit lands fused into its back."""
from pathlib import Path
import json
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import manifold3d as mf
import numpy as np
import trimesh
from lxml import etree as ET

HERE = Path(__file__).resolve().parent
M = HERE.parent
G = M/"pcb-fit-r0013"
sys.path.insert(0, str(G))
from check_assembly_fit import SUPPORTS, solid, digest

PROJECT = HERE/"Display-gauge-with-seats-X1C.3mf"
N = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
def make_gauge():
    ledger = json.loads((G/"geometry.json").read_bytes())["parts"]
    def installed(name):
        row = ledger[name]
        path = G/row["file"]
        assert digest(path) == row["sha256"]
        return solid(trimesh.load_mesh(path)).transform(row["print_to_installed_3x4"])
    original = installed("A1-display")
    body = original
    results = []
    for id, board in [("A4-display-shim","A4-integration"),("A5-display-shim","A5-power")]:
        z, centres = SUPPORTS[id]
        gauge = installed(board)
        shim = solid(trimesh.load_mesh(G/"meshes"/(id+".stl")))
        for x,y in centres:
            pad = shim.translate((x,y,z))
            # Overlap within the original A1 by 0.05 mm for robust union.
            joined = mf.Manifold.cube((3,3,21.05-z)).translate((x-1.5,y-1.5,z))
            overlap = (joined ^ original).volume()
            assert abs(overlap-.45)<.001
            assert (joined-original-pad).volume()<.0001
            patch = pad.slice(z+.001)
            assert abs((patch ^ gauge.slice(z-.001)).area()-9)<.001
            body = body + joined
            results.append(dict(board=board,installed_center_xy_mm=[x,y],bearing_z_mm=z,
                                nominal_height_mm=round(21-z,3),contact_area_mm2=9))
        assert abs((body ^ gauge).volume())<.0001
    assert body.status() == mf.Error.NoError and len(body.decompose())==1
    assert abs(body.volume()-original.volume()-sum(r["nominal_height_mm"]*9 for r in results))<.001
    pose = np.eye(4)
    pose[:3] = ledger["A1-display"]["print_to_installed_3x4"]
    m = body.transform(np.linalg.inv(pose)[:3]).to_mesh64()
    mesh = trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts)
    path = HERE/"display-gauge-with-seats.stl"
    mesh.export(path)
    mesh = trimesh.load_mesh(path)
    assert mesh.is_volume and len(mesh.split())==1
    assert np.allclose(mesh.bounds,ledger["A1-display"]["print_min_max_mm"],atol=.001)
    return mesh,results

def project(mesh):
    parent = M/"TW-A-0001-R0016/Printing/Thai-Waters-R0016-PCB-Fit-X1C.3mf"
    model,obj,cfg,rels = "3D/3dmodel.model","3D/Objects/gauge_102.model","Metadata/model_settings.config","3D/_rels/3dmodel.model.rels"
    with ZipFile(parent) as z:
        files={k:z.read(k) for k in (model,obj,cfg,rels,"[Content_Types].xml","_rels/.rels","Metadata/project_settings.config")}
    root,part,config,links=(ET.fromstring(files[k]) for k in (model,obj,cfg,rels))
    def retain(nodes, keep):
        for el in nodes:
            if not keep(el): el.getparent().remove(el)
    retain(root.findall(".//"+N+"object"),lambda el:el.get("id")=="102")
    retain(root.findall(".//"+N+"item"),lambda el:el.get("objectid")=="102")
    mid=mesh.bounds.mean(axis=0)
    root.find(".//"+N+"item").set("transform",f"1 0 0 0 1 0 0 0 1 128 128 {mid[2]:.8f}")
    v,f=(part.find(".//"+N+tag) for tag in ("vertices","triangles"))
    v.clear()
    f.clear()
    for x,y,z in mesh.vertices-mid:
        ET.SubElement(v,N+"vertex",x=str(x),y=str(y),z=str(z))
    for i,j,k in mesh.faces:
        ET.SubElement(f,N+"triangle",v1=str(i),v2=str(j),v3=str(k))
    retain(config.findall("object"),lambda el:el.get("id")=="102")
    retain(config.findall("plate"),lambda el:el.find("metadata[@key='plater_id']").get("value")=="7")
    retain(config.findall("plate/model_instance"),lambda el:el.find("metadata[@key='object_id']").get("value")=="102")
    config.find("plate/metadata[@key='plater_id']").set("value","1")
    config.find("plate/metadata[@key='plater_name']").set("value","Inert display with six fixed seats")
    for el in config.xpath(".//*[@face_count]"):el.set("face_count",str(len(mesh.faces)))
    for el in config.findall(".//metadata[@key='name']"):el.set("value","Display gauge with A4 and A5 seats")
    config.find(".//metadata[@key='matrix']").set("value",f"1 0 0 128 0 1 0 128 0 0 1 {mid[2]} 0 0 0 1")
    retain(list(links),lambda el:el.get("Target","").endswith("/gauge_102.model"))
    for k,tree in zip((model,obj,cfg,rels),(root,part,config,links)):
        files[k]=ET.tostring(tree,encoding="UTF-8",xml_declaration=True)
    with ZipFile(PROJECT,"w") as out:
        for k,data in sorted(files.items()):
            out.writestr(ZipInfo(k,(2026,11,23,0,0,0)),data,compress_type=ZIP_DEFLATED)

if __name__=="__main__":
    mesh,seats=make_gauge()
    project(mesh)
    (HERE/"fit.json").write_text(json.dumps(dict(seats=seats,one_connected_mesh=True,
        project_sha256=digest(PROJECT),stl_sha256=digest(HERE/"display-gauge-with-seats.stl")),indent=2)+"\n")
