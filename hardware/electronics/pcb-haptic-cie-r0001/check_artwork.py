"""Independently reconstruct A3 nets from plotted geometry and plated holes."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree
from zipfile import ZipFile

from gerbonara import ExcellonFile, GerberFile
from shapely.geometry import Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pcb-r0004"))
from verify_artwork import geometry

STEM = "A3-CIE-R0001"

def verify(folder):
    netlist = ElementTree.parse(HERE / "connectivity.xml")
    expected = {n.get("name"): {p.get("ref")+"."+p.get("pin") for p in n.findall("node")}
                for n in netlist.findall("./nets/net")}
    pin_groups, islands, pins = [], [], {}
    for layer in ("F","B"):
        objects = GerberFile.open(folder / f"{STEM}-{layer}_Cu.gbr").objects
        shapes = []
        for obj in objects:
            for primitive in obj.to_primitives():
                shape = geometry(primitive)
                # KiCad writes ground zones with bridged inner contours.
                shapes.append(shape if shape.is_valid else shape.buffer(0))
            attrs = obj.attrs if isinstance(obj.attrs, dict) else {}
            if ".P" in attrs:
                ref, number = attrs[".P"][:2]
                pin = ref + "." + number
                if pin in set.union(*expected.values()):
                    pins[(layer,pin)] = Point(obj.x, obj.y)
        copper = unary_union(shapes)
        islands.extend((layer, region) for region in copper.geoms)
    groups = [{i} for i in range(len(islands))]
    holes = ExcellonFile.open(folder / f"{STEM}.drl").objects
    for hole in holes:
        center = Point(hole.x, hole.y)
        touching = {i for i,(_,shape) in enumerate(islands) if shape.covers(center)}
        assert len(touching)==2 and {islands[i][0] for i in touching}=={"F","B"}, center
        merge = [g for g in groups if g & touching]
        for group in merge:
            groups.remove(group)
        groups.append(set.union(*merge))
    for group in groups:
        present = {pin for (layer,pin),point in pins.items()
                   if any(islands[i][0]==layer and islands[i][1].covers(point) for i in group)}
        if present:
            pin_groups.append(present)
    assert {frozenset(p) for p in pin_groups} == {frozenset(p) for p in expected.values()}
    assert len(pin_groups)==len(expected)
    j1 = {i:[120.25,round(-53.91-2.5*(i-1),2)] for i in range(1,6)}
    drills = {(h.x,h.y): h.aperture.diameter for h in holes}
    for i,xy in j1.items():
        assert pins[("F","J1."+str(i))].distance(Point(*xy)) < 1e-8
        assert drills[tuple(xy)]==1
    return dict(nets=len(expected), pads=len(set.union(*pin_groups)),
                plated_holes=len(holes), J1_xy_mm=j1, J1_hole_mm=1.0,
                connectivity={name:sorted(pads) for name,pads in expected.items()},
                floating_copper_islands=len(groups)-len(pin_groups))

if __name__ == "__main__":
    with TemporaryDirectory() as scratch, ZipFile(HERE/(STEM+"-fab.zip")) as archive:
        for file in archive.namelist():
            assert Path(file).name==file
            (Path(scratch)/file).write_bytes(archive.read(file))
        print(json.dumps(verify(Path(scratch)),indent=2))

