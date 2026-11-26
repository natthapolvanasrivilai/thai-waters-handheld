"""Check the seated-display W4 withdrawal against the installed R0013 members."""

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

import cadquery as cq
import numpy as np
from mate import (
    BASE,
    CRIMP_STUB,
    DEGREE,
    HERE,
    JACKET_OD,
    NET_PIN,
    STROKE,
    actuate,
    arc_length,
    bernstein,
    controls,
    guide,
    jacket,
    loop_edge,
    split_latch,
)

MECHANICAL = HERE.parents[1] / "mechanical/TW-A-0001-R0012"
sys.path.insert(0, str(MECHANICAL))
import service_check as sc

ROUTES = json.loads((HERE / "routing.json").read_text())
T = np.linspace(0, 1, 401)
POSITION = bernstein(DEGREE, T)
VELOCITY = DEGREE * bernstein(DEGREE - 1, T)
ACCELERATION = DEGREE * (DEGREE - 1) * bernstein(DEGREE - 2, T)
RADIUS = JACKET_OD / 2
OVERLAYS = {
    "drvBoard": HERE.parent / "pcb-haptic-cie-r0002/placed/drvBoard.brep",
    "drvParts": HERE.parent / "pcb-haptic-cie-r0002/placed/drvParts.brep",
    "A5-power": HERE.parent / "usb-entry-r0006/A5-power.brep",
    "A5-bond": MECHANICAL.with_name("TW-A-0001-R0013") / "A5-bond.brep",
}

USB_LEADS = HERE.parent / "usb-entry-r0006/installed-leads"
USB_MANIFEST = json.loads((USB_LEADS / "installed.json").read_text())
OVERLAYS.update({row["name"]: USB_LEADS / row["brep"] for row in USB_MANIFEST["add"]})


LOADED_HASHES = {}


def assembled(cache):
    ss = sc.read_shapes(cache)
    for name in USB_MANIFEST["remove"]:
        ss.pop(name, None)
    for name, path in OVERLAYS.items():
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        ss[name] = cq.Shape.importBrep(str(path))
        if hashlib.sha256(path.read_bytes()).hexdigest() != before:
            raise ValueError(f"{name} changed while loading")
        LOADED_HASHES[name] = before
    return ss


def native_at(net, d, free=False):
    x, _, z = ROUTES[net]["tap_center_mm"]
    return loop_edge(net, x, z, d) if free else jacket(net, x, z, d)[0]


