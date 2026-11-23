"""Verify the two installed rails, adhesive cavity and PCB in the delivery STEP."""
import argparse
import math
import sys
from pathlib import Path

from build_housing import CENTERS, FLOOR, HERE, OLD, ROOT, TOP, RELIEF, box, cq, digest, rail, read, save

sys.path.insert(0,str(OLD.with_name("TW-A-0001-R0012")))
from service_check import maximum_drawing_pack


def box_gap(a,b):
    return math.sqrt(sum(max(0, getattr(a,axis+"min")-getattr(b,axis+"max"),
                             getattr(b,axis+"min")-getattr(a,axis+"max"))**2 for axis in "xyz"))


def run(step):
    ledger = read(HERE/"installed-step.json")
    assert digest(step) == ledger["step_sha256"]
    installed = cq.Assembly.load(str(step))
    shapes = {c.name:c.obj.moved(c.loc) for c in installed.children}
    assert len(shapes) == 154 and set(shapes) == set(ledger["components"]) and "adhH" not in shapes
    housing, board = shapes.pop("Housing"), shapes["drvBoard"]
    shapes["cellDrawing"] = maximum_drawing_pack()
    boxes = {k:s.BoundingBox() for k,s in shapes.items()}
    details = {}
    max_overlap = 0.
    for x in CENTERS:
        r = rail(x)
        b = r.BoundingBox()
        w = "west" if x == CENTERS[0] else "east"
        # Each comparison uses the independent analytic rail definition AFTER
        # verifying all its material is present in the reopened housing.
        assert r.cut(housing).Volume() < .00001
        floor_foot = box(x-1.5,-12,FLOOR-.1,3,12,.1)
        assert abs(floor_foot.intersect(housing).Volume()/0.1 - 36) < .0001
        cavity = box(x-.6,-8,RELIEF,1.2,8,TOP-RELIEF)
        assert abs(cavity.Volume()-3.84) < .00001
        assert cavity.intersect(housing).Volume() < .00001
        exact = {}
        lower = {}
        for key, obstacle in shapes.items():
            bound = box_gap(b,boxes[key])
            if bound > 4 and not (key.startswith(("wh","wm","A3-J1")) or key in ("cellAlt","cellDrawing")):
                lower[key] = math.floor(bound*1e4)/1e4
                continue
            distance = r.distance(obstacle)
            overlap = r.intersect(obstacle).Volume() if distance < .00001 else 0.
            max_overlap = max(max_overlap, overlap)
            exact[key] = {"gap_mm":round(distance,5),"overlap_mm3":round(overlap,6)}
        assert max_overlap < .00001
        pins = sorted(shapes["A3-J1-header"].Solids(), key=lambda s:s.Center().x)
        pins = [s for s in pins if s.BoundingBox().zmin < TOP]
        assert len(pins) == 5
        contact = r.translate((0,0,.001)).intersect(board).Volume()/.001
        wettable = box(x-.6,-8,TOP,1.2,8,.001).intersect(board).Volume()/.001
        assert 25 < contact <= 26.4 and abs(wettable-9.6) < .0001
        collision = r.intersect(board.translate((0,0,-.25))).Volume()
        assert collision > 6
        # The end is open from Z4.20 through Z4.60. Test a 1 mm continuation
        # of the full flow section. No external squeeze-out is specified or counted.
        outlet = box(x-.6,0,RELIEF,1.2,1,TOP-RELIEF)
        assert outlet.intersect(housing).Volume() < .00001
        blocked = {}
        for name,s in shapes.items():
            if box_gap(outlet.BoundingBox(),boxes[name]) < .0001:
                v = outlet.intersect(s).Volume()
                if v > .00001:
                    blocked[name] = v
        assert not blocked
        details[w] = dict(center_x_mm=x, bearing_plane_z_mm=TOP, floor_z_mm=FLOOR,
            bonded_to_floor_footprint_mm2=36, hard_land_area_mm2=26.4,
            actual_PCB_supported_area_mm2=round(contact,5), actual_PCB_over_groove_area_mm2=round(wettable,5),
            adhesive_capacity_mm3=round(cavity.Volume(),5),clear_outlet_prism_length_mm=1.,
            negative_control_PCB_down_0p25mm_overlap_mm3=round(collision,5),
            pins_by_increasing_installed_x=[dict(center_x_mm=round(p.Center().x,4),
                tail_bottom_z_mm=round(p.BoundingBox().zmin,5),rail_gap_mm=round(r.distance(p),5)) for p in pins],
            exact_member_comparisons=exact, bounding_box_distance_lower_bounds_mm=lower)
        print(w, contact, wettable, flush=True)
    save(HERE/"QA/installed-fit.json",dict(dressed_step_sha256=digest(step), housing_brep_sha256=digest(HERE/"CAD/housing-battery-bay.brep"),
        installed_member_count=ledger["component_count"],members_besides_housing=153,
        additional_pack_option="cellDrawing: 35.3 x 62.3 x 5.3, checked instead of cellAlt",
        incremental_overlap_mm3=round(max_overlap,6), rails=details,
        scope="Incremental seated-case fit of added material against all 153 other installed children plus a separate maximum drawing battery. Distances are exact CAD shape distances for nearby components and marked Euclidean AABB lower bounds for others. Reported PCB contact area is the volume of a 0.001 mm hard-land penetration divided by its depth; plated holes reduce actual bearing. Dry fit excludes foam, glue and process variation. Electrical isolation, cured retention and shock require physical samples."))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step",type=Path)
    run(parser.parse_args().step)
