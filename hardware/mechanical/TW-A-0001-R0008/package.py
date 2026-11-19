"""Export the fitted STEP, offline assembly viewer and hash-checked R0008 build kit."""
import argparse
import base64
import csv
import io
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
import zlib

import cadquery as cq
import numpy as np

from build import HERE, PARTS
from verify_fit import parts_from_step

REV="TW-A-0001-R0008"
REPO=HERE.parents[2]
PRIOR=HERE.parent/"rev-G"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def records():
    return {r["id"]:r for r in load(PRIOR/"parts.json")}


def used_shapes():
    return {key:cq.Shape.importBrep(str(HERE/"CAD"/(name+".brep"))) for name,(key,*_) in PARTS.items() if key}


def step(out,work,cache,source):
    original=parts_from_step(source,cache)
    original.update(used_shapes())
    catalog=records()
    complete=cq.Assembly(name="TW_A_0001_R0008_drawing_maximum")
    for key,s in sorted(original.items()):
        complete.add(s,name=key,color=cq.Color(catalog[key]["color"]))
    temp=work/(REV+".step")
    complete.export(str(temp))
    dest=out/(REV+"-dressed.step.gz")
    with temp.open("rb") as f, dest.open("wb") as target:
        with gzip.GzipFile(filename="",fileobj=target,mode="wb",compresslevel=6,mtime=0) as g:
            shutil.copyfileobj(f,g)
    print("STEP",len(original),dest.stat().st_size,flush=True)


def viewer(out):
    shapes=used_shapes()
    src=(REPO/"docs/models/Riffle-Rev-G-exploded.html").read_text(encoding="utf-8")
    pat=r'(<script type="application/json" id="geometry">)(.+?)(</script>)'
    match=re.search(pat,src,re.S)
    rows=json.loads(match[2])
    bykey={key:load(HERE/"part-orientations.json")[name] for name,(key,*_) in PARTS.items() if key}
    for row in rows:
        key=row["id"]
        if key not in shapes:
            continue
        shape=shapes[key]
        vv,ff=shape.tessellate(.04,.10)
        def enc(a):
            return base64.b64encode(zlib.compress(a.tobytes(),7)).decode()
        row.update(v=enc(np.rint(np.array([p.toTuple() for p in vv])*100).astype("<i2")),
                   t=enc(np.array(ff,dtype="<u4")),source=REV+"/CAD/"+Path(bykey[key]["assembly_brep"]).name,
                   kind="R0008 fit-print CAD")
        b=shape.BoundingBox()
        row["bounds_mm"]=[round(getattr(b,coord),4) for coord in ("xmin","xmax","ymin","ymax","zmin","zmax")]
        row["note"]="Print on the "+bykey[key]["bed_face"].lower()+". "+row["note"]
        if key=="Housing":
            row["name"]="R0008 battery-bay housing"
    src=src[:match.start(2)]+json.dumps(rows,separators=(",",":"),ensure_ascii=False)+src[match.end(2):]
    src=src.replace(">REV G<",">R0008<").replace('"revision":"G"','"revision":"R0008"')
    src=src.replace('revision==="G"','revision==="R0008"')
    src=src.replace('" dressed-part pairs checked. "','" Rev G reference pairs. R0008 added material passed separate interference checks. "')
    src=src.replace('" seated pairs checked for this pack. "','" seated pairs in the Rev G reference. R0008 pack insertion and added-material checks passed. "')
    src=src.replace('Thai Waters · Assembly inspection','Thai Waters R0008 · Assembly inspection')
    doc=REPO/"docs/models"/(REV+"-exploded.html")
    doc.write_text(src,encoding="utf8")
    shutil.copyfile(doc,out/doc.name)
    print("viewer",len(rows),flush=True)


def kit(out):
    members={}
    for name, (key,*_) in PARTS.items():
        p=HERE/"Print"/(name+".stl")
        members[("Print/" if key else "Inert-gauges/")+p.name]=p
    for name in ["PRINT-GUIDE.md","part-orientations.json","fit-verification.json","build.py","verify_fit.py","verify_bores.py","horizontal-bores.json","export-verification.json","package.py"]:
        members[name]=HERE/name
    for folder in ["CAD","inputs","QA"]:
        for p in (HERE/folder).rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                members[p.relative_to(HERE).as_posix()]=p
    # Keep the supplier gauge reference and attribution with the offline kit.
    for name in ["Adafruit-258.step","Adafruit-CAD-LICENSE.txt"]:
        members["inputs/"+name]=HERE.parent/"rev-F/review/inputs"/name
    dest=out/(REV+"-fit-print.zip")
    with ZipFile(dest,"w",ZIP_DEFLATED,compresslevel=6) as z:
        manifest=[]
        with (REPO/"hardware/revisions/members.csv").open(encoding="utf8",newline="") as f:
            members_table=[r for r in csv.DictReader(f) if r["assembly"]==REV]
        assert len(members_table)==12
        text=io.StringIO(newline="")
        writer=csv.writer(text,lineterminator="\n")
        writer.writerow(["Assembly ID","Part revision","Quantity","Kit member","SHA-256"])
        for r in members_table:
            filename="Print/"+Path(r["source"]).name
            writer.writerow([REV,r["part"],r["quantity"],filename,hashlib.sha256(members[filename].read_bytes()).hexdigest()])
        data=text.getvalue().encode("utf8")
        z.writestr("device-print-register.csv",data)
        manifest.append(hashlib.sha256(data).hexdigest()+"  device-print-register.csv")
        for name,p in sorted(members.items()):
            raw=p.read_bytes()
            if name=="part-orientations.json":
                orient=json.loads(raw)
                for part,record in orient.items():
                    if not record["viewer_id"]:
                        record["print_stl"]="Inert-gauges/"+part+".stl"
                raw=(json.dumps(orient,indent=2)+"\n").encode("utf-8")
            z.writestr(name,raw)
            manifest.append(hashlib.sha256(raw).hexdigest()+"  "+name)
        z.writestr("SHA256SUMS.txt","\n".join(manifest)+"\n")
    with ZipFile(dest) as z:
        assert z.testzip() is None
        for line in z.read("SHA256SUMS.txt").decode().splitlines():
            h,n=line.split("  ",1)
            assert hashlib.sha256(z.read(n)).hexdigest()==h
        assert len([n for n in z.namelist() if n.endswith(".stl")])==14
    print("kit",len(members),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("targets",nargs="+",choices=["step","viewer","kit"])
    parser.add_argument("--exports",type=Path,required=True)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--reference-step",type=Path)
    parser.add_argument("--cache",type=Path)
    args=parser.parse_args()
    if "step" in args.targets:
        step(args.exports,args.work,args.cache,args.reference_step)
    if "viewer" in args.targets:
        viewer(args.exports)
    if "kit" in args.targets:
        kit(args.exports)
