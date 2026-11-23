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
REVISIONS = {"R0014": "scene.json", "R0015": "scene-r0015.json", "R0016": "scene-r0016.json", "R0017": "scene-r0016.json"}
USB_QA = ROOT / "hardware/mechanical/TW-A-0001-R0015/QA/usb-indicator"


from fixed_display import apply_fixed_display


def verify_sources(report, assembly):
    if report["assembly"] != assembly:
        raise ValueError(f"Motion evidence belongs to another assembly: {report['assembly']}")
    for source, digest in report["sources_sha256"].items():
        if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Rerun motion checks for the current {source}")


def apply_usb_indicator(scene, steps, revision):
    report = json.loads((USB_QA / f"{revision}.json").read_bytes())
    verify_sources(report, scene["assembly"])
    sections = json.loads((HERE / "usb1-sections.json").read_bytes())
    section = sections["revisions"][revision]
    for part in ("housing", "USB1", "uGuide"):
        mesh = scene["parts"][part]
        if mesh["sourceSha256"] != report["sources_sha256"].get(mesh["source"]):
            raise ValueError(f"The USB1 path and scene must use the same {part} mesh")
    for path, digest in (("source", "sourceSha256"), ("orientation", "orientationSha256")):
        if report["sources_sha256"].get(section[path]) != section[digest]:
            raise ValueError("Regenerate the USB1 housing section from the checked sources")
    scene["parts"]["usbSection"] = dict(sections["meshes"][section["mesh"]],
        source=section["source"], sourceSha256=section["sourceSha256"], sectionBoundsMm=sections["bounds_mm"])

    index, = [i for i, s in enumerate(steps) if s.get("usbIndicator")]
    step = steps[index]
    points = report["waypoints_offset_mm"]
    if report["waypoint_order"] != "from above the housing to the registered seat":
        raise ValueError("Unexpected USB1 waypoint order")
    if report["status"] == "blocked":
        if points:
            raise ValueError("A blocked USB1 path cannot have installation waypoints")
        contact, collision = report["rejected_vertical"]["first_contact_offset_z_from_above_mm"]
        if not 0 < collision < contact:
            raise ValueError("Missing first contact witness for the obstructed drop")
        step.update(title="Stop above the blocked USB1 slot", inspectionPart="USB1",
                    fixedOffset=[0, 0, contact], offset=[0, 0, 0], target=[-41.8, 0, 19.8], width=32,
                    instruction=f"The section shows the gauge at the first obstruction, {contact:.2f} mm above its seat. The roof crosses the straight drop, and the slot also blocks a straight push from inside. Set the loose gauge aside.",
                    check="Look for the roof over the shelf. Leave USB1 out for the remaining dry checks. Use the R0016 housing for the side-loading trial.")
        for later in steps[index+1:]:
            later["visible"] = [part for part in later["visible"] if part != "USB1"]
    elif report["status"] == "clear":
        if (len(points) != 3 or points[0][0] != 0 or points[0][1] >= 0 or points[0][2] <= 0
                or points[1] != [0, points[0][1], 0] or points[2] != [0, 0, 0]
                or report["above_rim_start_gap_mm"] <= 0):
            raise ValueError("Update the USB1 instructions for the measured route")
        step.update(motionPart="USB1", start=100, waypoints=list(reversed(points)))
        step["instruction"] = step["instruction"].format(approach=-points[0][1], drop=points[0][2])
        step["check"] = step["check"].format(gap=report["seated_guide_gap_mm"])
    else:
        raise ValueError("USB1 disposition is unknown")
    display, = [s for s in steps if s["title"] == "Lower the display onto its four seats"]
    display["check"] += " Use loose, unwired gauges. The soldered lamp leads cannot span the pictured 18 mm display lift."


def apply_power_key_paths(steps, qa_dir, parts=None):
    """Attach the measured removal waypoints. The viewer plays them backwards to install."""
    def read_evidence(name):
        report = json.loads((qa_dir / name).read_bytes())
        verify_sources(report, qa_dir.parents[1].name)
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
    housing_revision = "R0016" if revision == "R0017" else revision
    assembly = f"TW-A-0001-{housing_revision}"
    housing = scene["parts"]["housing"]
    source = f"hardware/mechanical/{assembly}/Print/housing-battery-bay.stl"
    if (scene["assembly"] != assembly or housing["source"] != source
            or housing["sourceSha256"] != hashlib.sha256((ROOT / source).read_bytes()).hexdigest()):
        raise ValueError(f"Regenerate the scene from the current {revision} housing before packaging")
    steps = json.loads((HERE / "steps.json").read_text(encoding="utf8").replace("@@REVISION@@",housing_revision))
    if revision in ("R0016", "R0017"):
        step = next(item for item in steps if item["title"] == "Orient the open housing")
        step["check"] += " This historical view shows the thin R0005 rotor. Use the reinforced TW-P-0007-R0006 rotor from plate 2 of the TW-A-0003-R0002 print kit."
    apply_power_key_paths(steps, ROOT / f"hardware/mechanical/{assembly}/QA/power-key",scene["parts"])
    apply_usb_indicator(scene, steps, housing_revision)
    if revision == "R0017":
        kit = ROOT / "hardware/mechanical/TW-A-0001-R0017"
        report = json.loads((kit / "QA/fit.json").read_bytes())
        cap = json.loads((kit / "QA/viewer-cap.json").read_bytes())
        if (hashlib.sha256((ROOT / cap["source"]).read_bytes()).hexdigest()
                != cap["sourceSha256"] or cap["sourceSha256"] != report["cap_stl_sha256"]
                or report["source_housing_sha256"] != hashlib.sha256(
                    (ROOT / source).parents[1].joinpath("CAD/housing-battery-bay.brep").read_bytes()).hexdigest()):
            raise ValueError("The keyed cap and its housing must match the checked pair")
        if (any(q["common_mm3"] for q in report["insertion_and_press"].values())
                or min(q["gap_mm"] for q in report["board_and_keeper_install"].values()) <= 0):
            raise ValueError("Keyed cap or subsequent board insertion is obstructed")
        scene["assembly"] = kit.name
        scene["parts"]["cap"] = cap
        step, = [s for s in steps if s.get("motionPart") == "cap"]
        step["title"] = "Match the keyed cap to the opening"
        step["facing"] = "Point the single rounded square corner toward the matching corner in the opening (+X, +Z). Keep the wide flange inside."
        step["check"] = "The face should follow the outline of the hole. Hold the cap at its seat until the switch board and keeper are fitted. With the real switch, press at the centre and edges and check that it returns freely."
        step["instruction"] = "The view opens at the alignment point, 2.50 mm inside the hole. Slide the keyed cap straight outward to seat it. To see how to reach this position from above, move the slider to the far right."
        step["start"] = 100 * 2.5 / 26.5
    if revision in ("R0016", "R0017"):
        apply_fixed_display(scene, steps, ROOT)
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
