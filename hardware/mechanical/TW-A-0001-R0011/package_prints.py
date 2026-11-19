"""Pack all matched STLs, installed solids, original service instructions and verified plate evidence."""
import argparse
import csv
import hashlib
import io
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
from build import HERE, OLD, LEGACY, load

def package(exports):
    meta=load(HERE/"part-orientations.json")
    mesh_reports=load(HERE/"QA/print-audit.json")
    with (HERE.parents[1]/"revisions/members.csv").open(encoding="utf-8-sig") as src:
        part_ids={Path(r["source"]).stem:r["part"] for r in csv.DictReader(src) if r["assembly"]==HERE.name}
    assert len(part_ids)==17
    members={}
    manifest=io.StringIO(newline="")
    wr=csv.writer(manifest,lineterminator="\n")
    wr.writerow(["file","part","role","quantity_per_unit","material","sha256"])
    def add(key,source):
        data=source.read_bytes()
        members[key]=data
        return hashlib.sha256(data).hexdigest()
    for name,row in meta.items():
        for kind,folder in (("assembly_brep","CAD"),("print_stl","Print")):
            src=HERE/row[kind]
            key=folder+"/"+src.name
            sha=add(key,src)
            row[kind]=key
        assert sha==row["sha256"]==mesh_reports[name]["sha256"]
        role="device" if name in part_ids else "inert gauge"
        part=part_ids.get(name,"")
        if name=="usb-c-shield-mask":
            role="single-colour alternative to two-colour 3MF"
            part=part_ids[name+"-two-colour"]
        wr.writerow([key,part,role,int(role=="device"),row.get("material",mesh_reports[name]["material"]),sha])
    mask="Print/usb-c-shield-mask-two-colour.3mf"
    wr.writerow([mask,part_ids[Path(mask).stem],"device",1,"Opaque TPU 95A, two regions",add(mask,LEGACY/mask)])
    add("CAD/usb-c-shield-mask-unloaded.brep",LEGACY/"CAD/usb-c-shield-mask-unloaded.brep")
    members["print-manifest.csv"]=manifest.getvalue().encode()
    members["part-orientations.json"]=(json.dumps(meta,indent=2)+"\n").encode()
    for name in ("README.md","PRINT-GUIDE.md","QA/print-audit.json","QA/housing-toolpaths.json","QA/receiver-toolpaths.png"):
        add(name,HERE/name)
    for rev in (OLD,LEGACY):
        add(rev.name+"/PRINT-GUIDE.md",rev/"PRINT-GUIDE.md")
        for src in (rev/"QA").glob("*"):
            if src.suffix in {".json",".png"}:
                add(rev.name+"/QA/"+src.name,src)
        members["PRINT-GUIDE.md"]=members["PRINT-GUIDE.md"].replace(("../"+rev.name).encode(),rev.name.encode())
    rows=list(csv.DictReader(io.StringIO(manifest.getvalue())))
    assert sum(r["role"]=="device" for r in rows)==17 and sum(r["role"]=="inert gauge" for r in rows)==2
    members["SHA256SUMS.txt"]="".join(hashlib.sha256(data).hexdigest()+"  "+k+"\n" for k,data in sorted(members.items())).encode()
    exports.mkdir(exist_ok=True,parents=True)
    path=exports/(HERE.name+"-fit-print.zip")
    with ZipFile(path,"w",ZIP_DEFLATED,compresslevel=7) as archive:
        for k,data in sorted(members.items()):
            archive.writestr(k,data)
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        for line in archive.read("SHA256SUMS.txt").decode().splitlines():
            sha,key=line.split("  ",1)
            assert sha==hashlib.sha256(archive.read(key)).hexdigest()
    print(path, len(members), "verified members")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exports",type=Path,required=True)
    package(p.parse_args().exports)
