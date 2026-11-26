"""Verify the editable project, both native jobs, USB slot, key flanks and integral rails."""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict

from lxml import etree as ET
import numpy as np
from shapely.geometry import Polygon
import trimesh

from prepare import (HERE, PREV, PROJECT, PARENT, BASELINE_HASH, STL, CORE, MODEL, SETTINGS, HOUSING,
                     BLOCKER_ID, BLOCKER_LOW, BLOCKER_HIGH, LAYER_CONFIG, digest, value)
from usb_paths import usb_witnesses
from check_project import compact, inspect_run
from rail_paths import measure, check, footprints, window
from path_evidence import inspect

sys.path.insert(0, str(PREV))
from verify import witnesses as key_witnesses

QA = HERE / "QA"
RAILS = HERE.parent.with_name("TW-A-0001-R0014") / "Printing/QA/rail-witnesses.json"


def package():
    assert digest(PARENT) == BASELINE_HASH
    source = trimesh.load_mesh(STL)
    with ZipFile(PROJECT) as z, ZipFile(PARENT) as parent:
        assert z.testzip() is None
        assert set(z.namelist()) - set(parent.namelist()) == {LAYER_CONFIG}
        assert not set(parent.namelist()) - set(z.namelist())
        assert {n for n in parent.namelist() if parent.read(n) != z.read(n)} == {HOUSING, MODEL, SETTINGS}
        config = ET.fromstring(z.read(SETTINGS))
        baseline = ET.fromstring(parent.read(SETTINGS))
        row = config.find("object[@id='2']")
        part = row.find("part[@id='1']")
        blocker = row.find(f"part[@id='{BLOCKER_ID}'][@subtype='support_blocker']")
        assert blocker is not None
        row.remove(blocker)
        for doc in (baseline, config):
            for element in doc.xpath("./object[@id='2']//*[@face_count]"):
                element.set("face_count", "normalized")
        assert compact(config) == compact(baseline)
        root = ET.fromstring(z.read(MODEL))
        addition = root.find(f".//{CORE}object[@id='2']//{CORE}component[@objectid='{BLOCKER_ID}']")
        addition.getparent().remove(addition)
        assert compact(root) == compact(ET.fromstring(parent.read(MODEL)))
        offset = [float(value(part, "source_offset_" + axis)) for axis in "xyz"]
        resources = ET.fromstring(z.read(HOUSING))
        def coordinates(obj_id):
            obj = resources.find(f".//{CORE}object[@id='{obj_id}']")
            return np.array([[float(v.get(k)) for k in "xyz"] for v in obj.findall(f".//{CORE}vertex")]) + offset
        obj = resources.find(f".//{CORE}object[@id='1']")
        triangles = np.array([[int(t.get(k)) for k in ("v1","v2","v3")] for t in obj.findall(f".//{CORE}triangle")])
        assert np.array_equal(triangles, source.faces)
        error = abs(coordinates("1") - source.vertices).max()
        assert error < 1e-7
        blocker_vertices = coordinates(BLOCKER_ID) - [0,0,3.200001004]
        np.testing.assert_allclose([blocker_vertices.min(0),blocker_vertices.max(0)], [BLOCKER_LOW,BLOCKER_HIGH], atol=1e-7)
        return {"mesh_faces": len(triangles), "max_native_vertex_error_mm": float(error),
                "blocker_installed_bounds_mm": [BLOCKER_LOW.tolist(), BLOCKER_HIGH.tolist()],
                "local_height_settings": z.read(LAYER_CONFIG).decode(),
                "other_object_placements_and_settings_identical": True}


def audit_plate(folder, plates):
    audit = inspect_run(folder, plates, RAILS)
    gcode = folder / "plate_1.gcode"
    rails = measure(gcode)
    check(rails)
    key = key_witnesses(gcode)
    for result in key.values():
        assert result["gap_model_min_max_mm2"] == [0,0] and result["maximum_gap_support_mm2"] == 0
        assert result["minimum_wall_witness_model_mm2"] > .20
    usb = usb_witnesses(gcode)
    for phase in usb["route"].values():
        assert all(not r["occupied_build_layers_mm"] for r in phase.values()), usb
    for feature in usb["features"].values():
        assert feature["min_max_native_model_coverage_fraction"][0] > .99, usb
    return audit, {"usb": usb, "key_flanks": key, "both_A3_rails": "pass"}


def roof_and_seat(gcode):
    trace = defaultdict(list)
    layers = footprints(gcode, window(-45,-13,-39,5), 14.4, 18.6, trace)
    roof = window(-42.56,-8.6,-41.26,2.405)
    unbacked = roof.difference(layers[18.0].get("model", Polygon()))
    spans = [line.intersection(unbacked).length for line in trace[18.2]]
    assert 1.25 < max(spans) < 1.32
    bearing = window(-42.04,-1.9,-41.55,1.9)
    coverage = lambda z: layers[z].get("model",Polygon()).intersection(bearing).area / bearing.area
    assert coverage(14.7) > .99 and coverage(14.8) < .001
    assert coverage(18) < .001 and coverage(18.2) > .99
    return {"bearing_top_build_z_mm": 14.7, "central_roof_underside_build_z_mm": 18.0,
            "vertical_margin_for_3_20_mm_board_between_bead_layers_mm": .10,
            "first_roof_layer_checked_build_z_mm": 18.2,
            "longest_individual_centerline_inside_unsupported_slot_mm": round(max(spans),6),
            "checked_installed_xy_mm": [-42.56,-8.6,-41.26,2.405]}


