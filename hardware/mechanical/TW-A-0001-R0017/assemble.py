"""Replace only the cap in the actual R0016 installed assembly, test new stock, and reopen the STEP."""
import argparse
import gc
import gzip
from pathlib import Path
import shutil
import sys
import cadquery as cq

HERE = Path(__file__).resolve().parent
PARENT = HERE.with_name("TW-A-0001-R0016")
sys.path.insert(0, str(HERE.with_name("TW-A-0001-R0014")))
from build_housing import digest, read, save


def measure(s):
    b = s.BoundingBox()
    return dict(volume_mm3=round(s.Volume(),5),solids=len(s.Solids()),
                bounds_mm=[round(getattr(b,k),4) for k in ("xmin","xmax","ymin","ymax","zmin","zmax")])


def run(original, dest):
    prior = read(PARENT/"installed-step.json")
    assert digest(original) == prior["step_sha256"]
    src = cq.Assembly.load(str(original))
    members = prior["components"]
    assert {c.name for c in src.children} == set(members)
    replacement = HERE/"CAD/power-cap.brep"
    cap = cq.Shape.importBrep(str(replacement))
    old_child = next(c for c in src.children if c.name=="Key cap")
    old = old_child.obj.moved(old_child.loc)
    addition = cap.cut(old)
    assert addition.Volume() > 0.1 and old.cut(cap).Volume() > 0.1
    # The inherited housing is still registered against its R0016 BREP.
    members["Housing"]["source_brep"] = "../TW-A-0001-R0016/CAD/housing-battery-bay.brep"
    box = addition.BoundingBox()
    new = cq.Assembly(name="TW_A_0001_R0017_keyed_cap")
    intersects = {}
    for c in src.children:
        if c.name=="Key cap":
            new.add(cap,name=c.name,color=c.color)
            continue
        s = c.obj.moved(c.loc)
        b = s.BoundingBox()
        if all(getattr(b,k+"min")<=getattr(box,k+"max") and getattr(b,k+"max")>=getattr(box,k+"min") for k in "xyz"):
            overlap = abs(addition.intersect(s).Volume())
            intersects[c.name] = round(overlap,7)
            assert overlap < .00001,(c.name,overlap)
        new.add(c.obj,name=c.name,color=c.color,loc=c.loc)
    members["Key cap"] = dict(**measure(cap),part_revision="TW-P-0013-R0003",source_brep="CAD/"+replacement.name,source_sha256=digest(replacement))
    dest.mkdir(exist_ok=True,parents=True)
    installed = dest/(HERE.name+"-dressed.step")
    new.export(str(installed))
    del new,src
    gc.collect()
    reopened = cq.Assembly.load(str(installed))
    assert {c.name for c in reopened.children}==set(members)
    worst_v = worst_b = 0.
    for c in reopened.children:
        actual = measure(c.obj.moved(c.loc))
        expected = members[c.name]
        vol = abs(actual["volume_mm3"]-expected["volume_mm3"])
        extent = max(abs(x-y) for x,y in zip(actual["bounds_mm"],expected["bounds_mm"]))
        assert vol < max(.014,expected["volume_mm3"]*3e-6) and actual["solids"]==expected["solids"] and extent<.015,c.name
        worst_v,worst_b=max(worst_v,vol),max(worst_b,extent)
    sha = digest(installed)
    save(HERE/"installed-step.json",dict(component_count=len(members),step_sha256=sha,components=members))
    packed = installed.with_suffix(".step.gz")
    with installed.open("rb") as src, packed.open("wb") as f, gzip.GzipFile(filename="",mode="wb",fileobj=f,mtime=0,compresslevel=6) as archive:
        shutil.copyfileobj(src,archive)
    save(HERE/"export-verification.json",dict(source_assembly=PARENT.name,source_step_sha256=prior["step_sha256"],
        installed_step_components=len(members),changed_member="Key cap",unchanged_installed_members=len(members)-1,
        added_cap_material_against_overlapping_component_boxes_mm3=intersects,
        step_sha256=sha,packed_step_sha256=digest(packed),max_bounds_delta_mm=round(worst_b,6),
        max_roundtrip_absolute_volume_delta_mm3=round(worst_v,6),local_dressed_step=installed.name,
        local_archive=packed.name,sharing="Full supplier assembly retained locally."))
    print("Verified installed STEP",sha)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("r0016_step",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    run(args.r0016_step,args.output)
