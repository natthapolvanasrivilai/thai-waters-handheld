"""Apply the verified key sequence to the archived R0013 flat-floor guide."""
import copy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
MODELS = ROOT / "docs/models"
REV = ROOT / "hardware/mechanical/TW-A-0001-R0014"
DATA = re.compile(r'(<script type="application/json" id="assemblyData">)(.*?)(</script>)', re.S)


def read_guide(revision):
    html = (MODELS / f"{revision}-PCB-assembly.html").read_text(encoding="utf8")
    match = DATA.search(html)
    return html, match, json.loads(match[2])


def main():
    _, _, old = read_guide("R0013")
    template, match, current = read_guide("R0014")
    geometry = json.loads((REV / "QA/housing-geometry.json").read_text())
    export = json.loads((REV / "export-verification.json").read_text())
    if (geometry["global_original_material_removed_mm3"] != 0
            or geometry["global_added_material_outside_two_interior_rails_mm3"] != 0
            or export["source_assembly"] != "TW-A-0001-R0013"
            or export["changed_member"] != "Housing" or export["removed_node"] != "adhH"
            or export["unchanged_installed_members"] != 153):
        raise ValueError("Recheck the R0013 power-key bay against the motion evidence")

    old_parts, new_parts = (guide["scene"]["parts"] for guide in (old, current))
    rows = [copy.deepcopy(s) for s in current["steps"] if s.get("motionPart") or s.get("inspectionPart")]
    if [s.get("motionPart") or s.get("inspectionPart") for s in rows] != ["cap", "KEY"]:
        raise ValueError("Expected the inside-loading cap and the legacy blocked-board inspection")
    if not rows[0].get("waypoints") or rows[1].get("waypoints") or "housing" in rows[1]["visible"]:
        raise ValueError("The legacy board must be inspected separately")
    for part in ("cap", "KEY", "keeper"):
        if old_parts[part]["bounds"] != new_parts[part]["bounds"]:
            raise ValueError(f"Recheck the installed alignment of {part}")
    for step in rows:
        if "A3" in step["visible"]:
            at = step["visible"].index("A3")
            step["visible"][at:at] = ["A3s1", "A3s2"]
        for field in ("instruction", "title", "check", "facing"):
            step[field] = step[field].replace("R0014", "R0013")
    first = next(i for i, s in enumerate(old["steps"]) if s["title"] == "Locate the KEY switch board")
    if old["steps"][first+1]["title"] != "Fit the retainer and power cap":
        raise ValueError("Unrecognized archived guide")
    old["steps"][first:first+2] = rows
    for step in old["steps"][first+2:]:
        step["visible"] = [part for part in step["visible"] if part not in ("cap", "KEY", "keeper")]
    checks = old["steps"][-1]["checklist"]
    key_check = next(i for i, text in enumerate(checks) if "KEY remains captured" in text)
    checks[key_check] = "Set the loose cap, KEY gauge and west retainer aside before closure. Check that A2 stays on all four shims."
    encoded = json.dumps(old, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c")
    page = template[:match.start(2)].replace("R0014", "R0013") + encoded
    page += template[match.end(2):].replace("R0014", "R0013")
    out = MODELS / "R0013-PCB-assembly-corrected.html"
    out.write_bytes(page.encode("utf8"))
    print(out, len(old["steps"]), "steps with the R0013 housing and loose A3 strips")


if __name__ == "__main__":
    main()
