"""Rebuild the four CviLux assembly imports from the adjacent supplier IGES files."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.IGESControl import IGESControl_Reader
from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Solid


SOURCE = Path(__file__).resolve().parent


def derive(source, work):
    reader = IGESControl_Reader()
    reader.ReadFile(str(source))
    if reader.TransferRoots() == 0:
        raise ValueError(f"No transferable IGES geometry in {source.name}")
    surfaces = cq.Shape.cast(reader.OneShape())
    tolerance_mm = 0.0001 if source.stem == "CIEP05C0010" else 0.001
    sewing = BRepBuilderAPI_Sewing(tolerance_mm)
    for face in surfaces.Faces():
        sewing.Add(face.wrapped)
    sewing.Perform()
    shells = cq.Shape.cast(sewing.SewedShape()).Shells()
    solids = [cq.Shape.cast(ShapeFix_Solid().SolidFromShell(s.wrapped)) for s in shells]
    if source.stem != "CIEPT021PP0":
        if sewing.NbFreeEdges() or sewing.NbMultipleEdges():
            raise ValueError(f"Unsealed IGES surfaces for {source.name}")
        return cq.Compound.makeCompound(solids)

    # The terminal drawing gives an 8 mm detached length with the nose at Z=0.
    # Normalize the strip's topology before the cutoff through its carrier neck.
    (strip,) = solids
    repair = ShapeFix_Shape(strip.wrapped)
    repair.Perform()
    intermediate = Path(work) / "strip.step"
    cq.exporters.export(cq.Shape.cast(repair.Shape()), str(intermediate))
    strip = cq.importers.importStep(str(intermediate)).val()
    retained = cq.Solid.makeBox(8, 6, 8, cq.Vector(-4, -1, -8))
    return strip.intersect(retained)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Directory for rebuilt STEP files")
    output = parser.parse_args().output.resolve()
    if output == SOURCE:
        parser.error("Choose a separate output directory to preserve the archived imports")
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SOURCE / "source-manifest.json").read_text())
    with TemporaryDirectory() as scratch:
        for expected in manifest["assembly_imports"]:
            model = derive(SOURCE / expected["source_file"], scratch)
            destination = output / expected["file"]
            cq.exporters.export(model, str(destination))
            restored = cq.importers.importStep(str(destination)).val()
            bounds = restored.BoundingBox()
            observed = (bounds.xmin, bounds.ymin, bounds.zmin, bounds.xmax, bounds.ymax, bounds.zmax)
            wanted = expected["bounds_xyz_min_mm"] + expected["bounds_xyz_max_mm"]
            if (not restored.isValid() or len(restored.Solids()) != expected["solids"]
                    or len(restored.Faces()) != expected["faces"]
                    or abs(restored.Volume() - expected["volume_mm3"]) > 0.002
                    or any(abs(value - ref) > 0.001 for value, ref in zip(observed, wanted))):
                raise ValueError(f"Round-trip geometry differs from archived import for {destination.name}")
            print(f"{destination.name}: {len(restored.Solids())} valid solids, {restored.Volume():.6f} mm3")


if __name__ == "__main__":
    main()
