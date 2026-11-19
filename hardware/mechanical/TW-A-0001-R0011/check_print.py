"""Slice both controlled housing STLs and verify connectivity, mesh integrity, and inherited plates."""
import argparse
from pathlib import Path
import subprocess
import sys

from build import HERE, OLD, LEGACY, NAME, digest, load, save
sys.path.insert(0,str(HERE/"QA"))
from toolpaths import inspect
sys.path.insert(0,str(HERE.with_name("TW-A-0001-R0008")/"QA"))
from audit_prints import configure, gcode_metrics, mesh_audit

def check(work, exe):
    work=work.resolve()
    work.mkdir(exist_ok=True,parents=True)
    configure(exe,work)
    meta=load(HERE/"part-orientations.json")
    metrics=load(OLD/"QA/print-audit.json")
    runs={}
    for tag,rev,brim in (("R0009",LEGACY,8),("R0011",HERE,0)):
        plate=work/tag
        plate.mkdir(exist_ok=True)
        process=load(work/"process.json")
        if brim:
            process.update(brim_type="outer_only",brim_width=str(brim))
        save(plate/"process.json",process)
        mesh=rev/"Print"/(NAME+".stl")
        cmd=[str(exe),"--load-settings",str(work/"machine.json")+";"+str(plate/"process.json"),
             "--load-filaments",str(work/"filament.json"),"--curr-bed-type","Textured PEI Plate",
             "--arrange","1","--slice","0","--outputdir",str(plate),str(mesh)]
        with (plate/"slice.log").open("wb") as log:
            subprocess.run(cmd,cwd=plate,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
        gcode=plate/"plate_1.gcode"
        row=mesh_audit(mesh)
        row.update(gcode_metrics(gcode),material="Generic PETG @BBL A1",outer_brim_mm=brim,filament_density_g_cm3=1.27)
        row["mesh_pass"]=all((row["watertight"], row["consistent_winding"], row["positive_volume"],
                             row["bodies"]==1,row["min_z_mm"]==0,row["bed_area_mm2"]>0,row["duplicate_triangles"]==0,
                             row["zero_area_triangles"]==0))
        assert row["mesh_pass"] and row["total_g"]>0
        paths=inspect(gcode)
        runs[tag]=dict(stl_sha256=digest(mesh),plate_gcode_sha256=digest(gcode),**row,**paths)
        if rev==HERE:
            metrics[NAME]=row
    for k,row in metrics.items():
        assert row["mesh_pass"] and digest(HERE/meta[k]["print_stl"])==meta[k]["sha256"]==row["sha256"],k
    assert len(metrics)==19
    old,new=runs.values()
    assert any(max(s["span_mm"])>30 for s in old["elevated_starts"])
    assert len(new["first_model_layer"]["regions"])==1 and new["first_model_layer"]["total_area_mm2"]>600
    assert all(max(s["span_mm"])<10 for s in new["elevated_starts"])
    save(HERE/"QA/print-audit.json",metrics)
    save(HERE/"QA/housing-toolpaths.json",runs)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--slicer",type=Path,required=True)
    a=p.parse_args()
    check(a.work,a.slicer)
