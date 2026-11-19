"""Package and reopen every matched printable, its installed CAD, and fit evidence."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from build import BASE, HERE


def kit(output):
    repo = HERE.parents[2]
    meta = json.loads((HERE / "part-orientations.json").read_text())
    checks = json.loads((HERE / "QA/print-audit.json").read_text())
    with (repo/"hardware/revisions/members.csv").open(encoding="utf-8-sig") as csvfile:
        parts = {Path(row["source"]).stem:row["part"] for row in csv.DictReader(csvfile) if row["assembly"]==HERE.name}
    assert len(parts)==17
    parts["usb-c-shield-mask"]=parts["usb-c-shield-mask-two-colour"]
    files={}
    register=io.StringIO(newline="")
    fieldnames=("file","part","role","quantity_per_unit","material","sha256")
    writer=csv.DictWriter(register,fieldnames=fieldnames,lineterminator="\n")
    writer.writeheader()

    def add(name, path):
        data=path.read_bytes()
        files[name]=data
        return hashlib.sha256(data).hexdigest()

    for name, row in meta.items():
        mesh=HERE/row["print_stl"]
        p="Print/"+mesh.name
        sha=add(p,mesh)
        assert sha==row["sha256"]==checks[name]["sha256"]
        row["print_stl"]=p
        cad=HERE/row["assembly_brep"]
        row["assembly_brep"]="CAD/"+cad.name
        add(row["assembly_brep"],cad)
        role="device" if name in parts else "inert gauge"
        if name=="usb-c-shield-mask":
            role="single-colour alternative to two-colour 3MF"
        writer.writerow(dict(file=p,part=parts.get(name,""),role=role,quantity_per_unit=int(role=="device"),material=row.get("material",checks[name]["material"]),sha256=sha))
    mask="Print/usb-c-shield-mask-two-colour.3mf"
    writer.writerow(dict(file=mask,part=parts["usb-c-shield-mask"],role="device",quantity_per_unit=1,material="Opaque TPU 95A; two regions",
                         sha256=add(mask,BASE/mask)))
    add("CAD/usb-c-shield-mask-unloaded.brep",BASE/"CAD/usb-c-shield-mask-unloaded.brep")
    files["part-orientations.json"]=(json.dumps(meta,indent=2)+"\n").encode()
    files["print-manifest.csv"]=register.getvalue().encode()
    for name in ("README.md","PRINT-GUIDE.md","installed-step.json","export-verification.json","QA/print-audit.json","QA/service-cover.json","QA/service-cover-installed.png","QA/service-cover-removed.png"):
        add(name,HERE/name)
    files["PRINT-GUIDE.md"]=files["PRINT-GUIDE.md"].replace(b"../TW-A-0001-R0009/PRINT-GUIDE.md",b"R0009/PRINT-GUIDE.md")
    files["README.md"]=files["README.md"].replace(b"../../revisions/README.md",b"print-manifest.csv")
    add("R0009/PRINT-GUIDE.md",BASE/"PRINT-GUIDE.md")
    for name in ("print-audit.json","usb-port.json","power-key.json","mechanism.json","speaker-fit.json","battery-fit.json","dressed-harness.json"):
        add("R0009/QA/"+name,BASE/"QA"/name)
    hashes = "".join(hashlib.sha256(data).hexdigest()+"  "+name+"\n" for name,data in sorted(files.items()))
    files["SHA256SUMS.txt"]=hashes.encode()
    output.mkdir(parents=True,exist_ok=True)
    path=output/(HERE.name+"-fit-print.zip")
    with ZipFile(path,"w",ZIP_DEFLATED,compresslevel=7) as archive:
        for name,data in sorted(files.items()):
            archive.writestr(name,data)
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        for line in archive.read("SHA256SUMS.txt").decode().splitlines():
            sha, name = line.split("  ",1)
            assert sha==hashlib.sha256(archive.read(name)).hexdigest()
        rows=list(csv.DictReader(io.StringIO(archive.read("print-manifest.csv").decode())))
        assert len([r for r in rows if r["role"]=="inert gauge"])==2
        assert len([r for r in rows if r["role"]=="device"])==17
    print(path, len(files),"verified members")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exports",type=Path,required=True)
    kit(parser.parse_args().exports)
