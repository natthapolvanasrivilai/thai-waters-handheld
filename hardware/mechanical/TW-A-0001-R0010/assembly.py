"""Extend the hash-checked R0009 dressed STEP, then read the new assembly back."""
import argparse
import gc
import gzip
import json
from pathlib import Path
import shutil

import cadquery as cq

from build import BASE, HERE, digest, write_json


def bounds(s):
    b = s.BoundingBox()
    return [round(getattr(b, k), 4) for k in ("xmin","xmax","ymin","ymax","zmin","zmax")]


def read_step(source, target):
    with gzip.open(source, "rb") as inp, target.open("wb") as out:
        shutil.copyfileobj(inp, out)
    return cq.Assembly.load(str(target))


def build_step(work, exports, prior):
    work.mkdir(exist_ok=True, parents=True)
    exports.mkdir(exist_ok=True, parents=True)
    original = json.loads((BASE / "installed-step.json").read_text())
    expected = json.loads((BASE / "export-verification.json").read_text())
    assert digest(prior) == expected["packed_step_sha256"]
    assembly = read_step(prior, work / "source.step")
    assert digest(work / "source.step") == original["step_sha256"]
    assert {node.name for node in assembly.children} == set(original["components"])
    # Re-register the imported children to preserve every installed local pose
    # and supplier colour, with a new root assembly identity.
    result = cq.Assembly(name="TW_A_0001_R0010_supplier_cell")
    for node in assembly.children:
        result.add(node.obj, name=node.name, color=node.color, loc=node.loc)
    cover = cq.Shape.importBrep(str(HERE / "CAD/service-cover.brep"))
    result.add(cover, name="serviceCover", color=cq.Color("#91a994"))
    expected_parts = original["components"]
    expected_parts["serviceCover"] = dict(volume_mm3=round(cover.Volume(),5), solids=1, bounds_mm=bounds(cover))
    output = work / (HERE.name + "-dressed.step")
    result.export(str(output))
    del result, assembly
    gc.collect()
    packed = exports / (HERE.name + "-dressed.step.gz")
    with output.open("rb") as inp, packed.open("wb") as out:
        with gzip.GzipFile(filename="", fileobj=out, mode="wb", compresslevel=6, mtime=0) as stream:
            shutil.copyfileobj(inp, stream)
    actual = read_step(packed, work / "roundtrip.step")
    assert digest(output) == digest(work / "roundtrip.step")
    assert {node.name for node in actual.children} == set(expected_parts)
    worst_volume = worst_dimension = 0.
    shapes = {}
    for node in actual.children:
        shape = node.obj.moved(node.loc)
        ref = expected_parts[node.name]
        dv = abs(shape.Volume() - ref["volume_mm3"])
        db = max(abs(a-b) for a,b in zip(bounds(shape),ref["bounds_mm"]))
        assert len(shape.Solids()) == ref["solids"] and dv <= max(.014,ref["volume_mm3"]*3e-6) and db <= .015, (node.name,dv,db)
        worst_volume = max(worst_volume,dv)
        worst_dimension = max(worst_dimension,db)
        shapes[node.name] = shape
    write_json(HERE / "installed-step.json", dict(component_count=len(expected_parts), step_sha256=digest(output), components=expected_parts))
    write_json(HERE / "export-verification.json", dict(source_assembly=BASE.name, source_step_sha256=original["step_sha256"],
               installed_step_components=len(shapes), step_sha256=digest(output), packed_step_sha256=digest(packed),
               max_roundtrip_absolute_volume_delta_mm3=round(worst_volume,6), max_bounds_delta_mm=round(worst_dimension,6)))
    from verify_cover import measure
    write_json(HERE / "QA/service-cover.json", measure(shapes))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exports", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args=parser.parse_args()
    build_step(args.work,args.exports,args.reference)


