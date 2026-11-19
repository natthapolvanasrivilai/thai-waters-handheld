"""Audit delivered STL coordinates and slice each part separately on identical A1 settings."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
REV = HERE.parent
MECH = REV.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stls(rev):
    if rev == "baseline":
        return sorted([*(MECH / "rev-G/Print").glob("*.stl"), *(MECH / "rev-F/review/gauges").glob("*.stl")])
    return sorted([*(REV/"Print").glob("*.stl"), *(REV/"Inert-gauges").glob("*.stl")])


def mesh_audit(path):
    mesh = trimesh.load_mesh(path)
    # STL coordinates are single precision. Accept up to 0.01 mm coplanarity at bed.
    z0 = mesh.bounds[0, 2]
    bed = mesh.triangles[:, :, 2].max(axis=1) <= z0 + 0.01
    nz = mesh.face_normals[:, 2]
    flat = nz < -math.cos(math.radians(0.1))
    low = nz < -math.cos(math.radians(30)) - 1e-7
    area = mesh.area_faces
    def total(mask):
        return round(float(np.sum(area[mask])), 3)
    down=(nz < -1e-9) & ~bed
    minimum=round(float(np.degrees(np.arccos(np.clip(-nz[down],-1,1))).min()),3) if down.any() else None
    return dict(sha256=sha(path), minimum_offbed_downward_deg=minimum,
                zero_area_triangles=int(np.count_nonzero(area < 1e-10)),
                duplicate_triangles=int(np.count_nonzero(~mesh.unique_faces())), watertight=bool(mesh.is_watertight),
                consistent_winding=bool(mesh.is_winding_consistent), positive_volume=bool(mesh.is_volume),
                bodies=len(mesh.split(only_watertight=False)), triangles=len(nz), min_z_mm=round(float(z0), 4),
                extents_mm=np.round(mesh.extents, 3).tolist(), bed_area_mm2=total(bed & flat),
                shallow_sloped_mm2=total(low & ~flat & ~bed), offbed_flat_mm2=total(flat & ~bed))


def merge_profile(folder, name):
    data = json.loads((folder / (name + ".json")).read_text(encoding="utf-8-sig"))
    base = data.pop("inherits", None)
    return (merge_profile(folder, base) if base else {}) | data


def configure(exe, work):
    root = exe.parent / "resources/profiles/BBL"
    for kind, name in [("machine", "Bambu Lab A1 0.4 nozzle"), ("process", "0.20mm Standard @BBL A1"),
                       ("filament", "Generic PETG @BBL A1")]:
        profile = merge_profile(root / kind, name)
        if kind == "process":
            profile.update(enable_support="1", support_type="normal(auto)", support_threshold_angle="30",
                           support_on_build_plate_only="0", brim_type="no_brim")
        (work / (kind + ".json")).write_text(json.dumps(profile), encoding="utf-8")


def gcode_metrics(path):
    feature = ""
    relative = False
    totals = defaultdict(float)
    grams = duration = version = None
    for line in path.open(encoding="utf-8", errors="replace"):
        if line.startswith("; FEATURE: "):
            feature = line.split(": ",1)[1].strip()
        if line.startswith("; total filament weight [g]"):
            grams = float(line.split(":")[-1])
        if line.startswith("; model printing time:"):
            duration = line.split(";")[1].split(":")[1].strip()
        if line.startswith("; BambuStudio "):
            version = line.strip()[2:]
        code = line.split(";",1)[0].strip()
        if code in ("M82", "M83"):
            relative = code == "M83"
        if not code.startswith(("G1 ", "G2 ", "G3 ")):
            continue
        if not re.search(r"(?:^| )([XY])[-.\d]+",code):
            continue
        m = re.search(r"(?:^| )E([.\d]+)(?: |$)",code)
        if feature in ("Bridge", "Internal Bridge", "Support", "Support interface", "Support transition", "Brim") and m:
            if not relative:
                raise ValueError("Parser expects positive relative toolpath extrusion")
            totals[feature] += float(m[1])
    # Filament settings explicitly use 1.75 mm rounds and 1.27 g/cm3 PETG.
    k = math.pi * (1.75 / 2)**2 * 1.27 / 1000
    return dict(slicer=version, estimated_time=duration, total_g=grams,
                support_g=round(k*sum(v for role,v in totals.items() if role.startswith("Support")),4),
                brim_g=round(k*totals["Brim"],4),
                bridge_extrusion_mm=round(totals["Bridge"] + totals["Internal Bridge"],3))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("rev",choices=["baseline","candidate"])
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--slicer", type=Path)
    p.add_argument("--specified-brims",action="store_true",help="Slice R0008 with the outer brims in the orientation table.")
    args = p.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True,exist_ok=True)
    if args.slicer:
        configure(args.slicer, work)
    if args.specified_brims and (args.rev!="candidate" or not args.slicer):
        p.error("--specified-brims requires candidate and --slicer")
    orientations=json.loads((REV/"part-orientations.json").read_text()) if args.specified_brims else {}
    out = {}
    for part in stls(args.rev):
        row = mesh_audit(part)
        if args.slicer:
            folder = work / (args.rev + ("-brims" if args.specified_brims else "")) / part.stem
            folder.mkdir(parents=True,exist_ok=True)
            settings=work/"process.json"
            if args.specified_brims:
                hint=orientations[part.stem]["brim"]
                width=0 if hint=="None" else float(hint.split(" ")[0])
                row["outer_brim_mm"]=width
                if width:
                    config=json.loads(settings.read_text())
                    config.update(brim_type="outer_only",brim_width=str(width))
                    settings=folder/"brim-process.json"
                    settings.write_text(json.dumps(config))
            cmd = [str(args.slicer), "--load-settings",str(work/"machine.json")+";"+str(settings),
                   "--load-filaments",str(work/"filament.json"),"--curr-bed-type","Textured PEI Plate",
                   "--arrange","1","--slice","0","--outputdir",str(folder),str(part)]
            result = subprocess.run(cmd,cwd=folder,capture_output=True,timeout=240)
            (folder / "slicer.log").write_bytes(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError((part.name,result.returncode,folder/"slicer.log"))
            row.update(gcode_metrics(folder / "plate_1.gcode"))
            record=json.loads((folder/"result.json").read_text())["sliced_plates"][0]["filaments"][0]
            native=record["total_used_g"]-record["main_used_g"]
            # Slicer builds may account for skirt/brim with the main object or auxiliary extrusion.
            assert min(abs(row["support_g"]-native),abs(row["support_g"]+row["brim_g"]-native))<.002, (part.name,row["support_g"],native)
            if row.get("outer_brim_mm"):
                assert row["brim_g"]>0.,part.name
        out[part.stem] = row
        print(part.stem, row["shallow_sloped_mm2"], row["offbed_flat_mm2"], row.get("support_g"),flush=True)
    if len(out)!=14:
        raise ValueError(f"Expected 14 parts, found {len(out)}")
    assert all(r["watertight"] and r["consistent_winding"] and r["positive_volume"] and r["bodies"]==1 for r in out.values())
    assert all(abs(r["min_z_mm"])<=.02 and r["bed_area_mm2"]>0 for r in out.values())
    filename = args.rev + ("-specified-brims.json" if args.specified_brims else "-fdm.json" if args.slicer else "-mesh.json")
    (HERE / filename).write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
