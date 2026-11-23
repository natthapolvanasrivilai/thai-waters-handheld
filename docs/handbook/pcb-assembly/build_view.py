"""Build the offline Plate 7 assembly view from checked geometry and step instructions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = ROOT / "docs/models/R0014-PCB-assembly.html"


def build(modules):
    scene = json.loads((HERE / "scene.json").read_bytes())
    housing = scene["parts"]["housing"]
    source = "hardware/mechanical/TW-A-0001-R0014/Print/housing-battery-bay.stl"
    if (scene["assembly"] != "TW-A-0001-R0014" or housing["source"] != source
            or housing["sourceSha256"] != hashlib.sha256((ROOT / source).read_bytes()).hexdigest()):
        raise ValueError("Regenerate the scene from the current R0014 housing before packaging")
    steps = json.loads((HERE / "steps.json").read_bytes())
    all_ids = set(scene["parts"])
    covered = set()
    for i, step in enumerate(steps, 1):
        visible = set(step["visible"])
        active = set(step["active"])
        moved = set(step.get("moving", step["active"]))
        if not visible <= all_ids or not active <= visible or not moved <= visible:
            raise ValueError(f"Unknown or hidden part on step {i}")
        if ("floor" in visible or "carrier" in visible) and "housing" in visible:
            raise ValueError("The R20 fixture and integral case mount are separate trials")
        if not all(step[k] for k in ("title", "group", "instruction", "facing", "check")):
            raise ValueError(f"Incomplete instructions at step {i}")
        covered.update(active)
    required = {"A1","A2","A3","A4","A5","KEY","USB1","USB2", "bezel"}
    required.update(id for id in all_ids if len(id) == 4 and id[2] == "s")
    if not required <= covered or not steps[-1].get("checklist"):
        raise ValueError("Missing fit gauges, spacer placement or closure checks")

    binary = modules / ("@esbuild/win32-x64/esbuild.exe" if os.name == "nt" else ".bin/esbuild")
    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / "viewer.js"
        subprocess.run([str(binary),str(HERE / "viewer.js"),"--bundle","--minify","--format=iife",
                        "--target=es2020","--legal-comments=none",f"--outfile={bundle}"],
                       env={**os.environ,"NODE_PATH":str(modules)},check=True)
        js = bundle.read_text(encoding="utf8")
    license = (ROOT / "third-party/three-LICENSE.txt").read_text(encoding="utf8")
    page = (HERE / "viewer.html").read_text(encoding="utf8")
    data = json.dumps(dict(scene=scene,steps=steps),ensure_ascii=True,separators=(",",":")).replace("<","\\u003c")
    page = page.replace("@@DATA@@",data).replace("@@APPLICATION@@", "/*\n"+license+"\n*/\n"+js.replace("</script", "<\\/script"))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_bytes(page.encode("utf8"))
    print(OUTPUT, len(steps), "steps,",len(scene["parts"]),"registered parts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules",type=Path, default=ROOT/"game/src/node_modules",
                        help="node_modules from npm ci --prefix game/src")
    build(parser.parse_args().modules.resolve())
