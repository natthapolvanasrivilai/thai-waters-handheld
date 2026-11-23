"""Round-trip the R0002 native PCB and measure the installed nominal component gaps."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
STEM = "A3-CIE-R0002"
HARNESS = HERE.parent / "harness-r0005/placed"
TRANSLATION = (-37.95, -135.15, 4.60)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def placed(path):
    shape = cq.importers.importStep(str(path)).val()
    if not shape.isValid():
        raise ValueError(f"Invalid STEP geometry in {path}")
    return shape.rotate((0, 0, 0), (0, 0, 1), 90).translate(TRANSLATION)


def bounds(shape):
    box = shape.BoundingBox()
    return [box.xmin, box.ymin, box.zmin, box.xmax, box.ymax, box.zmax]


def match(reference, candidates):
    """Find distinct solids with the same volume, face count and six installed bounds."""
    stock = list(candidates)
    max_bounds = max_volume = 0.0
    for solid in reference.Solids():
        target = bounds(solid)
        errors = [(max(abs(v - w) for v, w in zip(target, bounds(other))), i)
                  for i, other in enumerate(stock) if len(solid.Faces()) == len(other.Faces())]
        if not errors:
            raise ValueError("No matching topology in populated export")
        delta, index = min(errors)
        volume_delta = abs(solid.Volume(1e-9) - stock.pop(index).Volume(1e-9))
        if delta > 1e-5 or volume_delta > 1e-5:
            raise ValueError(f"Installed solid differs from native export by {delta}, {volume_delta}")
        max_bounds = max(delta, max_bounds)
        max_volume = max(volume_delta, max_volume)
    return dict(solids=len(reference.Solids()), max_bound_error_mm=round(max_bounds, 7),
                max_volume_error_mm3=round(max_volume, 7))


def run(cli, write_placed=False):
    board = HERE / (STEM + ".kicad_pcb")
    reports = {}
    with tempfile.TemporaryDirectory() as temp:
        cache = Path(temp)

        def export(name, *flags):
            path = cache / (name + ".step")
            subprocess.run([cli, "pcb", "export", "step", "--user-origin", "0x0mm",
                            *flags, "-o", str(path), str(board)], check=True)
            return placed(path)

        full = export("populated", "--no-dnp", "--include-pads", "--include-tracks",
                      "--no-extra-pad-thickness", "--cut-vias-in-body")
        parts = {ref: export(ref, "--no-dnp", "--no-board-body", "--component-filter", ref)
                 for ref in ("U1", "C1", "C2")}
        assert [len(p.Solids()) for p in parts.values()] == [12, 1, 1]
        substrate = export("substrate", "--board-only", "--cut-vias-in-body")
        parts_placed = cq.Compound.makeCompound(list(parts.values()))
        if write_placed:
            (HERE / "A3-substrate.step").write_bytes((cache / "substrate.step").read_bytes())
            substrate.exportBrep(str(HERE / "placed/drvBoard.brep"))
            parts_placed.exportBrep(str(HERE / "placed/drvParts.brep"))
        solids = full.Solids()
        for name, fresh in (("drvParts", parts_placed), ("drvBoard", substrate)):
            saved = cq.Shape.importBrep(str(HERE / "placed" / (name + ".brep")))
            assert saved.isValid() and len(saved.Solids()) == len(fresh.Solids())
            match(saved, fresh.Solids())
            reports[name] = match(saved, solids)
        match(placed(HERE / "A3-substrate.step"), substrate.Solids())
        fixed_names = ("A3-J1-header", "A3-J1-spacer", "A3-J1-plug", "A3-J1-TPA",
                       "wm0", "wm0-Cu", "wm1", "wm1-Cu")
        fixed = {k: cq.Shape.importBrep(str(HARNESS / (k + ".brep"))) for k in fixed_names}
        header = fixed["A3-J1-header"]
        assert len(header.Solids()) == 6
        reports["fixed_J1"] = match(header, solids)
        gaps = {}
        for ref, component in parts.items():
            gaps[ref] = {}
            for name, obj in fixed.items():
                distance = component.distance(obj)
                common = component.intersect(obj).Volume()
                if distance < 1e-5 or common > 1e-5:
                    raise ValueError(f"{ref} and {name} intersect or touch")
                gaps[ref][name] = dict(distance_mm=round(distance, 5), common_mm3=round(common, 7))
        old = cq.Shape.importBrep(str(HARNESS / "drvBoard.brep"))
        if max(abs(v - w) for v, w in zip(bounds(old), bounds(substrate))) > 1e-6:
            raise ValueError("Substrate envelope moved")

    inputs = [board, HERE / "A3-substrate.step", *(HERE / "placed" / (n + ".brep")
              for n in ("drvParts", "drvBoard")), HERE / "models/DRV2605LDGSR.step",
              HERE / "models/CIEP05P1HK0-NH-mounted.step"]
    return dict(board_sha256=digest(board), native_export_solids=len(solids),
                rotation_z_deg=90, translation_mm=TRANSLATION, installed_matches=reports,
                installed_board_bounds_mm=[round(v, 6) for v in bounds(substrate)],
                fitted_populated_bounds_mm={k: [round(v, 6) for v in bounds(s)] for k,s in parts.items()},
                seated_component_clearance=gaps,
                project_input_sha256={p.relative_to(HERE).as_posix(): digest(p) for p in inputs},
                fixed_installed_brep_sha256={n: digest(HARNESS / (n + ".brep")) for n in fixed_names})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad", required=True)
    parser.add_argument("--write-placed", action="store_true",
                        help="Regenerate the two installed BReps and bare substrate STEP.")
    options = parser.parse_args()
    result = run(options.kicad, options.write_placed)
    (HERE / "placed-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
