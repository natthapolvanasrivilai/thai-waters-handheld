"""Check the reconstructed STEP with all boards seated and both battery options (mm)."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile

import cadquery as cq

HERE = Path(__file__).resolve().parent
MECH = HERE.parents[1] / "mechanical"
NOMINAL = MECH / "TW-A-0001-R0012"


def separation(a, b):
    return math.sqrt(sum(max(0., getattr(a, axis+"min")-getattr(b, axis+"max"),
                             getattr(b, axis+"min")-getattr(a, axis+"max"))**2 for axis in "xyz"))


def assess(shape, fixed, shapes, boxes):
    box = shape.BoundingBox()
    candidates = sorted((separation(box, boxes[n]), n) for n in fixed)
    best = (float("inf"), "")
    contact = []
    for lower, name in candidates:
        if lower > best[0] + 0.00001:
            break
        other = shapes[name]
        distance = shape.distance(other)
        best = min(best, (distance, name))
        if distance < 0.00001:
            volume = shape.intersect(other).Volume()
            contact.append({"component": name, "common_volume_mm3": round(volume, 6)})
    return {"minimum_nominal_mm":round(best[0], 5), "closest":best[1], "touch_or_overlap":contact}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packed_step", type=Path)
    args = parser.parse_args()
    manifest = json.loads((NOMINAL/"installed-step.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "installed.step"
        with gzip.open(args.packed_step, "rb") as a, path.open("wb") as b:
            shutil.copyfileobj(a, b)
        with path.open("rb") as stream:
            sha = hashlib.file_digest(stream,"sha256").hexdigest()
        assert sha == manifest["step_sha256"]
        assembly = cq.Assembly.load(str(path))
    ss = {n.name:n.obj.moved(n.loc) for n in assembly.children}
    assert set(ss) == set(manifest["components"])
    import sys
    sys.path.insert(0, str(MECH / "rev-G"))
    from geometry import CX, CY, Z
    ss["cellDrawing"] = cq.Solid.makeBox(35.3,62.3,5.3,cq.Vector(CX-35.3/2,CY-62.3/2,Z))
    boxes = {k:v.BoundingBox() for k,v in ss.items()}
    new = json.loads((NOMINAL/"export-verification.json").read_text())["added_nodes"]
    checks = {}
    closed = ["Housing","Bezel","bridge","packplug","ph","serviceCover"]
    for pack in ("cellAlt", "cellDrawing"):
        checks[pack+" / changed parts"] = assess(ss[pack],new,ss,boxes)
        checks[pack+" / enclosure and pack hardware"] = assess(ss[pack],closed,ss,boxes)
    for board,own in [("A4-integration","A4-"),("A5-power","A5-")]:
        checks[board+" / installed neighbors"] = assess(ss[board], [k for k in ss if not k.startswith(own)],ss,boxes)
    wire_names = [k for k in ss if k.startswith("wh") and not k.endswith("-Cu")]
    for name in wire_names + [k for k in new if k.startswith("w1")]:
        obstacles = ["A4-integration","A5-power","A3-J1-spacer","drvBoard","drvParts",
                     "Housing","Bezel","A1-carrier","A1-population","A1-backing","bridge","cellAlt","cellDrawing"]
        checks[name+" / seated hardware"] = assess(ss[name],obstacles,ss,boxes)
    output={"installed_step_sha256":sha,"installed_members":len(assembly.children),"checks":checks,
            "scope":"Nominal, seated assembly. Each row lists the tested group. The two battery variants are mutually exclusive. Intersections are retained even below production measurement resolution. Bond strength, jacket flex, temperature, dimensional tolerance and post-life pack swelling require separate verification."}
    (HERE/"installed-fit.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    for k,v in checks.items():print(k, v, flush=True)


if __name__=="__main__":
    main()
