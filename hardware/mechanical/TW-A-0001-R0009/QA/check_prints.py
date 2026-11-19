"""Verify every delivered printer mesh, with the marked brim and part material."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

QA=Path(__file__).resolve().parent
REV=QA.parent
sys.path.insert(0,str(REV.with_name("TW-A-0001-R0008")/"QA"))
from audit_prints import configure, gcode_metrics, mesh_audit, merge_profile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--work",type=Path,required=True)
    ap.add_argument("--slicer",type=Path,required=True)
    ap.add_argument("--reuse",action="store_true",help="Reuse G-code only for identical STL and settings hash.")
    args=ap.parse_args()
    work=args.work.resolve()
    work.mkdir(exist_ok=True,parents=True)
    configure(args.slicer,work)
    meta=json.loads((REV/"part-orientations.json").read_text())
    files=sorted((REV/"Print").glob("*.stl"))
    assert {p.stem for p in files}==set(meta)
    results={}
    profile_root=args.slicer.parent/"resources/profiles/BBL/filament"
    for part in files:
        row=mesh_audit(part)
        folder=work/part.stem
        folder.mkdir(exist_ok=True)
        cfg=json.loads((work/"process.json").read_text())
        hint=meta[part.stem]["brim"]
        brim=0 if hint=="None" else float(hint.split(" ")[0])
        if brim: cfg.update(brim_type="outer_only",brim_width=str(brim))
        process=folder/"process.json"
        process.write_text(json.dumps(cfg))
        material="Generic TPU @BBL A1" if "shield-mask" in part.stem else "Generic PETG @BBL A1"
        filament=folder/"filament.json"
        profile=merge_profile(profile_root,material)
        filament.write_text(json.dumps(profile))
        import hashlib
        fingerprint=hashlib.sha256((row["sha256"]+filament.read_text()+process.read_text()+(work/"machine.json").read_text()).encode()).hexdigest()
        stamp=folder/"fingerprint"
        if not(args.reuse and stamp.exists() and stamp.read_text()==fingerprint and (folder/"plate_1.gcode").exists()):
            cmd=[str(args.slicer),"--load-settings",str(work/"machine.json")+";"+str(process),
                 "--load-filaments",str(filament),"--curr-bed-type","Textured PEI Plate",
                 "--arrange","1","--slice","0","--outputdir",str(folder),str(part)]
            run=subprocess.run(cmd,cwd=folder,capture_output=True,timeout=300)
            (folder/"log.txt").write_bytes(run.stdout+run.stderr)
            if run.returncode:raise RuntimeError((part,folder/"log.txt"))
            stamp.write_text(fingerprint)
        row.update(gcode_metrics(folder/"plate_1.gcode"))
        # R8's extraction converts relative support extrusion with PETG density 1.27.
        # Recalibrate for selected TPU density if needed.
        density=float(profile["filament_density"][0])
        row.update(material=material,outer_brim_mm=brim,filament_density_g_cm3=density)
        for k in ("support_g","brim_g"):row[k]=round(row[k]*density/1.27,4)
        row["mesh_pass"]=bool(row["watertight"] and row["consistent_winding"] and row["positive_volume"] and row["bodies"]==1
              and row["min_z_mm"]>=-.02 and row["bed_area_mm2"]>0 and not row["duplicate_triangles"] and not row["zero_area_triangles"])
        results[part.stem]=row
        print(part.stem,row["mesh_pass"],row["minimum_offbed_downward_deg"],row["shallow_sloped_mm2"],row["offbed_flat_mm2"],row["support_g"],flush=True)
    (QA/"print-audit.json").write_text(json.dumps(results,indent=2)+"\n")
if __name__=="__main__":main()