def main(cache, steps):
    cache = Path(cache)
    ss = assembled(cache)
    moving_names = {k for k in ss if k.startswith(("wh", "A3-J1-C"))} | {
        "A3-J1-plug",
        "A3-J1-TPA",
    }
    loom_names = {
        k
        for k in ss
        if k.startswith(("w1", "tee-", "termination-W1-")) or k == "J8plug"
    }
    display_names = {k for k in ss if k.startswith(("A1-", "A4-", "A5-"))}
    body, latch = split_latch(ss["A3-J1-plug"])
    members = {k: s for k, s in ss.items() if k not in moving_names}
    # At each station, twelve exact Bezier control hulls enclose the free
    # centerline. Components and individual board solids beyond 3 mm cannot
    # beat the reported groups' submillimetre minima even at maximum OD.
    samples = np.linspace(0, 1, DEGREE + 1)
    inverse = np.linalg.inv(bernstein(DEGREE, samples))
    sub = np.stack([inverse @ bernstein(DEGREE, (j + samples) / 12) for j in range(12)])
    lower, upper = [], []
    for n in NET_PIN:
        x, _, z = ROUTES[n]["tap_center_mm"]
        for d in np.linspace(0, STROKE, steps):
            poles = controls(n, x, z, d)
            tiles = sub @ poles
            lower.extend(tiles.min(axis=1))
            upper.extend(tiles.max(axis=1))
            lower.append(poles[0] - [0, CRIMP_STUB, 0])
            upper.append(poles[0])
    lo, hi = np.array(lower), np.array(upper)

    def nearby(shape):
        b = shape.BoundingBox()
        delta = np.maximum(
            0, np.maximum(lo - [b.xmax, b.ymax, b.zmax], [b.xmin, b.ymin, b.zmin] - hi)
        )
        return np.any(np.sum(delta * delta, axis=1) < 9)

    omitted = []
    fixed = {}
    for k, s in members.items():
        if not nearby(s):
            omitted.append(k)
            continue
        mesh = cache.parent / "mesh" / (k + ".npz")
        if (
            mesh.exists()
            and k not in OVERLAYS
            and not (BASE / "placed" / (k + ".brep")).exists()
        ):
            with np.load(mesh) as f:
                fixed[k] = sc.model(f["v"], f["i"])
        else:
            solids = [solid for solid in s.Solids() if nearby(solid)]
            if not solids:
                omitted.append(k)
                continue
            shape = cq.Compound.makeCompound(solids) if len(solids) > 1 else solids[0]
            print("Meshing", k, len(solids), flush=True)
            fixed[k] = sc.model(*sc.tri(shape))
    print("Fixed members ready", len(fixed), flush=True)
    # Test the free span separately against its own mating assembly. The rigid
    # crimp stub deliberately enters the modeled insulation wing and housing.
    rigid_shapes = {
        "plug-body": body,
        "released-latch": actuate(latch, 1),
        "TPA": ss["A3-J1-TPA"],
    }
    rigid_shapes.update(
        {k: ss[k] for k in moving_names if k.startswith("A3-J1-C") or k.endswith("-Cu")}
    )
    rigid_mesh = {k: sc.model(*sc.tri(s)) for k, s in rigid_shapes.items()}

    def best(m, objects, keys):
        box = sc.BOXES[id(m)] + m.getTranslation()
        order = []
        for k in keys:
            obj = objects[k]
            ob = sc.BOXES[id(obj)] + obj.getTranslation()
            lower = np.linalg.norm(
                np.maximum(0, np.maximum(box[0] - ob[1], ob[0] - box[1]))
            )
            order.append((lower, k))
        answer = (float("inf"), "")
        for lb, k in sorted(order):
            if lb > answer[0]:
                break
            answer = min(answer, (sc.meshgap(m, objects[k]), k))
        return answer

    rows = []
    winners = {}
    radius = {}
    previous = {}
    max_motion = {}
    lengths = {n: [] for n in NET_PIN}
    anchor_error = {n: 0.0 for n in NET_PIN}
    direction_error = {n: 0.0 for n in NET_PIN}
    end_direction = np.array([0.0, 0.70, -1.0])
    end_direction /= np.linalg.norm(end_direction)
    display = set(fixed) & display_names
    loom = set(fixed) & loom_names
    for d in np.linspace(0, STROKE, steps):
        for m in rigid_mesh.values():
            m.setTranslation(np.array([0.0, d, 0.0]))
        leads = {}
        minima = {}

        def add(g, val, n, k):
            value = (float(val), n, k, float(d))
            minima[g] = min(value, minima.get(g, value))

        for n in NET_PIN:
            x, _, z = ROUTES[n]["tap_center_mm"]
            p = controls(n, x, z, d)
            prescribed_start = np.array(ROUTES[n]["free_branch_start_mm"]) + [0, d, 0]
            prescribed_end = np.array(ROUTES[n]["fixed_branch_end_mm"])
            start_tangent = (p[1] - p[0]) / np.linalg.norm(p[1] - p[0])
            end_tangent = (p[-1] - p[-2]) / np.linalg.norm(p[-1] - p[-2])
            anchor_error[n] = max(
                anchor_error[n],
                np.linalg.norm(p[0] - prescribed_start),
                np.linalg.norm(p[-1] - prescribed_end),
            )
            direction_error[n] = max(
                direction_error[n],
                np.linalg.norm(start_tangent - [0, 1, 0]),
                np.linalg.norm(end_tangent - end_direction),
            )
            pts = guide(n, x, z, d, 97)
            free = sc.tube(pts, RADIUS)
            lead = sc.tube([[pts[0][0], -5.35 + d, 10.36]] + pts, RADIUS)
            leads[n] = lead
            keys = {k for k in fixed if not k.startswith("tee-" + n + "-")}
            for kind, selection in [
                ("display", display),
                ("W1", loom & keys),
                ("fixed", keys - display - loom),
            ]:
                g, k = best(lead, fixed, selection)
                add(kind, g, n, k)
            g, k = best(free, rigid_mesh, rigid_mesh)
            add("free_to_moving", g, n, k)
            # Also check the straight crimp stub against the TPA, other
            # occupied contacts and conductors. Own termination is intentional.
            pin = NET_PIN[n]
            sel = [
                k
                for k in rigid_mesh
                if k == "TPA"
                or (k.startswith("A3-J1-C") and k != "A3-J1-C" + str(pin))
                or (k.endswith("-Cu") and k != "wh" + n + "-Cu")
            ]
            g, k = best(lead, rigid_mesh, sel)
            add("jacket_to_moving", g, n, k)
            vel = VELOCITY @ np.diff(p, axis=0)
            acc = ACCELERATION @ np.diff(p, n=2, axis=0)
            radii = np.linalg.norm(vel, axis=1) ** 3 / np.maximum(
                1e-12, np.linalg.norm(np.cross(vel, acc), axis=1)
            )
            ri = int(np.argmin(radii))
            r = (float(radii[ri]), float(d), float(T[ri]))
            radius[n] = min(radius.get(n, r), r)
            lengths[n].append(CRIMP_STUB + arc_length(loop_edge(n, x, z, d)))
            centers = POSITION @ p
            if n in previous:
                max_motion[n] = max(
                    max_motion.get(n, 0),
                    float(np.linalg.norm(centers - previous[n], axis=1).max()),
                )
            previous[n] = centers
        for n, m in itertools.combinations(NET_PIN, 2):
            add("lead_to_lead", sc.meshgap(leads[n], leads[m]), n, "wh" + m)
        row = {"travel_mm": float(d)}
        for kind, (g, n, k, at) in minima.items():
            row.update({kind + "_mm": round(g, 6), kind + "_net": n, kind + "_part": k})
            winners[kind] = min(winners.get(kind, (g, n, k, at)), (g, n, k, at))
        rows.append(row)
        if len(rows) % 24 == 1:
            print(len(rows), row, flush=True)
    out = {}
    for kind, (g, n, k, d) in winners.items():
        a = native_at(n, d)
        if kind == "free_to_moving":
            # Subtract jacket radius from exact centerline distance. This is a
            # conservative solid-jacket distance even near the end caps.
            a = native_at(n, d, True)
        if kind == "lead_to_lead":
            b = native_at(k[2:], d)
        elif kind.endswith("_moving"):
            b = rigid_shapes[k].translate((0, d, 0))
        else:
            b = ss[k]
        exact = sc.native_gap(a, b)
        gap = exact["gap_mm"] - (RADIUS if kind == "free_to_moving" else 0)
        out[kind] = dict(
            travel_mm=d,
            net=n,
            part=k,
            mesh_mm=round(g, 6),
            native_gap_or_conservative_lower_mm=round(gap, 6),
            native_witness=exact,
        )
    negative = {}
    for n in NET_PIN:
        x, _, z = ROUTES[n]["tap_center_mm"]
        s = __import__("mate").base.jacket(n, x, z, 8.25)[0]
        b = cq.Shape.importBrep(str(BASE / "placed/A5-power.brep"))
        negative[n] = dict(
            R0012_full_withdrawal_to_R0012_A5_mm=round(s.distance(b), 6),
            R0012_A5_intersection_mm3=round(s.intersect(b).Volume(), 6),
        )
    for n in NET_PIN:
        if (
            anchor_error[n] > 1e-7
            or direction_error[n] > 1e-7
            or np.ptp(lengths[n]) > 1e-5
        ):
            raise ValueError(f"Datum, tangent or constant length failed for {n}")
    report = dict(
        stroke_mm=STROKE,
        withdrawal_axis="+Y",
        seated_display=True,
        station_count=steps,
        spacing_mm=STROKE / (steps - 1),
        geometry="Full outward stroke with released latch. Fixed W1/J8, taps, A1, A4, A5, and A3 board. Include the plug body, TPA, released rocker, four contacts and four conductors in free-span clearance.",
        excluded_contacts="Own wire to its own tap overcoat/copper is a designed bonded junction. The straight crimp stub enters its own insulation wing and supplier housing. The free span is checked against all moving connector members.",
        installed_fixed_parts_screened=sorted(fixed),
        fixed_parts_beyond_swept_box=sorted(omitted),
        overlay_sha256=LOADED_HASHES,
        jacket_sha256={
            r["name"]: r["sha256"]
            for r in json.loads((HERE / "installed.json").read_text())["add"]
        },
        form_sha256=hashlib.sha256((HERE / "loop-forms.json").read_bytes()).hexdigest(),
        minimum_by_pair_group=out,
        branch={
            n: dict(
                minimum_centerline_radius_mm=round(radius[n][0], 5),
                at_travel_mm=radius[n][1],
                at_curve_fraction=radius[n][2],
                native_length_range_mm=[
                    round(min(lengths[n]), 7),
                    round(max(lengths[n]), 7),
                ],
                max_observed_point_motion_between_adjacent_stations_mm=round(
                    max_motion[n], 6
                ),
            )
            for n in NET_PIN
        },
        anchor_checks={
            n: dict(
                maximum_endpoint_error_mm=round(float(anchor_error[n]), 10),
                maximum_unit_tangent_vector_error=round(float(direction_error[n]), 10),
                native_length_variation_mm=round(float(np.ptp(lengths[n])), 10),
            )
            for n in NET_PIN
        },
        R0012_negative_control=negative,
        scope="Nominal CAD. Distances screened at discrete stations; native extrema at the limiting mesh station of each pair group. Bore detail, forming tolerances, spring-back, fatigue and operating forces require physical evidence.",
    )
    (HERE / "clearance.json").write_text(json.dumps(report, indent=2) + "\n")
    with (HERE / "service-path.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-breps", required=True, type=Path)
    p.add_argument("--stations", type=int, default=133)
    args = p.parse_args()
    main(args.baseline_breps, args.stations)
