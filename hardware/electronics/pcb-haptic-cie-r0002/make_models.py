"""Make project-relative 3D models using locally obtained supplier files and CadQuery."""
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
MODELS = HERE / "models"
MODELS.mkdir(exist_ok=True)
source = HERE.parents[1] / "components/boardoza-drv2605l/DRV2605L.step"
solids = cq.importers.importStep(str(source)).val().Solids()
assert len(solids) == 18
driver = cq.Compound.makeCompound(solids[4:16]).translate((-128.2, 58.8, -1.595))
cq.exporters.export(driver, str(MODELS / "DRV2605LDGSR.step"))

source = HERE.parent / "harness-r0005/source-cad/CIEP05P1HK0-NH.step"
header = cq.importers.importStep(str(source)).val()
assert len(header.Solids()) == 6
installed = header.translate((22.713653857, -10.6093745, 1.66))
# KiCad places package models at 1.595 mm above the native board datum;
# the assembly datum is 4.600 mm. The unclad substrate ends at 1.510 mm.
local = installed.translate((-15.96, 14.9, -6.195)).rotate((0,0,0), (0,0,1), -90)
cq.exporters.export(local, str(MODELS / "CIEP05P1HK0-NH-mounted.step"))
