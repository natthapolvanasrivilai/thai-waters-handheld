"""Measure native model and support footprints along the dry gauge route and its seating features."""
import json
from itertools import product

import numpy as np
from shapely import union_all
from shapely.geometry import Polygon
import trimesh

from prepare import HERE, digest
from rail_paths import footprints, window


GAUGES = HERE.parent.with_name("pcb-fit-r0013")
ENTRY_Y = -15.0
DZ = 3.200001004
WITNESSES = {
    # Installed XY and completed build layers chosen inside the CAD features.
    "floor": ((-42.04, -1.9, -41.55, 1.9), [14.6]),
    "inboard_lip": ((-41.18, -2.2, -40.55, 1.9), [14.8, 15.0, 15.2, 15.4]),
    "far_stop": ((-42.06, 2.42, -41.54, 2.60), [n / 5 for n in range(75, 89)]),
    "roof": ((-42.42, -2.28, -41.50, 2.28), [18.2, 18.4, 18.6]),
}


def gauge_boxes():
    row = json.loads((GAUGES / "geometry.json").read_bytes())["parts"]["USB-PCB1"]
    mesh_path = GAUGES / row["file"]
    assert digest(mesh_path) == row["sha256"]
    matrix = np.eye(4)
    matrix[:3] = row["print_to_installed_3x4"]
    boxes = []
    for lo, hi in row["feature_bounds_print_min_max_mm"].values():
        points = trimesh.transform_points(list(product(*zip(lo, hi))), matrix)
        boxes.append((points.min(axis=0), points.max(axis=0)))
    # The plate-7 gauge is exactly the union of its substrate and LED blocks.
    (a, b), (c, d) = boxes
    volume = np.prod(b-a) + np.prod(d-c) - np.prod(np.maximum(0, np.minimum(b,d)-np.maximum(a,c)))
    assert abs(volume - trimesh.load_mesh(mesh_path).volume) < 0.00001
    return boxes


def result(rows):
    return {
        role: {
            "peak_in_section_mm2": round(max([area for _, area in values] or [0]), 6),
            "occupied_build_layers_mm": [z for z, area in values if area > .000001],
        } for role, values in rows.items()
    }


def usb_witnesses(gcode):
    boxes = gauge_boxes()
    heights = {}
    for line in gcode.read_text(encoding="utf8").splitlines():
        if line.startswith("; Z_HEIGHT:"):
            z = float(line.partition(":")[2])
        elif line.startswith("; LAYER_HEIGHT:"):
            heights[z] = float(line.partition(":")[2])
    layers = footprints(gcode, window(-43, -18, -40, 3.1), 14.4, 31.0)
    empty = Polygon()
    route = {}
    for phase in ("lower_at_service_edge", "slide_to_stop"):
        rows = {"model": [], "support": []}
        for z, roles in sorted(layers.items()):
            ceiling = z - DZ
            bottom = ceiling - heights[z]
            cross = []
            for low, high in boxes:
                if ceiling <= low[2] + 1e-6:
                    continue
                if phase == "slide_to_stop":
                    if bottom >= high[2] - 1e-6:
                        continue
                    area = window(low[0], low[1]+ENTRY_Y, high[0], high[1])
                else:
                    area = window(low[0], low[1]+ENTRY_Y, high[0], high[1]+ENTRY_Y)
                cross.append(area)
            swept = union_all(cross)
            for role in rows:
                rows[role].append((z, roles.get(role, empty).intersection(swept).area))
        route[phase] = result(rows)
    features = {}
    for name, (rect, zs) in WITNESSES.items():
        region = window(*rect)
        covered = [layers.get(z, {}).get("model", empty).intersection(region).area for z in zs]
        features[name] = {
            "installed_XY_mm": rect, "sampled_build_layers_mm": zs,
            "area_mm2": round(region.area, 6),
            "min_max_native_model_coverage_fraction": [round(f(covered) / region.area, 6) for f in (min, max)],
        }
    return {"route": route, "features": features}