def ledge_support(gcode):
    # This entire first model island lies within the installed ROI. Support
    # ends at Z13.8; one 0.20 mm release gap precedes the 14.0–14.2 model bead.
    region = window(-43.5,-3.3,-40.1,3.45)
    layers = footprints(gcode, region, 13.8, 14.2)
    ledge = layers[14.2]["model"]
    backed = layers[13.8]["support"].intersection(ledge)
    return {"first_ledge_build_z_mm":14.2,"ledge_model_mm2":round(ledge.area,5),
            "support_build_z_mm":13.8,"projected_ledge_support_mm2":round(backed.area,5),
            "covered_fraction":round(backed.area / ledge.area,5)}


def main(scratch, control):
    QA.mkdir(exist_ok=True)
    identity = package()
    all_run, first = audit_plate(scratch/"all", list(range(1,8)))
    reopened, second = audit_plate(scratch/"reopen", [1])
    assert len(all_run["objects"]) == 33 and len(reopened["objects"]) == 1 and first == second
    assert all_run["features"] == reopened["features"]
    gcode = scratch/"reopen/plate_1.gcode"
    section = roof_and_seat(gcode)
    assert section == roof_and_seat(scratch/"all/plate_1.gcode")
    context,_ = inspect(gcode, True, focus={"385"})
    control_job = control/"plate_1.gcode"
    with ZipFile(control/"auto.3mf") as auto, ZipFile(PROJECT) as release:
        auto_mesh = ET.fromstring(auto.read(HOUSING)).find(f".//{CORE}object[@id='1']")
        new_mesh = ET.fromstring(release.read(HOUSING)).find(f".//{CORE}object[@id='1']")
        assert compact(auto_mesh) == compact(new_mesh)
    old_profile = usb_witnesses(control_job)
    ledge = ledge_support(gcode)
    assert ledge == ledge_support(scratch/"all/plate_1.gcode") == ledge_support(control_job)
    assert ledge["projected_ledge_support_mm2"] > 8
    islands = context["385"]["model_component_backing"]["fully_unbacked_components"]
    assert len(islands) == 1 and islands[0]["z"] == 14.2
    assert old_profile["route"]["slide_to_stop"]["support"]["peak_in_section_mm2"] > 5
    assert old_profile["route"]["slide_to_stop"]["model"]["occupied_build_layers_mm"] == [14.8]
    with tempfile.TemporaryDirectory() as tmp, ZipFile(PREV/"QA/plate-1-reopen.sliced.3mf") as archive:
        old = Path(tmp)/"control.gcode"
        old.write_bytes(archive.read("Metadata/plate_1.gcode"))
        previous = usb_witnesses(old)
        prev_sha = digest(old)
        assert len(previous["route"]["slide_to_stop"]["model"]["occupied_build_layers_mm"]) > 10
    for name in ("all","reopen"):
        shutil.copyfile(scratch/name/"result.json", QA/f"native-{name}.json")
    shutil.copyfile(scratch/"reopen/sliced.3mf", QA/"plate-1-reopen.sliced.3mf")
    raw = json.loads((QA/"native-all.json").read_bytes())
    assert all(not p["warning_message"] for p in raw["sliced_plates"])
    data = {"assembly": HERE.parent.name, "editable_project_sha256": digest(PROJECT), "parent_project_sha256": BASELINE_HASH,
            "print_mesh_sha256": digest(STL), "native_project_verification": identity,
            "engine": gcode.read_text(encoding="utf8").splitlines()[1].strip("; "),
            "plates": [{"id":p["id"], "objects":len(p["objects"]), "seconds":round(p["total_predication"]),
                        "grams":round(sum(f["total_used_g"] for f in p["filaments"]),2)} for p in raw["sliced_plates"]],
            "all_plate_extrusion":all_run,"reopened_plate_extrusion":reopened,
            "matched_both_native_runs":first, "roof_and_bearing":section,
            "west_ledge_identical_to_full_automatic_support_control":ledge,
            "r0015_control_gcode_sha256":prev_sha, "r0015_control":previous,
            "automatic_support_control_project_sha256":digest(control/"auto.3mf"),
            "automatic_support_control_gcode_sha256":digest(control_job), "automatic_support_control":old_profile,
            "reopened_gcode_sha256":digest(gcode), "reopened_sliced_3mf_sha256":digest(QA/"plate-1-reopen.sliced.3mf"),
            "housing_extrusion_context":context["385"],
            "scope":"Nominal deposited-bead footprints. Bridge sag, bead-width variation, support removal, actual retention and inert fit await a physical print."}
    (QA/"project-check.json").write_bytes((json.dumps(data,indent=2)+"\n").encode())
    print("Verified editable project, 33 objects, fixed route, roof and retained features.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scratch",type=Path)
    parser.add_argument("control",type=Path)
    args = parser.parse_args()
    main(args.scratch, args.control)
