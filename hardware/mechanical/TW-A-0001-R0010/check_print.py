"""Slice the new part with Bambu Studio, retaining hash-checked inherited plate results."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from build import BASE, HERE, STEM, digest, write_json

sys.path.insert(0,str(BASE.with_name("TW-A-0001-R0008") / "QA"))
from audit_prints import configure, gcode_metrics, mesh_audit, merge_profile


def check(work, slicer):
    work=work.resolve()
    work.mkdir(exist_ok=True,parents=True)
    configure(slicer,work)
    material="Generic TPU @BBL A1"
    profile=merge_profile(slicer.parent / "resources/profiles/BBL/filament",material)
    filament=work/"filament.json"
    write_json(filament, profile)
    part=HERE/"Print"/(STEM+".stl")
    cmd=[str(slicer),"--load-settings",str(work/"machine.json")+";"+str(work/"process.json"),"--load-filaments",str(filament),
         "--curr-bed-type","Textured PEI Plate","--arrange","1","--slice","0","--outputdir",str(work),str(part)]
    with (work/"slice.log").open("wb") as log:
        subprocess.run(cmd,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
    results=json.loads((BASE/"QA/print-audit.json").read_text())
    for name, row in results.items():
        assert digest(BASE/"Print"/(name+".stl")) == row["sha256"] and row["mesh_pass"]
    row=mesh_audit(part)
    row.update(gcode_metrics(work/"plate_1.gcode"))
    density=float(profile["filament_density"][0])
    row.update(material=material,outer_brim_mm=0,filament_density_g_cm3=density)
    for k in ("support_g","brim_g"):
        row[k]=round(row[k]*density/1.27,4)
    row["mesh_pass"]=(row["bodies"]==1 and row["watertight"] and row["consistent_winding"] and row["positive_volume"]
                      and row["min_z_mm"]==0 and row["bed_area_mm2"]>0 and not row["zero_area_triangles"] and not row["duplicate_triangles"])
    assert row["mesh_pass"] and row["total_g"]>0 and row["support_g"]==0
    results[STEM]=row
    write_json(HERE/"QA/print-audit.json",results)
    print(row)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--slicer",type=Path,required=True)
    a=parser.parse_args()
    check(a.work,a.slicer)

