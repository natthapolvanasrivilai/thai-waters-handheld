"""Apply the R0013 service and haptic-board changes to a verified R0012 assembly."""
import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.with_name("TW-A-0001-R0012")
sys.path.insert(0, str(PREVIOUS))
from assembly import integrate
from build import digest, load, save

ELECTRONICS = ROOT / "hardware/electronics"
WIRES = ELECTRONICS / "harness-r0006"
HAPTIC = ELECTRONICS / "pcb-haptic-cie-r0002"

def prepare(parts, *, leads=None):
    source_rows = load(WIRES / "installed.json")["add"]
    rows = []
    previous = {r["name"]:r for r in load(ELECTRONICS/"harness-r0005/installed.json")["add"]}
    for row in source_rows:
        key = row["name"]
        path = (WIRES / row["brep"]).resolve()
        assert digest(path) == row["sha256"]
        rows.append({**previous[key], **row, "brep":os.path.relpath(path, HERE).replace(os.sep,"/")})
    for key, label in (("drvBoard","R0002 A3 haptic substrate"), ("drvParts","R0002 A3 populated electronics")):
        path = (parts / (key + ".brep")).resolve()
        rows.append({**previous[key], "sha256":digest(path), "label":label,
                     "note":"Installed from the rerouted A3 KiCad layout with the relocated electronic components.",
                     "brep":os.path.relpath(path, HERE).replace(os.sep,"/")})
    power=ELECTRONICS/"usb-entry-r0006/A5-power.brep"
    rows.append({**previous["A5-power"], "label":"R0006 A5 input protection and current control",
                 "note":"Revised A5 fixed at its installed location. A1 intercept wiring requires incoming-board identification.",
                 "sha256":digest(power), "brep":os.path.relpath(power,HERE).replace(os.sep,"/")})
    bond=HERE/"A5-bond.brep"
    rows.append({**previous["A5-bond"], "sha256":digest(bond),"brep":bond.name,
                 "note":"Six insulating adhesive pads. Board-side adhesive conforms to the revised back copper."})
    names=sorted(r["name"] for r in rows)
    assert names == sorted(["whVCC","whGND","whSCL","whSDA","drvBoard","drvParts","A5-power","A5-bond"])
    (HERE/"QA").mkdir(exist_ok=True)
    if leads is not None:
        fixed=load(leads)
        for row in fixed["add"]:
            path=(leads.parent/row["brep"]).resolve()
            assert digest(path)==row["sha256"]
            rows.append({**row,"brep":os.path.relpath(path,HERE).replace(os.sep,"/")})
        names.extend(fixed["remove"])
    save(HERE / "overlay.json", {"remove":sorted(set(names)), "add":rows})

if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for option in ("reference","work","exports","a3-parts"):
        cli.add_argument("--"+option,type=Path,required=True)
    cli.add_argument("--fixed-leads",required=True,type=Path)
    args=cli.parse_args()
    prepare(args.a3_parts,leads=args.fixed_leads)
    integrate(args.reference,args.work,args.exports,here=HERE,old=PREVIOUS,manifest=HERE/"overlay.json")
