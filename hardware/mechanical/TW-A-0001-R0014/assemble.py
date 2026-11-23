"""Build and independently reopen the complete local R0014 installation from the R0013 STEP."""
import argparse
import gc
import gzip
import shutil

from build_housing import HERE, OLD, ROOT, PART, NAME, read, save, digest, cq
from pathlib import Path


def describe(shape):
    b = shape.BoundingBox()
    return dict(volume_mm3=round(shape.Volume(), 5), solids=len(shape.Solids()),
                bounds_mm=[round(getattr(b,k),4) for k in ("xmin","xmax","ymin","ymax","zmin","zmax")])


def build(source, dest):
    registered = read(OLD/"installed-step.json")
    assert digest(source) == registered["step_sha256"]
    ledger = registered["components"].copy()
    previous = cq.Assembly.load(str(source))
    assert {c.name for c in previous.children} == set(ledger)
    hpath = HERE/"CAD"/(NAME+".brep")
    h = cq.Shape.importBrep(str(hpath))
    new = cq.Assembly(name="TW_A_0001_R0014_supplier_cell")
    old_shape = {c.name:c.obj.moved(c.loc) for c in previous.children if c.name in ("Housing","adhH")}
    # The registered STEP foam must coincide with the controlled workshop cut
    # definition. New occupied space is entirely contained in the old assembly.
    ref_foam = cq.Shape.importBrep(str(ROOT/"hardware/electronics/haptic-r0009/placed/adhH.brep"))
    assert abs(ref_foam.intersect(old_shape["adhH"]).Volume()-151.2) < .00001
    addition = h.cut(old_shape["Housing"])
    assert abs(addition.Volume()-143.52) < .001
    assert abs(addition.cut(old_shape["adhH"]).Volume()) < .0001
    assert abs(old_shape["Housing"].cut(h).Volume()) < .0001
    for c in previous.children:
        if c.name == "Housing":
            new.add(h, name=c.name, color=c.color)
        elif c.name != "adhH":
            new.add(c.obj, name=c.name, color=c.color, loc=c.loc)
    del ledger["adhH"]
    ledger["Housing"] = {**describe(h), "part_revision":PART, "source_brep":"CAD/"+hpath.name,
                         "source_sha256":digest(hpath)}
    dest.mkdir(parents=True,exist_ok=True)
    installed = dest/(HERE.name+"-dressed.step")
    print("Writing assembly",flush=True)
    new.export(str(installed))
    del new, previous, old_shape, addition
    gc.collect()
    packed = installed.with_suffix(".step.gz")
    with installed.open("rb") as src, packed.open("wb") as out:
        with gzip.GzipFile(filename="",fileobj=out,mode="wb",compresslevel=6,mtime=0) as archive:
            shutil.copyfileobj(src,archive)
    out_step = dest/"roundtrip.step"
    with gzip.open(packed,"rb") as src, out_step.open("wb") as out:
        shutil.copyfileobj(src,out)
    step_hash = digest(installed)
    assert digest(out_step) == step_hash
    print("Reopening dressed STEP",flush=True)
    restored = cq.Assembly.load(str(out_step))
    assert {c.name for c in restored.children} == set(ledger)
    max_vol = max_ext = 0.
    for c in restored.children:
        target = ledger[c.name]
        check = describe(c.obj.moved(c.loc))
        vol_error = abs(check["volume_mm3"]-target["volume_mm3"])
        ext_error = max(abs(a-b) for a,b in zip(check["bounds_mm"],target["bounds_mm"]))
        assert check["solids"] == target["solids"]
        assert vol_error <= max(.014,target["volume_mm3"]*3e-6) and ext_error <= .015, (c.name,check,target)
        max_vol, max_ext = max(max_vol,vol_error), max(max_ext,ext_error)
    save(HERE/"installed-step.json",dict(component_count=len(ledger), step_sha256=step_hash, components=ledger))
    save(HERE/"export-verification.json",dict(source_assembly=OLD.name,source_step_sha256=digest(source),
        installed_step_components=len(ledger),step_sha256=step_hash,packed_step_sha256=digest(packed),
        unchanged_installed_members=len(ledger)-1, changed_member="Housing", removed_node="adhH",
        total_volume_of_new_housing_outside_old_housing_and_foam_mm3=0,
        max_roundtrip_absolute_volume_delta_mm3=round(max_vol,6), max_bounds_delta_mm=round(max_ext,6),
        local_dressed_step=installed.name, local_archive=packed.name,
        sharing="Full electrical assembly contains locally retained supplier geometry. Preserve the R0013 distribution boundary."))
    print("Dressed assembly verified", step_hash, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("registered_r0013_step",type=Path)
    p.add_argument("local_output",type=Path)
    args = p.parse_args()
    build(args.registered_r0013_step,args.local_output)
