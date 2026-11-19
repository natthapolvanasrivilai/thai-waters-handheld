"""Create the standalone engineering inspection page using the verified STEP membership."""
import argparse
import base64
import json
from pathlib import Path
import re
import shutil
import zlib

import cadquery as cq
import numpy as np

from assembly import HARNESS, ROOT
from build import HERE, OLD, LEGACY, digest, load, save

def section(key):
    return re.compile(r'(<script type="application/json" id="'+key+r'">)(.+?)(</script>)',re.S)

def replace(page,key,value):
    return section(key).sub(lambda m:m[1]+json.dumps(value,ensure_ascii=False,separators=(",",":"))+m[3],page,count=1)

def mesh(shape):
    vertices,faces=shape.tessellate(.035,.10)
    def pack(arr):
        return base64.b64encode(zlib.compress(arr.tobytes(),7)).decode()
    return dict(v=pack(np.rint(np.array([p.toTuple() for p in vertices])*100).astype("<i2")),
                t=pack(np.array(faces,dtype="<u4")))

def viewer(exports):
    folder=ROOT/"docs/models"
    page=(folder/(LEGACY.name+"-exploded.html")).read_text(encoding="utf8")
    rows={r["id"]:r for r in json.loads(section("geometry").search(page)[2])}
    cover=next(r for r in load(OLD/"assembly-parts.json") if r["id"]=="serviceCover")
    cover_source=ROOT/cover["source"]
    assert digest(cover_source)==cover["geometrySha256"]
    rows["serviceCover"]={**cover,**mesh(cq.Shape.importBrep(str(cover_source)))}
    ledger=load(HERE/"installed-step.json")["components"]
    revised=load(HARNESS)
    replaced={key:rows.pop(key) for key in revised["remove"]}
    for change in revised["add"]:
        key=change["name"]
        source=HARNESS.parent/change["brep"]
        assert digest(source)==change["sha256"], key
        shape=cq.Shape.importBrep(str(source))
        assert abs(ledger[key]["volume_mm3"]-shape.Volume())<.001
        name=change.get("label",key)
        previous=replaced.get(key,{})
        rows[key]=dict(id=key,name=name,ref=change.get("ref","A3"),group=change.get("group","Wiring"),kind="R0004 integration CAD",
                      stage=change.get("stage",previous.get("stage",4)),delta=previous.get("delta",[10,5,-14]),note=change.get("note",name),color=change["color"],source=source.relative_to(ROOT).as_posix(),
                      option=change.get("option",previous.get("option","haptic")),added=True,productEligible=True,geometrySha256=digest(source),solids=ledger[key]["solids"],
                      bounds_mm=ledger[key]["bounds_mm"],**mesh(shape))
    rows["Housing"]["note"]="Receiver-down housing print. Both dovetail lips and their stop start on the bed; the lower service cover fits the separate board-key opening."
    assert {r["id"] for r in rows.values() if r["productEligible"]}==set(ledger)
    checks=json.loads(section("checks").search(page)[2])
    checks.update(revision="R0011",reference="Historical Rev G battery comparisons",r0011_print=load(HERE/"QA/housing-toolpaths.json"))
    # The historical Harness view whitelisted only its old board name. Include
    # the installed connector, contacts and their carrier in the selectable scene.
    harness_filter='Et==="wiring"?i.group==="Wiring"||'
    assert page.count(harness_filter)==1
    page=page.replace(harness_filter,'Et==="wiring"?["Wiring","Haptics"].includes(i.group)||')
    transparent='Et==="wiring"&&e.group!=="Wiring"'
    assert page.count(transparent)==1
    page=page.replace(transparent,'Et==="wiring"&&!["Wiring","Haptics"].includes(e.group)')
    page=replace(replace(page,"geometry",list(rows.values())),"checks",checks)
    page=page.replace("R0009 · Assembly inspection","R0011 · Assembly inspection").replace(">R0009</span>",">R0011</span>")
    page=page.replace("R0009 USB and speaker fit results are linked in the print kit.","R0011 receiver toolpaths and registered housing fit evidence accompany this release.")
    page=page.replace('<summary>Fit evidence</summary>',
                      '<summary>Fit evidence</summary><p>The dressed model includes the selected haptic interconnect and the covered lower service opening. Circuit changes proposed for the controller PCB require layout, enclosure clearance and thermal checks.</p>')
    save(HERE/"assembly-parts.json",[{k:v for k,v in row.items() if k not in ("v","t","c")} for row in rows.values()])
    path=folder/(HERE.name+"-exploded.html")
    path.write_text(page,encoding="utf8")
    exports.mkdir(exist_ok=True,parents=True)
    shutil.copyfile(path,exports/path.name)
    reloaded=json.loads(section("geometry").search(path.read_text(encoding="utf8"))[2])
    assert reloaded==list(rows.values())
    print(path,len(rows),"inspection records")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exports",type=Path,required=True)
    viewer(p.parse_args().exports)
