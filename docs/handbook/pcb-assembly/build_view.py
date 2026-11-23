"""Build the offline Plate 7 assembly view from checked geometry and step instructions."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REVISIONS = {"R0014": "scene.json", "R0015": "scene-r0015.json"}


def apply_power_key_paths(steps, qa_dir, parts=None):
    """Attach the measured removal waypoints. The viewer plays them backwards to install."""
    def read_evidence(name):
        report = json.loads((qa_dir / name).read_bytes())
        if report["assembly"] != qa_dir.parents[1].name:
            raise ValueError(f"{name} belongs to another assembly")
        for source, digest in report["sources_sha256"].items():
            if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != digest:
                raise ValueError(f"Rerun {name} checks for the current {source}")
        return report

    cap = read_evidence("cap-path.json")
    switch = read_evidence("key-path.json")
    if parts is not None:
        for part, report in [("housing", cap), ("cap", cap), ("housing", switch),
                             ("cap", switch), ("KEY", switch), ("keeper", switch)]:
            mesh = parts[part]
            if mesh["sourceSha256"] != report["sources_sha256"].get(mesh["source"]):
                raise ValueError(f"The scene and path checker use different meshes for {part}")
    motions = {"cap": cap, "KEY": switch["pcb"], "keeper": switch["keeper"]}
    pcb_status = switch["pcb"]["status"]
    if pcb_status not in ("clear", "blocked") or switch["keeper"]["status"] != "clear":
        raise ValueError("Power-key installation evidence is incomplete")
    blocked = pcb_status == "blocked"
    if blocked and switch["pcb"]["removal_offsets_mm"]:
        raise ValueError("A blocked board cannot have an approved insertion path")
    installed, placements, output = [], [], []
    skipped = False
    for step in steps:
        part = step.get("motionPart")
        inspection = step.pop("blockedInspection", None)
        if blocked and part == "KEY":
            if not inspection or inspection["inspectionPart"] != part:
                raise ValueError("Missing inspection instructions for the blocked KEY board")
            output.append(inspection)
            installed.clear()  # User removes the loose cap at the stop.
            skipped = True
            continue
        if skipped:
            if part == "keeper":
                continue
            step["visible"] = [id for id in step["visible"] if id not in motions]
            if "checklist" in step:
                step["checklist"] = [text.replace("KEY remains captured",
                    "The power-key bay remains empty") for text in step["checklist"]]
        if part:
            if (part not in motions or step["active"] != [part]
                    or step.get("moving", [part]) != [part] or step.get("start") != 100
                    or "offset" in step or "waypoints" in step):
                raise ValueError(f"Invalid power-key motion step: {part}")
            points = motions[part]["removal_offsets_mm"]
            if (len(points) < 2 or points[0] != [0, 0, 0]
                    or any(len(point) != 3 or not all(math.isfinite(n) for n in point) for point in points)
                    or any(a == b for a, b in zip(points, points[1:]))):
                raise ValueError(f"Invalid measured path: {part}")
            step["waypoints"] = points
            if part == "cap":
                if (len(points) != 3 or points[1][0] != 0 or points[1][1] >= 0 or points[1][2] != 0
                        or points[2][:2] != points[1][:2] or points[2][2] <= 0):
                    raise ValueError("Update the cap instructions for the new approach geometry")
                step["instruction"] = step["instruction"].format(setback=-points[1][1], drop=points[2][2])
                step["check"] = step["check"].format(gap=cap["insertion_legs"]["slide"]["cad_envelope_gap_mm"])
            else:
                if len(points) != 2 or points[1][:2] != [0, 0] or points[1][2] <= 0:
                    raise ValueError(f"Update the {part} instructions for the new approach geometry")
                step["instruction"] = step["instruction"].format(drop=points[1][2])
            installed.append(part)
            placements.append(part)
        if "housing" in step["visible"]:
            visible = set(step["visible"]) & motions.keys()
            if visible != set(installed):
                raise ValueError(f"Incorrect power-key assembly state at {step['title']}")
        output.append(step)
    if placements != (["cap"] if blocked else list(motions)) or skipped != blocked:
        raise ValueError("Power-key sequence differs from the verified assembly sequence")
    steps[:] = output


def build(modules, revision):
    scene = json.loads((HERE / REVISIONS[revision]).read_bytes())
    assembly = f"TW-A-0001-{revision}"
    housing = scene["parts"]["housing"]
    source = f"hardware/mechanical/{assembly}/Print/housing-battery-bay.stl"
    if (scene["assembly"] != assembly or housing["source"] != source
            or housing["sourceSha256"] != hashlib.sha256((ROOT / source).read_bytes()).hexdigest()):
        raise ValueError(f"Regenerate the scene from the current {revision} housing before packaging")
    steps = json.loads((HERE / "steps.json").read_text(encoding="utf8").replace("@@REVISION@@",revision))
    apply_power_key_paths(steps, ROOT / f"hardware/mechanical/{assembly}/QA/power-key",scene["parts"])
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
    page = (HERE / "viewer.html").read_text(encoding="utf8").replace("@@REVISION@@",revision)
    data = json.dumps(dict(scene=scene,steps=steps),ensure_ascii=True,separators=(",",":")).replace("<","\\u003c")
    page = page.replace("@@DATA@@",data).replace("@@APPLICATION@@", "/*\n"+license+"\n*/\n"+js.replace("</script", "<\\/script"))
    output = ROOT / f"docs/models/{revision}-PCB-assembly.html"
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(page.encode("utf8"))
    print(output, len(steps), "steps,",len(scene["parts"]),"registered parts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules",type=Path, default=ROOT/"game/src/node_modules",
                        help="node_modules from npm ci --prefix game/src")
    parser.add_argument("--revision",choices=REVISIONS,help="Build just one revision (default: both)")
    args = parser.parse_args()
    for revision in ([args.revision] if args.revision else REVISIONS):
        build(args.modules.resolve(),revision)
