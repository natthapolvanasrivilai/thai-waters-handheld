"""Generate the current private handbook from reviewed engineering data and current game."""
import argparse
import base64
import csv
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
REV=HERE.name
URL="https://github.com/natthapolvanasrivilai/thai-waters-handheld"


def load(path):
    return json.loads(path.read_text(encoding="utf8"))


def embedded(raw):
    return base64.b64encode(gzip.compress(raw,mtime=0)).decode()


def replace_script(page,name,text):
    match=re.search(fr'<script id="{name}"[^>]*>(.*?)</script>',page,re.S)
    if not match:
        raise ValueError(name)
    return page[:match.start(1)]+text+page[match.end(1):]


def generate(out):
    # Rev G overlays the pinned Rev F electronics/commercial report and supplies
    # the historical register UI. Use an isolated output without modifying its release.
    with tempfile.TemporaryDirectory() as tmp:
        preview=Path(tmp)/"prior.html"
        subprocess.run([sys.executable,str(HERE.parent/"rev-G/handbook.py"),"--exports",str(out),"--preview",str(preview)],check=True)
        page=preview.read_text(encoding="utf8")
    qa=load(HERE/"QA/candidate-specified-brims.json")
    orientation=load(HERE/"part-orientations.json")
    data=json.loads(re.search(r'<script id="reviewData"[^>]*>(.*?)</script>',page,re.S)[1])
    data["gameVersion"]=re.search(r"releaseNumber\s*=\s*(\d+)",(REPO/"firmware/WillowCreek/UpdateFeed.h").read_text())[1]
    with (REPO/"manufacturing/rev-F-review/software-evidence.csv").open(encoding="utf-8-sig",newline="") as f:
        data["softwareCases"]=list(csv.DictReader(f))
    data["firmware"]=[
        "Firmware 0.8 targets Waveshare 31137 with 16 MB flash, OPI PSRAM and two 3 MiB OTA application slots. Record the flashed binary digest and board revision on each unit.",
        "The embedded browser game and hardware firmware share the game engine. The current prototype includes the field journal, LCD weather and daily specimen tournaments. Verify actual controller, reel, touch, radio and audio behavior on hardware."
    ]
    data["decisions"][0]="Print the complete TW-A-0001-R0008 fit set in the supplied orientations. The housing and rotor need local supports. Verify the real inert assembly, layer strength and tolerances before powered closure."
    data["fitNotes"]=[
        "All 14 print files are single watertight bodies. The lowest elevated downward face is 32.37 degrees above the bed. Seven horizontal hole stations have a 45-degree tangent roof and 270-degree circular working arc.",
        "Bambu A1 PETG support falls from 13.9461 g to 4.8241 g. The housing accounts for 4.4098 g and the rotor for 0.4143 g. The complete set with specified brims takes seven hours of model print time across individual plates.",
        "Three pack variants, 16 placement corners, 15 power-key positions and the independent grip and reel motion checks passed in CAD. The maximum pack sits 0.65 mm below the bridge.",
        "Inspect the real prints for brim damage, cap travel, rotor runout, grip retention and lead clearance. Record both inert gauges before a powered closure decision."
    ]
    data["productionIntro"]="The matched R0008 print set and two gauges are ready for an inert first article. Inspect the two support-contact regions and record the actual printed fits on the traveler. Electrical measurements, supplier information, durability and production approval remain open."
    data["correlation"][-1][-1]="Record both inert gauges on the printed R0008 shell, pack allowance, harness dressing and bridge clearance before powered closure."
    data["manifest"].extend([["R0008 print orientation and SHA-256",f"hardware/mechanical/{REV}/part-orientations.json"],["R0008 CAD and slice audit",f"hardware/mechanical/{REV}/QA/README.md"]])
    data["explodedImage"]="data:image/png;base64,"+base64.b64encode((HERE/"assembly-preview.png").read_bytes()).decode()
    page=replace_script(page,"reviewData",json.dumps(data,separators=(",",":"),ensure_ascii=False).replace("<","\\u003c"))
    model=(REPO/"docs/models"/(REV+"-exploded.html")).read_bytes()
    game=(REPO/"game/Thai-Waters-play.html").read_bytes()
    page=replace_script(page,"compressedModel",embedded(model))
    page=replace_script(page,"compressedGame",embedded(game))
    page=page.replace("Rev G battery fit and assembly","R0008 print setup and assembly").replace("Rev G exploded mechanical assembly viewer","R0008 exploded mechanical assembly viewer").replace("Rev G fit print · Rev F electronics","R0008 fit print · R0002 electrical").replace("Rev G fit / Rev F electronics","R0008 fit / R0002 electrical")
    page=page.replace(" · Firmware 0.7 · 19 November 2026"," · Firmware 0.8 · 19 November 2026")
    page=page.replace("Riffle-Rev-G-exploded.html",REV+"-exploded.html")
    old=f'<p><a href="{URL}/releases/download/rev-g-fit-print/Riffle-Rev-G-fit-print.zip">Download Rev G print kit and both inert gauges</a> · <a href="{URL}/blob/main/hardware/mechanical/rev-G/README.md">Fit instructions and collision results</a></p>'
    root=f"{URL}/blob/{REV}/hardware/mechanical/{REV}"
    links=f'<p><a href="{URL}/releases/download/{REV}/{REV}-fit-print.zip">Download R0008 print kit and both inert gauges</a> · <a href="{root}/PRINT-GUIDE.md">Print guide</a> · <a href="{root}/QA/README.md">CAD and slicer evidence</a> · <a href="{URL}/releases/tag/rev-g-fit-print">Historical Rev G release</a></p>'
    assert page.count(old)==2
    page=page.replace(old,links)
    rows=[]
    for part,r in orientation.items():
        q=qa[part]
        rows.append("<tr><td>"+html.escape(part)+"</td><td>"+html.escape(r["bed_face"])+"</td><td>"+str(q["outer_brim_mm"])+"</td><td>"+format(q["support_g"],".3f")+"</td></tr>")
    setup=("<details><summary>Required build poses, brims and support removal</summary><div>"
        "<p>Load one supplied STL per plate at 100% and preserve rotation. The verified slice uses Bambu Lab A1, 0.4 mm nozzle, Generic PETG, 0.20 mm Standard, textured PEI and normal automatic supports at 30 degrees. Clear the shell receiver, encoder lands, reel well, wire tunnel and key. Clear the rotor rim and recess.</p>"
        "<table><thead><tr><th>Part</th><th>Bed contact</th><th>Outer brim, mm</th><th>Support, g</th></tr></thead><tbody>"
        +"".join(rows)+"</tbody></table><p>Verify actual pack insertion, lead dressing, key travel, reel fold and loaded rod retention on the first article. Physical fit and production release remain open.</p></div></details>")
    page=page.replace("<h2>R0008 print setup and assembly</h2>"+links,"<h2>R0008 print setup and assembly</h2>"+links+setup)
    for name,raw in [("compressedModel",model),("compressedGame",game)]:
        payload=re.search(fr'<script id="{name}"[^>]*>(.*?)</script>',page,re.S)[1]
        assert gzip.decompress(base64.b64decode(payload))==raw
    target=REPO/"docs/index.html"
    target.write_text(page,encoding="utf8")
    for name in [REV+"-handbook.html","Thai-Waters-0.8-handbook.html"]:
        shutil.copyfile(target,out/name)
    print("Current embedded game",hashlib.sha256(game).hexdigest(),"and R0008 viewer",hashlib.sha256(model).hexdigest())


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--exports",required=True,type=Path)
    generate(p.parse_args().exports.resolve())
