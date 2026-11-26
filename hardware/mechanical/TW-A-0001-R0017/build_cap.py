"""Build the keyed cap in the installed R0016 datums and check its complete nominal motion."""
import json
from pathlib import Path
import sys

import cadquery as cq
import trimesh

HERE = Path(__file__).resolve().parent
M = HERE.parent
BASE = M / "TW-A-0001-R0016"
sys.path.insert(0, str(M / "TW-A-0001-R0014/QA/power-key"))
import key_check as key

V = cq.Vector
AX = V(0, 1, 0)
axis = [(-36, 0, 12.5), (-36, 1, 12.5)]
box = key.box
vol = key.volume


def profile(r, y, depth, corner):
    """Three circular quadrants and a softly radiused fourth corner facing +X,+Z."""
    center = V(-36, y, 12.5)
    disk = cq.Solid.makeCylinder(r, depth, center, AX)
    quadrant = box(-36, -36+r, y, y+depth, 12.5, 12.5+r)
    outer = [e for e in quadrant.Edges() if
             abs(e.Center().x - (-36+r)) < .001 and abs(e.Center().z-(12.5+r)) < .001]
    assert len(outer) == 1
    return disk.fuse(quadrant.fillet(corner, outer)).clean().Solids()[0]


def cap_geometry(old):
    flange = profile(3.85, 33, .54, .5)
    face = profile(2.75, 33.54, .78, .45)
    rim = [e for e in face.Edges() if e.BoundingBox().ymin > 34.3199]
    face = face.fillet(.22, rim)
    engraving = box(-37.7,-34.3,34.018,34.33,10.8,14.52).cut(old)
    cap = flange.fuse(face).cut(engraving)
    # Give the fixed metal cover's four rivets room for the full switch pretravel.
    for x in (-38.15, -33.85):
        for z in (10.35, 14.65):
            cap = cap.cut(cq.Solid.makeCylinder(.98,.25,V(x,32.99,z),AX))
    cap = cap.clean()
    assert cap.isValid() and len(cap.Solids()) == 1
    return cap


def check():
    parts, _, _ = key.all_geometry()
    old = parts.pop("Key cap")
    cap = cap_geometry(old)
    case = cq.Shape.importBrep(str(BASE/"CAD/housing-battery-bay.brep"))
    cq.exporters.export(cap,str(HERE/"CAD/power-cap.step"))
    cap.exportBrep(str(HERE/"CAD/power-cap.brep"))
    # Same flange-down orientation and XY origin as the R0016 print kit.
    printed = cap.translate((36,-33,-12.5)).rotate((0,0,0),(1,0,0),90)
    printed.exportStl(str(HERE/"Print/power-cap.stl"), .003, .06)
    assert trimesh.load_mesh(HERE/"Print/power-cap.stl").is_volume

    def swept(lo, hi):
        # Both profiles envelop all reliefs, engraving and edge radii throughout this slide.
        return profile(3.85,33+lo,.54+hi-lo,.5).fuse(profile(2.75,33.54+lo,.78+hi-lo,.45))
    drop = box(-39.85,-32.15,30.5,31.82,8.65,40.35)
    assert vol(cap,drop.translate((0,2.5,0))) > cap.Volume()-.00001
    paths = {name:key.pair(shape,case) for name,shape in {
        "inside drop 24 mm":drop,"outward seating 2.50 mm":swept(-2.5,0),
        "inward press 0.50 mm":swept(-.50,0)}.items()}
    assert all(row["common_mm3"]<1e-6 for row in paths.values()),paths
    # All cap positions clear of the PCB and keeper insertion. They arrive after the loose cap.
    install = {n:key.pair(s,cap) for n,s in key.vertical_boxes(key.seated_boxes(
        {n:s for n,s in parts.items() if n != "Retainer"})).items()}
    install["keeper"] = key.pair(key.keeper_sweep(parts["Retainer"]),cap)
    assert min(p["gap_mm"] for p in install.values()) > .001
    # The nearest Y face of each fixed solid lies behind the pressing cap.
    # Its projection toward the switch is maximal at full stroke. The four
    # counterbores are invariant in depth until the rounded rivet tips enter them.
    fixed, moving = sorted(parts["Switch plunger"].Solids(),key=lambda s:s.BoundingBox().ymax)
    full = cap.translate((0,-.50,0))
    full_gaps = {n:key.pair(full,s)["gap_mm"] for n,s in
                 {"fixed switch cover":fixed,"switch body":parts["Switch case"],"keeper":parts["Retainer"]}.items()}
    assert min(full_gaps.values()) > .01,full_gaps
    assert abs(cap.distance(moving)-.05)<1e-5
    assert abs(full.distance(moving.translate((0,-.45,0))))<1e-5
    # Rotation controls at seated and fully depressed positions. Check nominal
    # centered angles separately from translational play in an actual print.
    twist = {}
    for stroke in (0,.50):
        row = {}
        for sign in (-1,1):
            clear, hit = 0., 18.
            def interference(s,angle):
                return vol(s.rotate(*axis,angle).translate((0,-stroke,0)),case)
            assert interference(cap,sign*hit)>.001
            for _ in range(12):
                mid=(clear+hit)/2
                if interference(cap,sign*mid)>1e-7: hit=mid
                else: clear=mid
            row[str(sign)] = round(sign*hit,3)
        assert vol(old.rotate(*axis,90).translate((0,-stroke,0)),case)<1e-6
        twist[str(stroke)]=row
    # At rest the 3/4-round flange spans the bore diameter on both axes.
    # Even translating by the complete nominal flange play cannot take its
    # keyed corner through the circular quadrant at 90 degrees.
    radius=3.85
    corner=.5
    corner_r=(2**.5)*(radius-corner)+corner
    radial_excess=corner_r - 4.15 - (2**.5)*.30
    assert radial_excess>.5
    result=dict(assembly="TW-A-0001-R0016 with TW-P-0013-R0003",source_housing_sha256=key.digest(BASE/"CAD/housing-battery-bay.brep"),
                cap_stl_sha256=key.digest(HERE/"Print/power-cap.stl"),housing_steps_mm=[6.,8.3],
                perimeter_clearance_mm={"face":.25,"flange":.30},insertion_and_press=paths,board_and_keeper_install=install,
                full_press_fixed_part_gaps_mm=full_gaps,rest_plunger_gap_mm=.05,switch_motion_mm=.45,
                centered_twist_first_interference_deg=twist,old_round_cap_90deg_control="free",
                seated_90deg_radial_interference_lower_bound_after_xy_play_mm=round(radial_excess,3),
                scope="Rigid, nominal CAD. Print variation, side load, wear, electrical switching and return require a physical sample.")
    (HERE/"QA/fit.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    check()
