"""Check installed vendor-standard screws against the R0009 bridge, pack and receiver."""
from pathlib import Path
import cadquery as cq
import json

HERE = Path(__file__).resolve().parent
CAD = HERE.parents[1] / "mechanical/TW-A-0001-R0009/CAD"
read = lambda p: cq.Shape.importBrep(str(p))
pairs = {
    "tieS1": ["battery-wire-bridge", "PKCELL-max-body-with-wire-sockets"],
    "tieS2": ["battery-wire-bridge", "PKCELL-max-body-with-wire-sockets"],
    "Receiver nut": ["housing-battery-bay", "receiver-nut-keeper"],
    "Keeper screw": ["key-board-retainer-west", "PKCELL-max-body-with-wire-sockets"],
    **{f"H1-{i}": ["PKCELL-max-body-with-wire-sockets", "battery-wire-bridge"] for i in range(1,5)}
}
results = []
for name, neighbours in pairs.items():
    part = read(HERE / "placed" / (name+".brep"))
    for other in neighbours:
        mating = read(CAD / (other+".brep"))
        common = part.intersect(mating).Volume()
        results.append(dict(part=name, neighbour=other, common_mm3=round(common,5),
                            gap_mm=round(part.distance(mating),4)))
(HERE/"fit.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf8")
for r in results: print(r)
