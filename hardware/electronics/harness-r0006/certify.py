"""Conservative native clearance gate for the fixed assembly and distinct W4 leads.

At each station, subdivided centerline control boxes reject distant native
faces. Remaining face distances are evaluated on exact Bezier edges. Subtract
the maximum jacket radius and the independently verified interstation drift.
The rounded endpoint envelopes include the physical flat end caps.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import cadquery as cq
from check import LOADED_HASHES, ROUTES, assembled
from mate import (
    CRIMP_STUB,
    DEGREE,
    HERE,
    JACKET_OD,
    NET_PIN,
    STROKE,
    V,
    bernstein,
    controls,
)

TILES = 24
T = np.linspace(0, 1, DEGREE + 1)
inv = np.linalg.inv(bernstein(DEGREE, T))
SUB = np.stack([inv @ bernstein(DEGREE, (s + T) / TILES) for s in range(TILES)])
RADIUS = JACKET_OD / 2
LIMIT = 0.50
EPS = 0.00003


def bbox(shape):
    b = shape.BoundingBox()
    return np.array([[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]])


def posbox(points):
    return np.array([points.min(axis=0), points.max(axis=0)])


def separation(a, b):
    return np.linalg.norm(
        np.maximum(
            0, np.maximum(a[..., 0, :] - b[..., 1, :], b[..., 0, :] - a[..., 1, :])
        ),
        axis=-1,
    )


def run(cache):
    limits = json.loads((HERE / "motion-bound.json").read_text())
    steps = limits["station_count"]
    drift = {
        n: v["maximum_centerline_displacement_from_nearest_station_mm"] + 0.000001
        for n, v in limits["wire"].items()
    }
    shapes = assembled(cache)
    shapes = {
        k: s
        for k, s in shapes.items()
        if not k.startswith(("wh", "A3-J1-C")) and k not in {"A3-J1-TPA", "A3-J1-plug"}
    }
    poses = {}
    sweep = {}
    for net in NET_PIN:
        x, _, z = ROUTES[net]["tap_center_mm"]
        poses[net] = []
        for d in np.linspace(0, STROKE, steps):
            c = controls(net, x, z, d)
            segments = [
                np.linspace(c[0] - [0, CRIMP_STUB, 0], c[0], DEGREE + 1),
                *(SUB @ c),
            ]
            boxes = np.array([posbox(poles) for poles in segments])
            poses[net].append((segments, boxes))
        allbox = np.stack([q[1] for q in poses[net]])
        sweep[net] = np.array(
            [allbox[:, :, 0].min(axis=(0, 1)), allbox[:, :, 1].max(axis=(0, 1))]
        )
    face_boxes = []
    faces = []
    owners = []
    omitted = []
    for k, s in shapes.items():
        bb = bbox(s)
        if all(
            separation(sweep[n], bb) > LIMIT + RADIUS + drift[n] + EPS for n in NET_PIN
        ):
            omitted.append(k)
            continue
        for f in s.Faces():
            fb = bbox(f)
            if any(
                separation(sweep[n], fb) <= LIMIT + RADIUS + drift[n] + EPS
                for n in NET_PIN
            ):
                faces.append(f)
                face_boxes.append(fb)
                owners.append(k)
    fb = np.array(face_boxes)
    print("Nearby native faces", len(fb), flush=True)
    # Confirm an interior-free starting point for every disjoint stationary
    # solid. Subsequent connected paths cannot enter a solid across a boundary
    # without being caught by the native face clearance test.
    for n in NET_PIN:
        p = poses[n][0][0][0][0]
        pointbox = np.stack([p, p])
        for k, s in shapes.items():
            if k.startswith("tee-" + n + "-") or separation(pointbox, bbox(s)) > EPS:
                continue
            for solid in s.Solids():
                if separation(pointbox, bbox(solid)) <= EPS and solid.isInside(
                    V(*p), 1.0e-7
                ):
                    raise ValueError(("start inside solid", n, k))
    edges = {}
    cache_proofs = {}
    checks = 0
    reused = 0
    pair_checks = 0
    bad = []

    def edge(n, i, tile):
        key = (n, i, tile)
        if key not in edges:
            pts = poses[n][i][0][tile]
            edges[key] = (
                cq.Edge.makeLine(V(*pts[0]), V(*pts[-1]))
                if tile == 0
                else cq.Edge.makeBezier([V(*p) for p in pts])
            )
        return edges[key]

    for n in NET_PIN:
        threshold = LIMIT + RADIUS + drift[n] + EPS
        mask = np.array([not k.startswith("tee-" + n + "-") for k in owners])
        for i, (segments, boxes) in enumerate(poses[n]):
            ids = np.flatnonzero(
                mask
                & (
                    separation(
                        np.array([boxes[:, 0].min(axis=0), boxes[:, 1].max(axis=0)]), fb
                    )
                    <= threshold
                )
            )
            for tile, box in enumerate(boxes):
                for idx in ids[separation(box, fb[ids]) <= threshold]:
                    key = (n, tile, int(idx))
                    if key in cache_proofs:
                        old_idx, old_gap = cache_proofs[key]
                        delta = np.linalg.norm(
                            segments[tile] - poses[n][old_idx][0][tile], axis=1
                        ).max()
                        if old_gap - delta > threshold:
                            reused += 1
                            continue
                    gap = edge(n, i, tile).distance(faces[idx])
                    checks += 1
                    cache_proofs[key] = (i, gap)
                    if gap < threshold:
                        item = (n, i, tile, owners[idx], float(gap), float(threshold))
                        bad.append(item)
                        if len(bad) < 4:
                            print("below proof threshold", item, flush=True)
            if i % 66 == 0:
                print(
                    "fixed",
                    n,
                    i,
                    "extrema",
                    checks,
                    "cached",
                    reused,
                    "failures",
                    len(bad),
                    flush=True,
                )
    for a, b in itertools.combinations(NET_PIN, 2):
        threshold = LIMIT + JACKET_OD + drift[a] + drift[b] + EPS
        for i in range(steps):
            aseg, ab = poses[a][i]
            bseg, bb = poses[b][i]
            aa, jj = np.where(
                separation(ab[:, None, :, :], bb[None, :, :, :]) <= threshold
            )
            for at, bt in zip(aa, jj):
                key = (a, int(at), b, int(bt))
                if key in cache_proofs:
                    old, old_gap = cache_proofs[key]
                    delta = (
                        np.linalg.norm(aseg[at] - poses[a][old][0][at], axis=1).max()
                        + np.linalg.norm(bseg[bt] - poses[b][old][0][bt], axis=1).max()
                    )
                    if old_gap - delta > threshold:
                        continue
                gap = edge(a, i, at).distance(edge(b, i, bt))
                cache_proofs[key] = (i, gap)
                pair_checks += 1
                if gap < threshold:
                    bad.append((a, i, int(at), "wh" + b, float(gap), float(threshold)))
    result = dict(
        pass_nominal=not bad,
        continuous_external_and_interlead_clearance_test_mm=LIMIT,
        native_face_count=len(faces),
        rejected_by_part_bbox=sorted(omitted),
        fixed_overlay_sha256=LOADED_HASHES,
        jacket_sha256={
            r["name"]: r["sha256"]
            for r in json.loads((HERE / "installed.json").read_text())["add"]
        },
        form_sha256=hashlib.sha256((HERE / "loop-forms.json").read_bytes()).hexdigest(),
        exact_edge_to_native_face_queries=checks,
        reused_valid_distance_bounds=reused,
        exact_lead_to_lead_edge_queries=pair_checks,
        uncertified_pairs=bad[:30],
        uncertified_count=len(bad),
        scope="Continuous maximum-radius W4 envelope vs stationary installed geometry, including A1, A4 and updated A3/A5, and vs the three other W4 leads. Only the participating tap joint and the moving connector assembly are excluded from the external certificate. See clearance.json for moving assembly checks.",
    )
    (HERE / "continuous-clearance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result, flush=True)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-breps", type=Path, required=True)
    run(p.parse_args().baseline_breps)
