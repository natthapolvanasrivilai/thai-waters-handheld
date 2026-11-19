"""Slice both controlled housing STLs and verify connectivity, mesh integrity, and inherited plates."""
import argparse
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy import ndimage
import trimesh
from scipy.spatial import cKDTree

from build import HERE, OLD, LEGACY, NAME, digest, load, save
sys.path.insert(0,str(HERE/"QA"))
from toolpaths import GRID, inspect
sys.path.insert(0,str(HERE.with_name("TW-A-0001-R0008")/"QA"))
from audit_prints import configure, gcode_metrics, mesh_audit

def locate_old_strand(mesh, plate, result, sections):
    # Locate the actual disconnected strand in model and support extrusion, then map
    # the toolpath box back through the slicer placement and controlled CAD transform.
    model, _, _ = sections[31.4]
    _, support, _ = sections[31.0]
    labels, _ = ndimage.label(model,structure=np.ones((3,3), dtype=bool))
    regions = [(i,ys,xs) for i,(ys,xs) in enumerate(ndimage.find_objects(labels),1)
               if 30<(ys.stop-ys.start)*GRID<40 and (xs.stop-xs.start)*GRID<1]
    assert len(regions)==1
    footprint=labels==regions[0][0]
    fraction=float((support & footprint).sum()/footprint.sum())
    assert fraction>.2
    strand=max(result["elevated_starts"],key=lambda row:max(row["span_mm"]))
    assert strand["z_mm"]==31.4
    bbox=load(plate/"result.json")["sliced_plates"][0]["objects"][0]["bbox"]
    placed_offset=np.array([bbox["x"],bbox["y"]])-trimesh.load_mesh(mesh).bounds[0,:2]
    xy=np.array(strand["bed_xy_center_mm"])-placed_offset
    inv=np.linalg.inv(load(LEGACY/"part-orientations.json")[NAME]["assembly_to_print"])
    ends=[(inv@[xy[0],xy[1]+dy,strand["z_mm"]-.1,1])[:3].round(2).tolist()
          for dy in (-strand["span_mm"][1]/2,strand["span_mm"][1]/2)]
    return dict(feature="West outer lip of integral rod-grip dovetail",
                centerline_ends_assembly_mm=ends,model_z_mm=31.4,
                support_test_z_mm=31.0,projected_overlap_with_support_percent=round(100*fraction,1))

def verify_rigid_export(meta):
    src=trimesh.load_mesh(LEGACY/"Print"/(NAME+".stl"))
    src.apply_transform(np.linalg.inv(load(LEGACY/"part-orientations.json")[NAME]["assembly_to_print"]))
    dest=trimesh.load_mesh(HERE/meta["print_stl"])
    dest.apply_transform(np.linalg.inv(meta["assembly_to_print"]))
    gaps,index=cKDTree(src.vertices).query(dest.vertices)
    assert len(src.vertices)==len(dest.vertices)==len(np.unique(index))
    assert gaps.max()<.00002
    def faces(array):
        # Cyclic vertex ordering preserves triangle orientation.
        return {tuple(np.roll(face,-int(np.argmin(face)))) for face in array}
    assert faces(src.faces)==faces(index[dest.faces])
    return dict(oriented_triangles=len(src.faces),matching_vertices=len(src.vertices),
                maximum_assembly_vertex_delta_mm=round(float(gaps.max()),8))

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
        sections={31.0:None,31.4:None} if rev==LEGACY else None
        paths=inspect(gcode,sections)
        if sections is not None:
            paths["old_receiver_location"]=locate_old_strand(mesh,plate,paths,sections)
        runs[tag]=dict(stl_sha256=digest(mesh),plate_gcode_sha256=digest(gcode),**row,**paths)
        if rev==HERE:
            metrics[NAME]=row
    for k,row in metrics.items():
        assert row["mesh_pass"] and digest(HERE/meta[k]["print_stl"])==meta[k]["sha256"]==row["sha256"],k
    assert len(metrics)==19
    old,new=runs.values()
    new["installed_mesh_comparison"]=verify_rigid_export(meta[NAME])
    assert any(max(s["span_mm"])>30 for s in old["elevated_starts"])
    assert len(new["first_model_layer"]["regions"])==1 and new["first_model_layer"]["bead_union_regions"]==1
    assert new["first_model_layer"]["bead_union_area_mm2"]>600
    assert all(max(s["span_mm"])<10 for s in new["elevated_starts"])
    save(HERE/"QA/print-audit.json",metrics)
    save(HERE/"QA/housing-toolpaths.json",runs)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--slicer",type=Path,required=True)
    a=p.parse_args()
    check(a.work,a.slicer)
