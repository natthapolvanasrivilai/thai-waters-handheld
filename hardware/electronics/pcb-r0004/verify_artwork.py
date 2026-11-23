"""Check exported Gerber/Excellon copper against netlist.csv. Uses gerbonara and shapely."""
import argparse
import csv
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from gerbonara import ExcellonFile, GerberFile
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent


def geometry(primitive):
    if not primitive.polarity_dark:
        raise ValueError("Unexpected clear copper primitive")
    kind = type(primitive).__name__
    if kind == "Circle":
        return Point(primitive.x, primitive.y).buffer(primitive.r, quad_segs=64)
    if kind == "Line":
        return LineString([(primitive.x1, primitive.y1), (primitive.x2, primitive.y2)]).buffer(
            primitive.width / 2, quad_segs=64
        )
    if kind == "Rectangle":
        x, y, w, h = primitive.x, primitive.y, primitive.w, primitive.h
        return rotate(box(x-w/2, y-h/2, x+w/2, y+h/2), primitive.rotation, (x,y), use_radians=True)
    if kind == "ArcPoly" and not any(primitive.arc_centers):
        return Polygon(primitive.outline)
    raise ValueError(f"Unsupported copper primitive {kind}")


def validate(folder):
    expected = defaultdict(set)
    with (ROOT / "netlist.csv").open() as f:
        for row in csv.DictReader(f):
            expected[row["net"]].add(row["component.pad"])
    by_layer = {}
    pins = {}
    for layer in ("F", "B"):
        copper = defaultdict(list)
        for obj in GerberFile.open(folder / f"harness-{layer}_Cu.gbr").objects:
            net, = obj.attrs[".N"]
            copper[net].extend(geometry(p) for p in obj.to_primitives())
            if ".P" in obj.attrs:
                pin = ".".join(obj.attrs[".P"][:2])
                assert layer == "F" and pin in expected[net] and pin not in pins, (net, pin)
                pins[pin] = Point(obj.x, obj.y)
        by_layer[layer] = {net: unary_union(parts) for net, parts in copper.items()}

    outline = GerberFile.open(folder / "harness-Edge_Cuts.gbr").objects
    expected_corners = {(0,0), (0,-13), (23,0), (23,-13)}
    assert len(outline) == 4 and {(o.x1,o.y1) for o in outline} == expected_corners
    perimeter = box(0,-13,23,0)
    for o in outline:
        assert perimeter.boundary.covers(LineString([(o.x1,o.y1),(o.x2,o.y2)]))
    clearance = min(a.distance(b) for copper in by_layer.values() for a,b in combinations(copper.values(), 2))
    edge_clearance = min(shape.distance(perimeter.boundary) for copper in by_layer.values() for shape in copper.values())
    assert clearance >= 0.1999 and edge_clearance >= 0.4999
    assert all(perimeter.covers(g) for layers in by_layer.values() for g in layers.values())

    # Ignore net names when constructing the actual connected copper islands.
    islands = []
    for layer, copper in by_layer.items():
        connected = unary_union(list(copper.values()))
        for poly in ([connected] if connected.geom_type == "Polygon" else connected.geoms):
            islands.append((layer, poly))
    groups = [{i} for i in range(len(islands))]
    holes = ExcellonFile.open(folder / "harness.drl").objects
    assert len(holes) == 2
    hits = []
    for hole in holes:
        assert abs(hole.aperture.diameter - 0.30) < 1e-6
        center = Point(hole.x, hole.y)
        # Allow only the nominal annulus less tool rounding and polygon discretization.
        lands = [i for i, (_, poly) in enumerate(islands) if poly.covers(center.buffer(0.34))]
        assert len(lands) == 2 and {islands[i][0] for i in lands} == {"F","B"}
        touching = [g for g in groups if g.intersection(lands)]
        for g in touching:
            groups.remove(g)
        groups.append(set.union(*touching))
        hits.append([hole.x, hole.y, hole.aperture.diameter])
    measured = [
        {pin for pin, pt in pins.items() if any(islands[i][0] == "F" and islands[i][1].covers(pt) for i in group)}
        for group in groups
    ]
    assert {frozenset(v) for v in expected.values()} == {frozenset(v) for v in measured}
    assert len(measured) == len(expected) and set(pins) == set.union(*expected.values())
    counts = {}
    for layer in ("F_Mask","B_Mask","F_Paste","F_Silkscreen","B_Silkscreen"):
        counts[layer] = len(GerberFile.open(folder / f"harness-{layer}.gbr").objects)
    assert (counts["F_Mask"],counts["B_Mask"],counts["F_Paste"]) == (34,0,21)
    return {"check": "Gerber copper connected regions with Excellon via bridges against the 34-pad netlist",
            "outline_mm": [23,13], "outer_copper_um": 35, "artwork_networks": len(measured),
            "terminal_pads": len(pins), "drill_xy_diameter_mm_gerber_axes": hits,
            "nominal_minimum_clearance_mm": round(clearance,5),
            "nominal_minimum_edge_clearance_mm": round(edge_clearance,5),
            "plotted_objects": counts, "netlist_match": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path, nargs="?", default=ROOT / "harness-fab.zip")
    args = parser.parse_args()
    with TemporaryDirectory() as tmp, ZipFile(args.archive) as z:
        for member in z.namelist():
            if Path(member).name != member:
                raise ValueError(member)
            (Path(tmp) / member).write_bytes(z.read(member))
        print(json.dumps(validate(Path(tmp)), indent=2))

