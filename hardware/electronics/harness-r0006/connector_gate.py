"""Verify the exposed wire span continuously in the translating plug frame."""

import hashlib
import json
import math

import cadquery as cq
import numpy as np
from certify import bbox, separation, posbox
from check import ROUTES
from mate import (
    BASE,
    CRIMP_STUB,
    DEGREE,
    HERE,
    JACKET_OD,
    NET_PIN,
    PIVOT,
    RELEASE_DEG,
    STROKE,
    V,
    actuate,
    bernstein,
    controls,
    split_latch,
)

R = JACKET_OD / 2
TARGET = 0.0399
EPS = 0.00002
KNOTS = np.linspace(0, 1, DEGREE + 1)
SUB = np.stack(
    [
        np.linalg.inv(bernstein(DEGREE, KNOTS)) @ bernstein(DEGREE, (j + KNOTS) / 16)
        for j in range(16)
    ]
)


def load(name):
    return cq.Shape.importBrep(str(BASE / "placed" / (name + ".brep")))


def edge(p):
    return cq.Edge.makeBezier([V(*x) for x in p])


def main():
    evidence = json.loads((HERE / "motion-bound.json").read_text())
    body, latch = split_latch(load("A3-J1-plug"))
    members = {"body": body, "latch": actuate(latch, 1), "TPA": load("A3-J1-TPA")}
    for n, pin in NET_PIN.items():
        members["A3-J1-C" + str(pin)] = load("A3-J1-C" + str(pin))
        members["wh" + n + "-Cu"] = load("wh" + n + "-Cu")
    box = {k: bbox(v) for k, v in members.items()}
    lb = bbox(latch)
    rocker_radius = max(
        math.hypot(y - PIVOT[1], z - PIVOT[2]) for y in lb[:, 1] for z in lb[:, 2]
    )
    rocker_allowance = rocker_radius * math.radians(abs(RELEASE_DEG)) / 8
    queries = 0
    cached = 0
    fail = []
    press_min = 999.0
    stub_min = 999.0
    per_net = {}
    for n, pin in NET_PIN.items():
        x, _, z = ROUTES[n]["tap_center_mm"]
        bound = (
            np.array(
                evidence["wire"][n][
                    "relative_displacement_by_sixteen_equal_bezier_parameter_intervals_mm"
                ]
            )
            + 0.000001
        )
        remembered = {}
        c0 = controls(n, x, z, 0)
        p0 = c0[0]
        shaft = cq.Edge.makeLine(V(*(p0 - [0, CRIMP_STUB, 0])), V(*p0))
        start_wire = cq.Wire.assembleEdges([shaft, edge(c0)])
        # Using the straight centerline plus spherical end caps conservatively
        # encloses the full jacket, including the two flat end faces.
        for k, s in members.items():
            if k in {"body", "A3-J1-C" + str(pin), "wh" + n + "-Cu"}:
                continue
            gap = shaft.distance(s) - R
            stub_min = min(stub_min, gap)
            if gap < TARGET + EPS:
                fail.append([n, k, "straight jacket", float(gap)])
        for u in np.linspace(0, 1, 5):
            gap = start_wire.distance(actuate(latch, float(u))) - R - rocker_allowance
            press_min = min(press_min, gap)
            if gap < TARGET:
                fail.append([n, "press", float(u), float(gap)])
        for s in members.values():
            if any(t.isInside(V(*p0), 1e-7) for t in s.Solids()):
                raise ValueError(("free start inside moving member", n))
        for i, d in enumerate(np.linspace(0, STROKE, evidence["station_count"])):
            p = controls(n, x, z, d) - [0, d, 0]
            for j, pts in enumerate(SUB @ p):
                threshold = R + bound[j] + TARGET + EPS
                b = posbox(pts)
                part = None
                for k, s in members.items():
                    if separation(b, box[k]) > threshold:
                        continue
                    key = (k, j)
                    if key in remembered:
                        old, old_gap = remembered[key]
                        if (
                            old_gap - np.linalg.norm(pts - old, axis=1).max()
                            > threshold
                        ):
                            cached += 1
                            continue
                    if part is None:
                        part = edge(pts)
                    gap = part.distance(s)
                    queries += 1
                    remembered[key] = (pts, gap)
                    if gap < threshold:
                        fail.append([n, k, float(d), j, round(gap - R - bound[j], 7)])
        per_net[n] = dict(relative_drift_at_first_sixteenth_mm=float(bound[0]))
    result = dict(
        pass_nominal=not fail,
        form_sha256=hashlib.sha256((HERE / "loop-forms.json").read_bytes()).hexdigest(),
        mating_model_sha256={
            name: hashlib.sha256(
                (BASE / "placed" / (name + ".brep")).read_bytes()
            ).hexdigest()
            for name in [
                "A3-J1-plug",
                "A3-J1-TPA",
                *[key for key in members if key.startswith(("A3-J1-C", "wh"))],
            ]
        },
        continuous_nominal_clearance_test_mm=TARGET,
        minimum_exact_straight_stub_to_nonmating_moving_part_mm=round(stub_min, 6),
        rocker_press_lower_bound_after_rotation_allowance_mm=round(press_min, 6),
        exact_free_span_queries=queries,
        reused_valid_bounds=cached,
        uncertified_pairs=fail[:10],
        uncertified_count=len(fail),
        scope="Free span to body, rocker, TPA, all terminals and conductors during withdrawal. Rigid stub to TPA, rocker, other terminals/conductors. The own crimp and the uncut vendor housing around the rigid stub are intentional/model-limited interfaces. Press is checked before +Y withdrawal.",
        per_net=per_net,
    )
    (HERE / "connector-clearance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result, flush=True)
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
