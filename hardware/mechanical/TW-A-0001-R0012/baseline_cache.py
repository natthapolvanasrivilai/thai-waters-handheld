"""Expand the verified R0011 STEP into installed part solids for local motion checks."""
import argparse
import gzip
from pathlib import Path
import shutil
import tempfile
import cadquery as cq
from build import OLD, digest, load


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("r0011_step_gz",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    ledger=load(OLD/"installed-step.json")
    if digest(args.r0011_step_gz)!=load(OLD/"export-verification.json")["packed_step_sha256"]:
        p.error("The archive must match the R0011 engineering release")
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/"baseline.step"
        with gzip.open(args.r0011_step_gz,"rb") as a,path.open("wb") as b:
            shutil.copyfileobj(a,b)
        assert digest(path)==ledger["step_sha256"]
        assembly=cq.Assembly.load(str(path))
    assert {n.name for n in assembly.children}==set(ledger["components"])
    args.output.mkdir(exist_ok=True,parents=True)
    for node in assembly.children:
        shape=node.obj.moved(node.loc)
        assert abs(shape.Volume()-ledger["components"][node.name]["volume_mm3"])<0.01
        shape.exportBrep(str(args.output/(node.name+".brep")))
    print(len(assembly.children),"installed solids/groups extracted")


if __name__=="__main__":
    main()
