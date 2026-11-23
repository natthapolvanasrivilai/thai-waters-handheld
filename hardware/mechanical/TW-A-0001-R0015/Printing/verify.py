"""Check native 3MF identity, relieved key-flank bead footprints, and all deposited components."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

from lxml import etree as ET
import numpy as np
from shapely.geometry import Polygon
import trimesh

from prepare import HERE, PREV, BASELINE_HASH, PROJECT, PARENT, STL, HOUSING, SETTINGS, digest, value
from check_project import compact, inspect_run
from rail_paths import DX, DY, footprints, measure, check, window
from path_evidence import inspect

QA = HERE / "QA"
LAYERS = [n / 5 for n in range(101, 156)]  # Installed Z17.0..27.8 above the circular counterbore.
FLANKS = {"west":(-38.85,-38.25), "east":(-33.75,-33.15)}
GAP_Y = (32.54,32.68)
WALL_Y = (32.85,33.19)


def editable():
    assert digest(PARENT) == BASELINE_HASH
    with ZipFile(PARENT) as a, ZipFile(PROJECT) as b:
        assert b.testzip() is None and set(a.namelist()) == set(b.namelist())
        assert {k for k in b.namelist() if a.read(k) != b.read(k)} == {HOUSING, SETTINGS}
        configs = [ET.fromstring(z.read(SETTINGS)) for z in (a,b)]
        for cfg in configs:
            for node in cfg.xpath("./object[@id='2']//*[@face_count]"):
                node.set("face_count", "normalized")
        assert compact(configs[0]) == compact(configs[1])
        housing = ET.fromstring(b.read(HOUSING))
        vertices = np.array([[float(v.get(k)) for k in "xyz"] for v in housing.findall(".//{*}vertex")])
        faces = np.array([[int(f.get(k)) for k in ("v1","v2","v3")] for f in housing.findall(".//{*}triangle")])
        part = configs[1].find("object[@id='2']/part")
        offset = np.array([float(value(part,"source_offset_"+k)) for k in "xyz"])
        mesh = trimesh.load_mesh(STL)
        assert np.array_equal(faces, mesh.faces)
        vertex_error = float(abs(vertices + offset - mesh.vertices).max())
        assert vertex_error < .0000001
        return dict(native_faces=len(faces), maximum_vertex_axis_error_mm=vertex_error,
                    changed_archive_members=[HOUSING, SETTINGS],
                    settings_diff="Only two housing face-count fields change. All object IDs, materials, placements and plate settings match R0014.")


def witnesses(gcode):
    # Measure actual swept bead area in two small windows intersecting the
    # switch rim at X +/- 2.25..2.85 from center. A second pair confirms wall
    # material immediately behind the relieved region, on all 55 layers.
    layers = footprints(gcode, window(-39.2,32.4,-32.8,33.4), LAYERS[0], LAYERS[-1])
    assert all(z in layers for z in LAYERS)
    results = {}
    for name, (x0,x1) in FLANKS.items():
        gap = window(x0,GAP_Y[0],x1,GAP_Y[1])
        stock = window(x0,WALL_Y[0],x1,WALL_Y[1])
        area = lambda z, role, w: layers[z].get(role, Polygon()).intersection(w).area
        model = [area(z,"model",gap) for z in LAYERS]
        support = [area(z,"support",gap) for z in LAYERS]
        wall = [area(z,"model",stock) for z in LAYERS]
        results[name] = dict(gap_model_min_max_mm2=[round(min(model),6),round(max(model),6)],
                             maximum_gap_support_mm2=round(max(support),6),
                             minimum_wall_witness_model_mm2=round(min(wall),6))
    return results


def verify(scratch):
    identity = editable()
    all_run = inspect_run(scratch/"all",list(range(1,8)),PREV/"QA/rail-witnesses.json")
    reopen = inspect_run(scratch/"reopen",[1],PREV/"QA/rail-witnesses.json")
    assert len(all_run["objects"]) == 33 and len(reopen["objects"]) == 1
    assert all_run["features"] == reopen["features"]
    actual = []
    for run in ("all","reopen"):
        job = scratch / run
        path = job / "plate_1.gcode"
        rail = measure(path)
        check(rail)
        actual.append(witnesses(path))
        shutil.copyfile(job/"result.json",QA/f"native-{run}.json")
    assert actual[0] == actual[1]
    for row in actual[0].values():
        assert row["gap_model_min_max_mm2"] == [0,0] and not row["maximum_gap_support_mm2"]
        assert row["minimum_wall_witness_model_mm2"] > .20
    with tempfile.TemporaryDirectory() as temp, ZipFile(PREV/"QA/plate-1-reopen.sliced.3mf") as z:
        prior = Path(temp)/"baseline.gcode"
        prior.write_bytes(z.read("Metadata/plate_1.gcode"))
        control = witnesses(prior)
        control_digest = digest(prior)
        assert all(v["gap_model_min_max_mm2"][0] > .083 for v in control.values())
    # Audit the whole plate for isolated starts. The inherited west USB ledge
    # is the only elevated feature whose model starts entirely on support.
    context,_ = inspect(scratch/"reopen/plate_1.gcode",True,focus={"385"})
    body = context["385"]
    islands = body["model_component_backing"]["fully_unbacked_components"]
    assert len(islands)==1 and islands[0]["z"] == 14.2 and islands[0]["bbox"][0] < 82
    shutil.copyfile(scratch/"reopen/sliced.3mf",QA/"plate-1-reopen.sliced.3mf")
    raw = json.loads((QA/"native-all.json").read_bytes())
    assert all(not p["warning_message"] for p in raw["sliced_plates"])
    project = dict(assembly=HERE.parent.name, editable_project_sha256=digest(PROJECT),
        source_project_sha256=BASELINE_HASH, print_mesh_sha256=digest(STL), package_check=identity,
        engine=(scratch/"reopen/plate_1.gcode").read_text(encoding="utf8").splitlines()[1].strip("; "),
        plates=[dict(plate=p["id"],objects=len(p["objects"]),warning=p["warning_message"],
                     total_time_s=round(p["total_predication"]),
                     total_filament_g=round(sum(f["total_used_g"] for f in p["filaments"]),2))
                for p in raw["sliced_plates"]],
        expected_instances_verified=33, entire_native_all_extrusion_audit=all_run,
        independent_plate1_extrusion_audit=reopen, retained_A3_rail_witnesses_pass=True,
        installed_to_commanded_translation_mm=[DX,DY,3.200001004],
        measured_build_z_mm=LAYERS, switch_flank_installed_x_mm=FLANKS, gap_installed_y_mm=GAP_Y,
        retained_wall_installed_y_mm=WALL_Y, baseline_r0014_gcode_sha256=control_digest,
        baseline_witnesses=control, all_plates_and_reopen_witnesses=actual[0],
        reopened_plate1_gcode_sha256=digest(scratch/"reopen/plate_1.gcode"),
        reopened_slice_sha256=digest(QA/"plate-1-reopen.sliced.3mf"), whole_housing_context=body,
        scope="Digital native extrusion footprints; physical support removal, button travel and switch seating await an inert first print.")
    (QA/"project-check.json").write_text(json.dumps(project,indent=2)+"\n",encoding="utf8")
    print("Verified 33 instances, 55 layers per flank, retained wall and A3 witnesses",actual[0],flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scratch",type=Path)
    verify(parser.parse_args().scratch)
