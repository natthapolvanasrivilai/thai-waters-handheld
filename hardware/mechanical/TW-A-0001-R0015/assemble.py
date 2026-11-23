"""Replace the housing in the registered, locally retained R0014 STEP and reopen the result."""
import argparse
import gc
import gzip
import hashlib
import json
from pathlib import Path
import shutil

import cadquery as cq

HERE = Path(__file__).resolve().parent
PARENT = HERE.with_name("TW-A-0001-R0014")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, data):
    path.write_bytes((json.dumps(data, indent=2) + "\n").encode())


def measure(shape):
    b = shape.BoundingBox()
    return dict(volume_mm3=round(shape.Volume(), 5), solids=len(shape.Solids()),
                bounds_mm=[round(getattr(b, k), 4) for k in ("xmin","xmax","ymin","ymax","zmin","zmax")])


def main(original, dest):
    previous = json.loads((PARENT / "installed-step.json").read_bytes())
    if digest(original) != previous["step_sha256"]:
        raise ValueError("R0014 source STEP differs from its registered digest")
    ledger = previous["components"]
    source = cq.Assembly.load(str(original))
    assert {child.name for child in source.children} == set(ledger)
    replacement = HERE / "CAD/housing-battery-bay.brep"
    housing = cq.Shape.importBrep(str(replacement))
    new = cq.Assembly(name="TW_A_0001_R0015_supplier_cell")
    for child in source.children:
        if child.name == "Housing":
            parent = child.obj.moved(child.loc)
            assert housing.cut(parent).Volume() < .0001
            assert .1 < parent.cut(housing).Volume() < 100
            new.add(housing, name=child.name, color=child.color)
        else:
            new.add(child.obj, name=child.name, loc=child.loc, color=child.color)
    ledger["Housing"] = dict(**measure(housing), part_revision="TW-P-0001-R0012",
                             source_brep="CAD/" + replacement.name, source_sha256=digest(replacement))
    dest.mkdir(exist_ok=True, parents=True)
    installed = dest / (HERE.name + "-dressed.step")
    new.export(str(installed))
    del new, source
    gc.collect()
    restored = cq.Assembly.load(str(installed))
    assert {child.name for child in restored.children} == set(ledger)
    worst_v = worst_b = 0.
    for child in restored.children:
        a, b = measure(child.obj.moved(child.loc)), ledger[child.name]
        v = abs(a["volume_mm3"] - b["volume_mm3"])
        ext = max(abs(x-y) for x, y in zip(a["bounds_mm"], b["bounds_mm"]))
        assert a["solids"] == b["solids"] and v < max(.014, b["volume_mm3"]*3e-6) and ext < .015, child.name
        worst_v, worst_b = max(worst_v, v), max(worst_b, ext)
    packed = installed.with_suffix(".step.gz")
    with installed.open("rb") as src, packed.open("wb") as output:
        with gzip.GzipFile(filename="", fileobj=output, mode="wb", compresslevel=6, mtime=0) as archive:
            shutil.copyfileobj(src, archive)
    fingerprint = digest(installed)
    with gzip.open(packed, "rb") as check:
        assert hashlib.file_digest(check, "sha256").hexdigest() == fingerprint
    save(HERE/"installed-step.json", dict(component_count=len(ledger), step_sha256=fingerprint, components=ledger))
    save(HERE/"export-verification.json", dict(source_assembly=PARENT.name, source_step_sha256=previous["step_sha256"],
         installed_step_components=len(ledger), step_sha256=fingerprint, packed_step_sha256=digest(packed),
         unchanged_installed_members=len(ledger)-1, changed_member="Housing",
         max_roundtrip_absolute_volume_delta_mm3=round(worst_v, 6), max_bounds_delta_mm=round(worst_b, 6),
         local_dressed_step=installed.name, local_archive=packed.name, sharing="Locally retained supplier assembly."))
    print("Verified", len(ledger), "installed components", fingerprint)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("r0014_step", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.r0014_step, args.output)
