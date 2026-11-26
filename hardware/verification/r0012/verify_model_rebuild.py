"""Rebuild A3 models in a clean tree, then compare a fresh KiCad STEP with fitted geometry."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = Path("hardware/electronics/harness-r0005/source-cad")
BOARD = Path("hardware/electronics/pcb-haptic-cie-r0001")
OEM = Path("hardware/components/boardoza-drv2605l/DRV2605L.step")
STEM = "A3-CIE-R0001"

def bounds(solid):
    b = solid.BoundingBox()
    return (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)

def error(a, b):
    return max(abs(x-y) for x,y in zip(a,b))

def read(path):
    return cq.importers.importStep(str(path)).val()

def run(downloads, kicad):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for rel in [OEM, *(SOURCE/f for f in ("prepare_sources.py","convert_supplier.py","source-manifest.json"))]:
            (root/rel).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/rel,root/rel)
        # Exclude generated 3D models and fabrication/analysis outputs.
        board = root / BOARD
        board.mkdir(parents=True)
        for path in (ROOT/BOARD).iterdir():
            if path.is_file() and (path.name in ("make_models.py","fp-lib-table","sym-lib-table")
                                   or path.suffix in (".kicad_pro",".kicad_pcb",".kicad_sch",".kicad_sym")):
                shutil.copyfile(path,board/path.name)
        shutil.copytree(ROOT/BOARD/"TW_Haptic.pretty",board/"TW_Haptic.pretty")
        subprocess.run([sys.executable, root/SOURCE/"prepare_sources.py", downloads],check=True)
        subprocess.run([sys.executable,board/"make_models.py"],check=True)
        models = {}
        for rebuilt in sorted((board/"models").glob("*.step")):
            actual = read(rebuilt)
            reference = read(ROOT/BOARD/"models"/rebuilt.name)
            box_error = error(bounds(actual),bounds(reference))
            volume_error = abs(actual.Volume()-reference.Volume())
            assert actual.isValid() and len(actual.Solids())==len(reference.Solids())
            assert len(actual.Faces())==len(reference.Faces()) and box_error<1e-5 and volume_error<1e-4
            models[rebuilt.name] = dict(solids=len(actual.Solids()),faces=len(actual.Faces()),
                max_bound_difference_mm=round(box_error,7),volume_difference_mm3=round(volume_error,7))
        export = root/"check.step"
        subprocess.run([kicad,"pcb","export","step","--no-dnp","--user-origin","0x0mm",
                        "--include-pads","--include-tracks","--cut-vias-in-body","--no-extra-pad-thickness",
                        "-o",export,board/(STEM+".kicad_pcb")],check=True)
        result = read(export)
        assert result.isValid()
        installed = result.rotate((0,0,0),(0,0,1),90).translate((-37.95,-135.15,4.60))
        exported_bounds = [bounds(s) for s in installed.Solids()]
        comparisons = {}
        for name in ("A3-J1-header","drvParts"):
            original = cq.Shape.importBrep(str(ROOT/SOURCE.parent/"placed"/(name+".brep")))
            reference_bounds = [bounds(s) for s in original.Solids()]
            maximum = max(min(error(ref,bb) for bb in exported_bounds) for ref in reference_bounds)
            assert maximum < 1e-5
            comparisons[name]=dict(matched_solids=len(original.Solids()),
                                   maximum_component_bound_difference_mm=round(maximum,7))
        return dict(input="Nine supplier inputs matched manufacturer-file SHA-256 values. Clean native project and public preparation scripts.",
                    comparison=models,populated_kicad_10_0_8_export=dict(geometry_valid=True,total_solids=len(exported_bounds),
                    comparison_to_installed=comparisons,datum_translation_mm=[-37.95,-135.15,4.60],rotation_about_Z_degrees=90))

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("downloads",type=Path)
    cli.add_argument("--kicad",required=True)
    args=cli.parse_args()
    report=run(args.downloads.resolve(),args.kicad)
    (HERE/"model-rebuild.json").write_text(json.dumps(report,indent=2)+"\n")
