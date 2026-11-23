"""Check the editable package and native all-plate, housing-only and R0013 control slices."""
from argparse import ArgumentParser
from pathlib import Path
import json
import shutil
from zipfile import ZipFile

from lxml import etree as ET
import numpy as np
import trimesh
from shapely.geometry import box

from make_project import (HERE, MECH, PROJECT, PARENT, PARENT_HASH, MESH, MODEL, SETTINGS,
                          RELATIONSHIPS, HOUSING, REMOVED, digest, value)
from rail_paths import DX, DY, RAILS, LEVELS, measure, check, footprints
from verify_model_extrusion import audit, instance_index
from path_evidence import inspect

QA = HERE/"QA"


def write(path, data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def compact(node):
    # Ignore insignificant element indentation after a node was removed.
    return ET.tostring(ET.fromstring(ET.tostring(node), ET.XMLParser(remove_blank_text=True)), method="c14n")


def project():
    assert digest(PARENT) == PARENT_HASH
    with ZipFile(PARENT) as old, ZipFile(PROJECT) as new:
        assert new.testzip() is None
        assert set(old.namelist())-set(new.namelist()) == {f"3D/Objects/gauge_{i}.model" for i in REMOVED}
        assert {k for k in new.namelist() if new.read(k)!=old.read(k)} == {MODEL, SETTINGS, HOUSING, RELATIONSHIPS}
        oldidx, newidx = instance_index(old), instance_index(new)
        assert [set(oldidx[i])-set(newidx[i]) for i in range(1,8)] == [set()]*6+[{"1709","1710"}]
        assert all(oldidx[i][k]==v for i,plate in newidx.items() for k,v in plate.items())
        # Verify every retained wrapper, instance, transform, setting and relationship.
        for key in (MODEL,SETTINGS,RELATIONSHIPS):
            a,b = [ET.fromstring(z.read(key)) for z in (old,new)]
            if key==MODEL:
                for path in (".//{*}resources/{*}object", ".//{*}build/{*}item"):
                    for node in a.findall(path):
                        if (node.get("id") or node.get("objectid")) in REMOVED:
                            node.getparent().remove(node)
            elif key==RELATIONSHIPS:
                for node in list(a):
                    if node.get("Target") in {f"/3D/Objects/gauge_{i}.model" for i in REMOVED}:
                        a.remove(node)
            else:
                for node in a.findall("object"):
                    if node.get("id") in REMOVED:
                        a.remove(node)
                for node in a.findall("plate/model_instance"):
                    if value(node,"object_id") in REMOVED:
                        node.getparent().remove(node)
                a.findall("plate")[6].find("metadata[@key='plater_name']").set("value","07 PCB fit gauges - R0014")
                for obj in [doc.find("object[@id='2']") for doc in (a,b)]:
                    for element in obj.xpath(".//*[@face_count]"):
                        element.set("face_count","normalized")
            assert compact(a)==compact(b),key
        source=trimesh.load_mesh(MESH)
        tree=ET.fromstring(new.read(HOUSING))
        vertices=np.array([[float(v.get(k)) for k in "xyz"] for v in tree.findall(".//{*}vertex")])
        faces=np.array([[int(t.get(k)) for k in ("v1","v2","v3")] for t in tree.findall(".//{*}triangle")])
        config=ET.fromstring(new.read(SETTINGS))
        part=config.find("object[@id='2']/part")
        offset=[float(value(part,"source_offset_"+k)) for k in "xyz"]
        assert np.array_equal(faces,source.faces)
        delta=float(np.abs(vertices+offset-source.vertices).max())
        assert delta < 1e-7
        settings=json.loads(new.read("Metadata/project_settings.config"))
        assert settings["extruder_offset"] == ["0x2"]
        assert settings["nozzle_diameter"] == ["0.4"] and settings["layer_height"]=="0.2"
        return dict(parent_sha256=PARENT_HASH,editable_project_sha256=digest(PROJECT),housing_stl_sha256=digest(MESH),
                    native_faces=len(faces),max_native_vertex_axis_error_mm=delta,
                    filament_presets=settings["filament_settings_id"],filament_colours=settings["filament_colour"],
                    instances=newidx,plates=[dict(name=value(p,"plater_name"),bed=value(p,"bed_type"),
                        logical_filament_map=value(p,"filament_maps")) for p in config.findall("plate")])


def witnesses():
    result=[]
    for name,cx in RAILS:
        for part,x0,x1,y0,y1,zs in [
            ("south cap",cx-1.1,cx+1.1,-11.4,-9.0,LEVELS),
            ("west shoulder",cx-1.45,cx-.65,-7.6,-2.,[7.6,7.8]),
            ("east shoulder",cx+.65,cx+1.45,-7.6,-2.,[7.6,7.8]),
            ("groove floor",cx-.52,cx+.52,-7.6,-2.,[7.4])]:
            result.append(dict(plate=1,object_id="385",name=f"{name} rail {part}",
                         reference="Installed A3 rail and channel dimensions registered through the saved receiver-down P0001 pose",
                         xy_mm=[[round(x0+DX,5),round(x1+DX,5)],[round(y0+DY,5),round(y1+DY,5)]],
                         required_layers_z_mm=zs, minimum_path_mm=1.0))
    return dict(features=result)


def inspect_run(folder, expected, features):
    result=json.loads((folder/"result.json").read_bytes())
    assert [p["id"] for p in result["sliced_plates"]]==expected
    audit_result=audit(folder/"sliced.3mf",folder/"result.json",features,None)
    assert audit_result["status"]=="pass",audit_result
    with ZipFile(folder/"sliced.3mf") as z:
        for i in expected:
            assert z.read(f"Metadata/plate_{i}.gcode")== (folder/f"plate_{i}.gcode").read_bytes()
    return audit_result


def verify(scratch):
    QA.mkdir(exist_ok=True)
    identity=project()
    features=QA/"rail-witnesses.json"
    write(features,witnesses())
    runs={}
    for name,expected in [("all",list(range(1,8))),("reopen",[1]),("baseline",[1])]:
        folder=scratch/name
        runs[name]=inspect_run(folder,expected,features if name!="baseline" else None)
    assert len(runs["all"]["objects"])==33 and len(runs["reopen"]["objects"])==1
    for name in ("all","reopen"):
        rails=measure(scratch/name/"plate_1.gcode")
        check(rails)
        runs[name]["rail_footprints"]=rails
    assert runs["all"]["features"]==runs["reopen"]["features"]
    assert runs["all"]["rail_footprints"]==runs["reopen"]["rail_footprints"]
    control=measure(scratch/"baseline/plate_1.gcode")
    for rail in control["rails"].values():
        assert all(row["model_area_mm2"]==0 for row in rail if row["z"]>=6.)
    runs["baseline"]["rail_footprints"]=control
    # Plate 1 whole-object context for bed contact, total support and established
    # elevated islands elsewhere in the housing. The rail check above uses a
    # separately registered local vector footprint and includes support interfaces.
    context,_=inspect(scratch/"reopen/plate_1.gcode",True,focus={"385"})
    count=len(context["385"]["model_component_backing"]["fully_unbacked_components"])
    assert count==1
    # The sole support-started feature is inherited at the west USB end of the
    # housing. Compare its swept model and support shapes against the old slice.
    usb=box(81.55,120.45,83.67,126.40)
    native_usb=[footprints(scratch/k/"plate_1.gcode",usb,13.3,14.2) for k in ("baseline","reopen")]
    island=native_usb[1][14.2]["model"]
    under=native_usb[1][13.8]["support"]
    for z,role in [(14.2,"model"),(13.8,"support")]:
        assert native_usb[0][z][role].symmetric_difference(native_usb[1][z][role]).area < .00001
    usb_overlap=island.intersection(under).area
    assert usb_overlap/island.area > .45
    context["385"]["usb_end"]=dict(model_layer_top_mm=14.2,model_bottom_mm=14.,
            support_layer_top_mm=13.8,model_area_mm2=round(island.area,4),
            model_over_support_mm2=round(usb_overlap,4),projected_overlap_pct=round(100*usb_overlap/island.area,2),
            shape_matches_R0013=True)
    native=json.loads((scratch/"all/result.json").read_bytes())
    plates=[dict(id=p["id"],objects=len(p["objects"]),logical_filaments=p["filaments"],
                 seconds=p["total_predication"],warning=p["warning_message"]) for p in native["sliced_plates"]]
    write(QA/"project-check.json",dict(project=identity,plates=plates,runs=runs,
            housing_path_context=context["385"],housing_elevated_components=count))
    for name in ("all","reopen"):
        shutil.copyfile(scratch/name/"result.json",QA/f"native-{name}.json")
    shutil.copyfile(scratch/"reopen/sliced.3mf",QA/"plate-1-reopen.sliced.3mf")
    print("Verified seven plates, 33 instances, two rail footprints and the independent plate 1 reslice")


if __name__=="__main__":
    cli=ArgumentParser(description=__doc__)
    cli.add_argument("scratch",type=Path)
    verify(cli.parse_args().scratch)
