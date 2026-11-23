"""Audit the source kit, all seven Bambu slices, reopened gauges, mounting holes and local landmarks."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

from lxml import etree as ET
import numpy as np
from shapely.geometry import LineString, Point, box

from make_project import BASE_SHA, CONFIG, GAUGES, HERE, MODEL, PROJECT, SPACERS
sys.path.insert(0, str(HERE.parents[2]/"tools"))
from verify_model_extrusion import audit
sys.path.insert(0, str(HERE.parent/"pocket-reel-r19b-removal-trial"))
from path_evidence import inspect


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def move_hash(z, plate):
    # Generated timestamps, print estimates and slicer comments do not drive the tool.
    with z.open(f"Metadata/plate_{plate}.gcode") as f:
        commands=(line.partition(b";")[0].strip() for line in f)
        return sha256(b"\n".join(line for line in commands if line)).hexdigest()


def check_source(base,project):
    assert digest(base)==BASE_SHA
    with ZipFile(base) as old, ZipFile(project) as new:
        assert new.testzip() is None
        for k in old.namelist():
            if k.startswith("3D/Objects/"):
                assert new.read(k)==old.read(k),k
        for name,nodes in [(MODEL,(".//{*}resources/{*}object",".//{*}build/{*}item")),
                           (CONFIG,("object","plate"))]:
            previous,current=[ET.fromstring(z.read(name)) for z in (old,new)]
            for path in nodes:
                prev=previous.findall(path)
                curr=current.findall(path)
                for a,b in zip(prev,curr[:len(prev)],strict=True):
                    for el in (a,b):
                        for field in el.findall("metadata[@key='gcode_file']"):
                            el.remove(field)
                    assert ET.tostring(a,method="c14n")==ET.tostring(b,method="c14n"),path
        settings=json.loads(new.read("Metadata/project_settings.config"))
        original_settings=json.loads(old.read("Metadata/project_settings.config"))
        assert [k for k in settings if settings[k]!=original_settings[k]]==["filament_colour"]
        assert settings["extruder_offset"]==["0x2"] and len(settings["filament_colour"])==3
        plate=current.findall("plate")[-1]
        assert plate.find("metadata[@key='bed_type']").get("value")=="Engineering Plate"
        assert len(plate.findall("model_instance"))==len(GAUGES+SPACERS)


def verify(base,baseline_run,full,reopen,out):
    project=HERE/PROJECT
    check_source(base,project)
    geom=read(HERE/"geometry.json")["parts"]
    roster=GAUGES+SPACERS
    runs={}
    for name,run,expected in [("all",full,[1,2,3,4,5,6,7]),("reopen",reopen,[7])]:
        native=read(run/"result.json")
        plates=native["sliced_plates"]
        assert native["return_code"]==0 and [p["id"] for p in plates]==expected
        result=audit(run/"sliced.3mf",run/"result.json",None,None)
        assert result["status"]=="pass",result
        if name=="all":
            base_result=audit(baseline_run/"sliced.3mf",baseline_run/"result.json",None,None)
            for plate_id in (1,2,3,6):
                assert [o for o in result["objects"] if o["plate"]==plate_id]==[o for o in base_result["objects"] if o["plate"]==plate_id]
            assert {o["plate"] for o in base_result["objects"] if o["status"]!="pass"}=={4,5}
        last=plates[-1]
        assert [o["name"] for o in last["objects"]]==[x[1] for x in roster]
        runs[name]=dict(native_report_sha256=digest(run/"result.json"),
                        checks=result,plate_ids=expected,
                        plate7_grams=last["filaments"][0]["total_used_g"],
                        plate7_seconds=last["total_predication"])
    with ZipFile(baseline_run/"sliced.3mf") as baseline, ZipFile(full/"sliced.3mf") as seven, ZipFile(reopen/"sliced.3mf") as again:
        original_hashes=[move_hash(baseline,i) for i in range(1,7)]
        output_hashes=[move_hash(seven,i) for i in range(1,7)]
        gauge_hash=move_hash(seven,7)
        reopened_hash=move_hash(again,7)
        assert [o for o in runs["all"]["checks"]["objects"] if o["plate"]==7]==runs["reopen"]["checks"]["objects"]
        assert abs(runs["all"]["plate7_grams"]-runs["reopen"]["plate7_grams"])<.1
    landmarks=[]
    bores=[]
    def local_checks(instance,layers):
        index=int(instance)-1701
        stem,_,cx,cy=roster[index]
        if stem not in geom:return
        board=geom[stem]
        lower,upper=np.array(board["print_min_max_mm"])
        offset=np.array([cx,cy-2])-(lower[:2]+upper[:2])/2
        for label,(lo,hi) in board["feature_bounds_print_min_max_mm"].items():
            if label=="substrate" or label.startswith("population-"):continue
            target=(lo[2]+hi[2])/2
            possible=[z for z in layers if lo[2]-.001 < z <= hi[2]+.1]
            assert possible,(stem,label)
            z=min(possible,key=lambda zn:abs(zn-target))
            area=box(*(np.array(lo[:2])+offset-.01),*(np.array(hi[:2])+offset+.01))
            length=sum(LineString(points).intersection(area).length for _,points in layers[z])
            assert length>.25,(stem,label,length)
            landmarks.append(dict(part=stem,feature=label,z_mm=z,extrusion_length_mm=round(length,3)))
        if stem not in ("A1-display","A2-sensor"):return
        for h in board["bore_geometry"]:
            if h["diameter_mm"]<1.9:continue
            xy=offset+np.array(h["center_print_xy_mm"])
            probe=Point(*xy)
            start,end=h["depth_span_print_z_mm"]
            # Inspect all fully enclosed layers, including the first bottom layer
            # of the through-holes. Ignore the transition into the A1 blind bottom.
            tested=[z for z in layers if start+.19<=z<=end+.001]
            assert len(tested)>=7
            gaps=[]
            for z in tested:
                closest=min(LineString(points).distance(probe)-width/2 for width,points in layers[z])
                # Also require deposited perimeter near the nominal radius on
                # every layer. Empty space outside a board is not a passing hole.
                assert h["diameter_mm"]/2-.21 < closest < h["diameter_mm"]/2+.35,(stem,z,xy,closest)
                gaps.append(closest)
            if stem=="A2-sensor":assert min(gaps)>2.05/2
            bores.append(dict(part=stem,center_gcode_mm=xy.round(4).tolist(),nominal_diameter_mm=h["diameter_mm"],
                              layers=len(tested),minimum_bead_clear_radius_mm=round(min(gaps),4)))
    focus={str(1701+i) for i in range(len(roster))}
    paths,_=inspect(reopen/"plate_7.gcode",True,focus=focus,layer_observer=local_checks)
    assert set(paths)==focus
    for key,entry in paths.items():
        assert entry["model_mm3"]>0 and entry["first_model_contact_regions"]==1
        assert entry["brim_mm3"]==entry["support_mm3"]==0
        assert not entry["model_component_backing"]["fully_unbacked_components"],(key,entry)
    assert len(bores)==8
    report=dict(project_sha256=digest(project),enclosure_project_sha256=BASE_SHA,
                source_geometry_sha256=digest(HERE/"geometry.json"),
original_six_command_sha256=original_hashes,repacked_six_command_sha256=output_hashes,
                plate7_command_sha256=gauge_hash,reopen_command_sha256=reopened_hash,
                runs=runs,plate7_paths=paths,landmarks=landmarks,mounting_hole_paths=bores)
    out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(out,"verified",len(paths),"objects and",len(bores),"mounting bores")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ("baseline","baseline_run","all","reopen"):cli.add_argument(name,type=Path)
    args=cli.parse_args()
    verify(args.baseline,args.baseline_run,args.all,args.reopen,HERE/"QA/project-check.json")
