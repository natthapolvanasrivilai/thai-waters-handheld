"""Recover connectivity of A5 from plotted copper and plated-drill layers."""
import argparse
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from gerbonara import ExcellonFile, GerberFile
from shapely.geometry import Point, box
from shapely.ops import unary_union

HOME = Path(__file__).resolve().parent
sys.path.insert(0, str(HOME.parent / "pcb-r0004"))
from verify_artwork import geometry


def verify(folder):
    spec = json.loads((HOME/"design.json").read_text())
    expected = defaultdict(set)
    for ref, _, _, _, _, _, nets in spec["parts"]:
        for pin,net in enumerate(nets,1):
            expected[net].add((ref,str(pin)))
    nodes, pins = [], {}
    all_copper = {}
    for layer in ("F","B"):
        copper = defaultdict(list)
        for obj in GerberFile.open(folder/f"usb-input-{layer}_Cu.gbr").objects:
            name, = obj.attrs[".N"]
            copper[name].extend(geometry(p) for p in obj.to_primitives())
            if ".P" in obj.attrs:
                pin = tuple(obj.attrs[".P"][:2])
                assert pin in expected[name]
                pins[pin] = Point(obj.x,obj.y)
        nets = {n:unary_union(s) for n,s in copper.items()}
        all_copper[layer] = nets
        total = unary_union(list(nets.values()))
        nodes.extend((layer,polygon) for polygon in total.geoms)
    groups = [{i} for i in range(len(nodes))]
    holes = ExcellonFile.open(folder/"usb-input.drl").objects
    for hole in holes:
        pt = Point(hole.x,hole.y)
        touching = {i for i,(_,poly) in enumerate(nodes) if poly.covers(pt)}
        assert len(touching)==2 and len({nodes[i][0] for i in touching})==2
        joined = [g for g in groups if g & touching]
        for g in joined: groups.remove(g)
        groups.append(set.union(*joined))
    observed = [{pin for pin,pt in pins.items() if any(nodes[i][0]=='F' and nodes[i][1].covers(pt) for i in g)} for g in groups]
    assert set(pins)==set.union(*expected.values())
    assert {frozenset(s) for s in observed}=={frozenset(s) for s in expected.values()}
    outline = GerberFile.open(folder/"usb-input-Edge_Cuts.gbr").objects
    w,h=spec["size_mm"]
    assert len(outline)==4 and {(o.x1,o.y1) for o in outline}=={(0,0),(w,0),(0,-h),(w,-h)}
    min_space=min(a.distance(b) for nets in all_copper.values() for a,b in combinations(nets.values(),2))
    edge=box(0,-h,w,0)
    assert all(edge.contains(poly) for _,poly in nodes)
    min_edge=min(edge.boundary.distance(poly) for _,poly in nodes)
    assert min_space >= .199 and min_edge >= .499
    return dict(verified_nets=len(expected),pin_count=len(pins),plated_holes=len(holes),size_mm=spec["size_mm"],
                min_gerber_spacing_mm=round(min_space,5),min_gerber_edge_mm=round(min_edge,5))


if __name__ == "__main__":
    with TemporaryDirectory() as tmp, ZipFile(HOME/"usb-input-fab.zip") as archive:
        for file in archive.namelist():
            assert Path(file).name==file
            (Path(tmp)/file).write_bytes(archive.read(file))
        print(json.dumps(verify(Path(tmp)),indent=2))
