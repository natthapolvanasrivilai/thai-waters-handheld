"""Write the four installed W4 jackets as an incremental R0012 overlay."""

import csv
import hashlib
import json
from mate import (
    BASE,
    CRIMP_STUB,
    FREE_START_Y,
    HERE,
    NET_PIN,
    STROKE,
    arc_length,
    jacket,
    loop_edge,
)


def dressing_stations(routes):
    with (HERE / "dress-fixture.csv").open("w", newline="") as stream:
        table = csv.writer(stream)
        table.writerow(
            ["net", "withdrawal_mm", "distance_along_jacket_mm", "X_mm", "Y_mm", "Z_mm"]
        )
        for net in NET_PIN:
            x, _, z = routes[net]["tap_center_mm"]
            for d in (0.0, STROKE):
                edge = loop_edge(net, x, z, d)
                tip = edge.startPoint()
                table.writerow([net, d, 0, round(tip.x, 4), round(-5.35 + d, 4), 10.36])
                length = arc_length(edge)
                for station in range(13):
                    u = station / 12
                    point = edge.positionAt(u, mode="length")
                    table.writerow(
                        [
                            net,
                            d,
                            round(CRIMP_STUB + length * u, 4),
                            *[round(v, 4) for v in point.toTuple()],
                        ]
                    )


def main():
    routes = json.loads((BASE / "routing.json").read_text())
    previous = {
        row["name"]: row
        for row in json.loads((BASE / "installed.json").read_text())["add"]
    }
    placed = HERE / "placed"
    placed.mkdir(exist_ok=True)
    new = []
    for net in NET_PIN:
        routes[net]["free_branch_start_mm"][1] = FREE_START_Y
        name = "wh" + net
        tx, _, z = routes[net]["tap_center_mm"]
        shape, length = jacket(net, tx, z)
        assert shape.isValid() and shape.Volume() > 0, net
        path = placed / (name + ".brep")
        shape.exportBrep(str(path))
        new.append(
            dict(
                previous[name],
                note="Fixed-length service lead. A1/A4/A5 and W1 stay at their installed datums throughout withdrawal.",
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
        routes[net]["full_jacket_length_mm"] = round(length, 5)
    (HERE / "installed.json").write_text(
        json.dumps(dict(remove=[r["name"] for r in new], add=new), indent=2) + "\n"
    )
    (HERE / "routing.json").write_text(json.dumps(routes, indent=2) + "\n")
    dressing_stations(routes)


if __name__ == "__main__":
    main()
