"""Cross-check R0012 electronics against the withdrawn R19b X1C housing only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import cadquery as cq
import manifold3d as mf
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
H = ROOT/"hardware/electronics/harness-r0005"
M = ROOT/"hardware/mechanical/TW-A-0001-R0012"
sys.path.insert(0,str(M))
from service_check import tri, model, meshgap, tube
from mate import guide, JACKET_OD, STROKE, split_latch, actuate

R19B = "dcfc3c9c0725d91c54026f1e65f5b9855a036b35f61483d5b1dfcfb471db546c"
H1 = np.array([[-36,-24.25,1.4],[-36,24.25,1.4],[36,-24.25,1.4],[36,24.25,1.4]])
def manifold(v,t):
    mesh=mf.Mesh64(np.ascontiguousarray(v,dtype=np.float64),np.ascontiguousarray(t,dtype=np.uint64))
    mesh.merge()
    solid=mf.Manifold(mesh)
    return solid if solid.status()==mf.Error.NoError and not solid.is_empty() else None


def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("r19b",type=Path)
    args.add_argument("--revision-dir",type=Path)
    args.add_argument("--output",type=Path,default=HERE/"r19b-shell-fit.json")
    cfg=args.parse_args()
    path=cfg.r19b
    source=H/"installed.json"
    override={}
    form=guide
    if cfg.revision_dir:
        revision=cfg.revision_dir.resolve()
        sys.path.insert(0,str(revision))
        from stroke import new_leads
        form=new_leads().guide
        source=revision/"overlay.json"
        for row in json.loads(source.read_bytes())["add"]:
            part=revision/row["brep"]
            assert hashlib.sha256(part.read_bytes()).hexdigest()==row["sha256"]
            override[row["name"]]=part
    assert hashlib.sha256(path.read_bytes()).hexdigest()==R19B
    with ZipFile(path) as z:
        settings=ET.fromstring(z.read("Metadata/model_settings.config"))
        meta=settings.find("object[@id='9']")
        assert "datum-pocket housing" in meta.find("metadata[@key='name']").get("value")
        base=ET.fromstring(z.read("3D/3dmodel.model"))
        components=base.find(".//{*}object[@id='9']/{*}components")
        m={c.get("objectid"):np.fromstring(c.get("transform"),sep=" ")[9:] for c in components}
        assert all(meta.find(f"part[@id='{i}']/metadata[@key='name']").get("value").startswith(f"H1-{i-2} screw corridor") for i in range(3,7))
        frame=np.stack([m[str(i)] for i in range(3,7)])
        raw=ET.fromstring(z.read("3D/Objects/object_27.model")).find(".//{*}object[@id='1']/{*}mesh")
        v=np.array([[float(x.get(k)) for k in ("x","y","z")] for x in raw.find("{*}vertices")])
        t=np.array([[int(x.get(k)) for k in ("v1","v2","v3")] for x in raw.find("{*}triangles")])
    x=frame[2]-frame[0];x/=np.linalg.norm(x)
    y=frame[1]-frame[0];y/=np.linalg.norm(y)
    reg=np.stack([x,y,np.cross(x,y)])
    pos=H1.mean(axis=0)-frame.mean(axis=0)@reg.T
    error=np.max(np.linalg.norm(frame@reg.T+pos-H1,axis=1))
    assert error<.01
    vertices=v@reg.T+pos
    enclosure=manifold(vertices,t)
    assert enclosure is not None
    shell_mesh=model(vertices,t)
    harness_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    checks={}
    def placed(k):
        return cq.Shape.importBrep(str(override.get(k,H/"placed"/(k+".brep"))))
    ids=["drvBoard","drvParts","A3-J1-header","A3-J1-plug","A3-J1-TPA","A4-integration","A5-power",
         "A4-spacers","A5-spacers",*["w1"+n for n in ("VCC","SCL","SDA","GND")],
         *["wh"+n for n in ("VCC","SCL","SDA","GND")]]
    for k in sorted(set(ids)|set(override)):
        hits=0.;gap=float("inf");missing=0
        for s in placed(k).Solids():
            vv,tt=tri(s)
            gap=min(gap,meshgap(model(vv,tt),shell_mesh))
            native=manifold(vv,tt)
            if native is None:missing+=1
            else:hits+=(native^enclosure).volume()
        checks[k]={"mesh_gap_mm":round(gap,5),"known_common_volume_mm3":round(hits,5),"solids_without_volume_check":missing}
        print(k,checks[k],flush=True)
    r=json.loads((H/"routing.json").read_text())
    best=(float("inf"),"",0)
    for d in np.linspace(0,STROKE,67):
        for n in ("VCC","SCL","SDA","GND"):
            tx,_,z=r[n]["tap_center_mm"]
            pts=form(n,tx,z,d);pts.insert(0,[pts[0][0],-5.35+d,10.36])
            gap=meshgap(tube(pts,JACKET_OD/2),shell_mesh)
            best=min(best,(gap,n,float(d)))
    assert harness_hash==hashlib.sha256(source.read_bytes()).hexdigest()
    results={"r19b_sha256":R19B,"harness_sha256":harness_hash,
      "scope":"R19b printed housing triangles, component 1 only. Registration uses four named H1 screw-corridor modifier centers and the shared 1.4 mm height datum. Physical registration, carrier, bezel, battery insertion, support residue, hand access and cable tolerances remain open.",
      "registration_max_residual_mm":float(error),"source_to_installed_rotation":reg.tolist(),"translation_mm":pos.tolist(),
      "r19b_triangles":len(t),"seated":checks,"W4_to_R19b_shell_67_stations":{"minimum_mesh_mm":round(best[0],5),"wire":best[1],"travel_mm":best[2]}}
    cfg.output.write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results["W4_to_R19b_shell_67_stations"]),flush=True)
if __name__=="__main__":
    main()
