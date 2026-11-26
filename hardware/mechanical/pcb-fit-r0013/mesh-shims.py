"""Generate removable height gauges for the R0013 dummy-board stack."""
import argparse
from pathlib import Path

import trimesh


# name, length along installed X and Y, installed bottom, installed top (mm).
# The A4/A5 gauges take their flat backs to the copper envelope.
SHIMS = {
    "A3-floor-shim": (3, 12, 2.50, 4.60),
    "A4-display-shim": (3, 3, 18.535, 21.00),
    "A5-display-shim": (3, 3, 17.840, 21.00),
}


def make(destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name, (width, length, bottom, top) in SHIMS.items():
        height = top - bottom
        part = trimesh.creation.box(extents=(width, length, height))
        part.apply_translation((0, 0, height / 2))
        part.export(destination / (name + ".stl"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    make(parser.parse_args().destination)
