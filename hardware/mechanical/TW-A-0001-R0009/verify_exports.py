"""Read the released STEP and 3MF back and compare them with the registered CAD."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import zlib
import cadquery as cq
import numpy as np
import trimesh
from package import REV,HERE,load,save,GEOMETRY,bbox

def verify(exports,work):
    ledger=load(HERE/"installed-step.json")
    step=work/(REV+"-roundtrip.step")
    compressed=exports/(REV+"-dressed.step.gz")
    with gzip.open(compressed,"rb") as source,step.open("wb") as dest:
        from shutil import copyfileobj
        copyfileobj(source,dest)
    assert hashlib.sha256(step.read_bytes()).hexdigest()==ledger["step_sha256"]
    assembly=cq.Assembly.load(str(step));parts={p.name:p.obj.moved(p.loc) for p in assembly.children}
    assert set(parts)==set(ledger["components"])
    worst_volume=worst_box=0.
    for k,shape in parts.items():
        ref=ledger["components"][k]
        dv=abs(shape.Volume()-ref["volume_mm3"]);db=max(abs(x-y) for x,y in zip(bbox(shape),ref["bounds_mm"]))
        # Vendor STEP has internally complex noncritical sliver topology.
        if dv>max(.014,abs(ref["volume_mm3"])*3e-6) or db>.015 or len(shape.Solids())!=ref["solids"]:
            raise ValueError((k,dv,db,len(shape.Solids()),ref["solids"]))
        worst_volume=max(worst_volume,dv);worst_box=max(worst_box,db)
    doc=exports/(REV+"-exploded.html");rows=json.loads(GEOMETRY.search(doc.read_text(encoding="utf8"))[2])
    assert {r["id"] for r in rows if r.get("productEligible")}==set(parts)
    for r in rows:
        verts=np.frombuffer(zlib.decompress(base64.b64decode(r["v"])),dtype="<i2").reshape(-1,3)
        tris=np.frombuffer(zlib.decompress(base64.b64decode(r["t"])),dtype="<u4").reshape(-1,3)
        assert len(verts) and len(tris) and tris.max()<len(verts)
    packed=HERE/"Print/usb-c-shield-mask-two-colour.3mf"
    with ZipFile(packed) as z:
        root=ET.fromstring(z.read("3D/3dmodel.model"))
    objects=root.findall(".//{*}object")
    assert [o.attrib["id"] for o in objects]==["2","3","4"]
    assert [o.attrib["objectid"] for o in objects[-1].findall(".//{*}component")]==["2","3"]
    materials={}
    for obj in objects[:2]:
        vs=[[float(p.attrib[k]) for k in ("x","y","z")] for p in obj.findall(".//{*}vertex")]
        fs=[[int(p.attrib[k]) for k in ("v1","v2","v3")] for p in obj.findall(".//{*}triangle")]
        m=trimesh.Trimesh(vertices=vs,faces=fs,process=False)
        assert m.is_watertight and m.is_volume and len(m.split())==1
        assert abs(m.bounds[0][2])<.002
        materials[obj.attrib["name"]]=round(m.volume,5)
    mask=trimesh.load_mesh(HERE/"Print/usb-c-shield-mask.stl")
    assert abs(sum(materials.values())-mask.volume)<.03
    report={"installed_step_components":len(parts),"viewer_inspection_entries":len(rows),"engineering_allowances_only":[r["id"] for r in rows if not r.get("productEligible")],
            "step_sha256":ledger["step_sha256"],"packed_step_sha256":hashlib.sha256(compressed.read_bytes()).hexdigest(),
            "max_roundtrip_absolute_volume_delta_mm3":round(worst_volume,6),"max_bounds_delta_mm":worst_box,
            "3mf_co_printed_region_volumes_mm3":materials,"single_mask_stl_volume_mm3":round(mask.volume,5)}
    save(HERE/"export-verification.json",report)
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--work",type=Path,required=True);p.add_argument("--exports",type=Path,required=True)
    a=p.parse_args();verify(a.exports,a.work)
