"""Install the controlled electrical rework into the previous complete, covered STEP."""
import argparse
import gc
import gzip
from pathlib import Path
import shutil
import sys

import cadquery as cq

from build import HERE, OLD, digest, load, save
sys.path.append(str(OLD))
from verify_cover import measure

ROOT=HERE.parents[2]
HARNESS=ROOT/"hardware/electronics/harness-r0004/installed.json"

def bounds(shape):
    box=shape.BoundingBox()
    return [round(getattr(box,k),4) for k in ("xmin","xmax","ymin","ymax","zmin","zmax")]

def describe(shape):
    return dict(volume_mm3=round(shape.Volume(),5),solids=len(shape.Solids()),bounds_mm=bounds(shape))

def unpack(source,out):
    with gzip.open(source,"rb") as inp,out.open("wb") as f:
        shutil.copyfileobj(inp,f)

def integrate(reference, work, exports):
    work.mkdir(exist_ok=True,parents=True)
    exports.mkdir(exist_ok=True,parents=True)
    baseline=load(OLD/"installed-step.json")
    assert digest(reference)==load(OLD/"export-verification.json")["packed_step_sha256"]
    raw=work/"source.step"
    unpack(reference,raw)
    assert digest(raw)==baseline["step_sha256"]
    print("Reading source STEP",flush=True)
    source=cq.Assembly.load(str(raw))
    signature=digest(HARNESS)
    changes=load(HARNESS)
    expected=baseline["components"].copy()
    remove=set(changes["remove"])
    assert {n.name for n in source.children}==set(expected)
    assert remove.issubset(expected)
    updated=cq.Assembly(name="TW_A_0001_R0011_supplier_cell")
    for child in source.children:
        if child.name in remove:
            del expected[child.name]
        else:
            updated.add(child.obj,name=child.name,color=child.color,loc=child.loc)
    for row in changes["add"]:
        key=row["name"]
        assert key not in expected
        brep=HARNESS.parent/row["brep"]
        assert digest(brep)==row["sha256"],key
        shape=cq.Shape.importBrep(str(brep))
        assert shape.isValid() and shape.Volume()>0,key
        updated.add(shape,name=key,color=cq.Color(row["color"]))
        expected[key]=dict(**describe(shape), source_brep=row["brep"],source_sha256=row["sha256"],
                           component_label=row.get("label",key),geometry_provenance=row.get("note",""))
    print("Writing",len(expected),"installed components",flush=True)
    output=work/(HERE.name+"-dressed.step")
    updated.export(str(output))
    del source,updated
    gc.collect()
    packed=exports/(output.name+".gz")
    with output.open("rb") as inp,packed.open("wb") as out:
        with gzip.GzipFile(filename="",fileobj=out,mode="wb",compresslevel=6,mtime=0) as stream:
            shutil.copyfileobj(inp,stream)
    reread=work/"roundtrip.step"
    unpack(packed,reread)
    assert digest(output)==digest(reread)
    print("Verifying round trip",flush=True)
    actual=cq.Assembly.load(str(reread))
    shaped={c.name:c.obj.moved(c.loc) for c in actual.children}
    assert set(shaped)==set(expected)
    worst_volume=worst_extent=0
    for key,shape in shaped.items():
        ref=expected[key]
        dv=abs(shape.Volume()-ref["volume_mm3"])
        db=max(abs(a-b) for a,b in zip(bounds(shape),ref["bounds_mm"]))
        assert len(shape.Solids())==ref["solids"] and dv<=max(.014,ref["volume_mm3"]*3e-6) and db<=.015,(key,dv,db)
        worst_volume=max(worst_volume,dv)
        worst_extent=max(worst_extent,db)
    assert signature==digest(HARNESS),"Harness changed during STEP generation"
    cover=measure(shaped)
    cover.update(assembly=HERE.name,source="R0011 compressed STEP reimport")
    save(HERE/"QA/service-cover.json",cover)
    save(HERE/"installed-step.json",dict(component_count=len(expected),step_sha256=digest(reread),components=expected))
    save(HERE/"export-verification.json",dict(source_assembly=OLD.name,source_step_sha256=baseline["step_sha256"],
        installed_step_components=len(expected),step_sha256=digest(reread),packed_step_sha256=digest(packed),
        max_roundtrip_absolute_volume_delta_mm3=round(worst_volume,6),max_bounds_delta_mm=round(worst_extent,6),
        harness_manifest_sha256=signature,component_provenance={r["name"]:r.get("note","") for r in changes["add"]},removed_nodes=sorted(remove),added_nodes=[r["name"] for r in changes["add"]]))
    print(packed,flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ("reference","work","exports"):
        parser.add_argument("--"+k,type=Path,required=True)
    a=parser.parse_args()
    integrate(a.reference,a.work,a.exports)
