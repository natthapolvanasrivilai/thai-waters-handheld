"""Bake centimeter-by-centimeter catch weights for the C++ and WebAssembly engines."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_catch_weights():
    with (ROOT / "game/content/Field-book.csv").open(encoding="utf-8", newline="") as src:
        fish = list(csv.DictReader(src))
    catalog = json.loads((ROOT / "game/content/catalog.json").read_text(encoding="utf-8"))["fish"]
    assert len(fish) == 52 and len(catalog) >= len(fish)
    offsets, measures, lines = [], [], []
    offset = 0
    for number, (row, entry) in enumerate(zip(fish, catalog)):
        low, high = int(row["Min cm"]), int(row["Max cm"])
        assert (int(row["Stable ID"]), row["Species"], low, high) == (
            number, entry["name"], entry["low"], entry["high"])
        a, b = float(row["Mass a"]), float(row["Mass b"])
        if row["Shape axes"]:
            axes = [float(ratio) for ratio in row["Shape axes"].split()]
            assert len(axes) == 3 and all(0 < axis < 1 for axis in axes)
            assert b == 3 and abs(a - math.pi / 6 * math.prod(axes)) < 1e-10
        weights = [max(1, int(a * cm**b + 0.5)) for cm in range(low, high + 1)]
        assert weights == sorted(weights) and weights[-1] <= 1000000
        lines.append(" // " + row["Species"])
        for start in range(0, len(weights), 14):
            lines.append(" " + ",".join(map(str, weights[start:start + 14])) + ",")
        offsets.append(str(offset))
        offset += len(weights)
        measures.append(json.dumps(row["Size measure"]))
    header = (
        "// Generated from game/content/Field-book.csv by game/catch_weights.py.\n"
        "#pragma once\n#include <cstdint>\nnamespace catchmass {\n"
        "constexpr uint16_t offset[]={" + ",".join(offsets) + "};\n"
        "constexpr const char* measure[]={\n " + ",\n ".join(measures) + "\n};\n"
        "constexpr int32_t grams[]={\n" + "\n".join(lines) + "\n};\n}\n"
    )
    target = ROOT / "firmware/WillowCreek/CatchMass.h"
    if not target.exists() or target.read_text(encoding="utf-8") != header:
        target.write_text(header, encoding="utf-8")


if __name__ == "__main__":
    write_catch_weights()
