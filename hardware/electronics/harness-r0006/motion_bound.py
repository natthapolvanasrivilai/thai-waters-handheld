"""Bound the centerline motion between stations using Bernstein control hulls.

The length of each seventh-degree curve is bounded above by subdivided control
polygons and below by its inscribed chords. For a fixed scale, the poles are
affine in travel. Convexity therefore bounds the upper length by the worse
endpoint of an interval. Projecting chords on their midpoint directions gives
an affine lower bound, valid throughout the interval. These two inequalities
enclose the constant-length solution's positive scale before bounding its XYZ
motion against the nearest sampled station.
"""

import hashlib
import json
import numpy as np
from mate import (
    SPEED_BASIS,
    WEIGHTS,
    CRIMP_STUB,
    DEGREE,
    HERE,
    NET_PIN,
    STROKE,
    base_poles,
    bernstein,
    controls,
    free_length,
)

N = 133
SUB = 128
NODES = np.linspace(0, 1, DEGREE + 1)
LOCAL = np.linalg.inv(bernstein(DEGREE, NODES))
SUBDIV = np.vstack([LOCAL @ bernstein(DEGREE, (s + NODES) / SUB) for s in range(SUB)])
PROBE = bernstein(DEGREE, np.linspace(0, 1, 401))
routes = json.loads((HERE / "routing.json").read_text())


def polar_limits(ref, direction, factor):
    return (ref + factor * direction).reshape(SUB, DEGREE + 1, 3)


def polygon_length(p):
    return np.linalg.norm(np.diff(p, axis=1), axis=2).sum()


def derivative_subdivision(deg):
    knots = np.linspace(0, 1, deg + 1)
    inverse = np.linalg.inv(bernstein(deg, knots))
    return np.stack([inverse @ bernstein(deg, (s + knots) / SUB) for s in range(SUB)])


VELOCITY_TILES = derivative_subdivision(DEGREE - 1)
ACCELERATION_TILES = derivative_subdivision(DEGREE - 2)


def radius_bound(poles):
    # The first and second derivatives are bilinear in travel and scale.
    # Each derivative lies in its local Bernstein control hull on every tile.
    v = VELOCITY_TILES @ (DEGREE * np.diff(poles, axis=1))[:, None, :, :]
    acc = (
        ACCELERATION_TILES
        @ (DEGREE * (DEGREE - 1) * np.diff(poles, n=2, axis=1))[:, None, :, :]
    )
    vmin, vmax = v.min(axis=(0, 2)) - 1e-7, v.max(axis=(0, 2)) + 1e-7
    amin, amax = acc.min(axis=(0, 2)) - 1e-6, acc.max(axis=(0, 2)) + 1e-6
    speed = np.linalg.norm(np.maximum(0, np.maximum(vmin, -vmax)), axis=1)

    def product(i, j):
        x = np.array([u[:, i] * v[:, j] for u in (vmin, vmax) for v in (amin, amax)])
        return x.min(axis=0), x.max(axis=0)

    components = []
    for i, j in ((1, 2), (2, 0), (0, 1)):
        lo, hi = product(i, j)
        neglo, neghi = product(j, i)
        components.append(np.maximum(abs(lo - neghi), abs(hi - neglo)))
    return (
        np.min(speed**3 / np.maximum(1e-12, np.linalg.norm(components, axis=0))) - 1e-6
    )


def bounds(n, left, right, station, target_lo, target_hi):
    x, _, z = routes[n]["tap_center_mm"]
    a, b = base_poles(n, x, z, left)
    c, e = base_poles(n, x, z, right)
    c0 = controls(n, x, z, station)
    original = (a, b, c, e)
    qvel = [SPEED_BASIS @ np.diff(p, axis=0) for p in (a, b, c, e)]
    nominal_length = free_length(controls(n, x, z, 0))
    a, b, c, e, c0 = [SUBDIV @ p for p in (a, b, c, e, c0)]
    scale = lambda p, r, s: float(np.vdot(r, s - p) / np.vdot(r, r))
    ql = scale(a, b, SUBDIV @ controls(n, x, z, left))
    qr = scale(c, e, SUBDIV @ controls(n, x, z, right))
    low, high = min(ql, qr), max(ql, qr)
    pad = 1.0e-6
    for _ in range(36):
        lower = low - pad
        upper = high + pad
        if lower <= 0:
            raise ValueError("Positive root lower bracket lost")
        endpoint_lo = [polar_limits(A, B, lower) for A, B in ((a, b), (c, e))]
        if max(polygon_length(p) for p in endpoint_lo) >= target_lo - 1e-8:
            pad *= 1.8
            continue
        endpoint_hi = [polar_limits(A, B, upper) for A, B in ((a, b), (c, e))]
        chords = [p[:, -1] - p[:, 0] for p in endpoint_hi]
        mid = chords[0] + chords[1]
        directions = mid / np.linalg.norm(mid, axis=1)[:, None]
        if min(np.sum(v * directions) for v in chords) <= target_hi + 1.0e-8:
            pad *= 1.8
            continue
        # Enclose the finite Gauss length functional used by controls() as
        # well as true arclength. Each positive-node speed is a norm of an
        # affine function of travel. A midpoint supporting direction is an
        # affine lower bound at both extremes, hence throughout the interval.
        va, vb, vc, ve = qvel
        lo_velocity = [va + lower * vb, vc + lower * ve]
        if (
            max(WEIGHTS @ np.linalg.norm(v, axis=1) for v in lo_velocity)
            >= nominal_length - 1e-9
        ):
            pad *= 1.8
            continue
        hi_velocity = [va + upper * vb, vc + upper * ve]
        mean = hi_velocity[0] + hi_velocity[1]
        direction = mean / np.linalg.norm(mean, axis=1)[:, None]
        if (
            min(WEIGHTS @ np.sum(v * direction, axis=1) for v in hi_velocity)
            <= nominal_length + 1e-9
        ):
            pad *= 1.8
            continue
        # P(d,q) is bilinear, so every pole stays in the convex hull of the
        # four corners. Subdivision reduces overestimation in curve parameter.
        corners = [
            (A + q * B - c0, offset)
            for A, B, offset in ((a, b, left - station), (c, e, right - station))
            for q in (lower, upper)
        ]
        absolute = max(
            abs(left - station),
            abs(right - station),
            *(np.linalg.norm(delta, axis=1).max() for delta, _ in corners),
        )
        relative_tiles = np.max(
            [
                np.linalg.norm(delta - [0, offset, 0], axis=1)
                .reshape(16, -1)
                .max(axis=1)
                for delta, offset in corners
            ],
            axis=0,
        )
        A, B, C, E = original
        extremes = np.array(
            [A + lower * B, A + upper * B, C + lower * E, C + upper * E]
        )
        return np.r_[absolute, relative_tiles] + 1e-7, radius_bound(extremes)
    raise ValueError("Cannot verify a scale enclosure")


def main():
    output = {}
    grid = np.linspace(0, STROKE, N)
    for name in NET_PIN:
        x, _, z = routes[name]["tap_center_mm"]
        fixed = controls(name, x, z, 0)
        pieces = (SUBDIV @ fixed).reshape(SUB, DEGREE + 1, 3)
        target_lo = np.linalg.norm(pieces[:, -1] - pieces[:, 0], axis=1).sum()
        target_hi = polygon_length(pieces)
        maximum = np.zeros(17)
        selfgap = 999.0
        min_radius = 999.0
        for i, at in enumerate(grid):
            limits = (
                [max(at - STROKE / (N - 1) / 2, 0), at],
                [at, min(at + STROKE / (N - 1) / 2, STROKE)],
            )
            for left, right in limits:
                if left < right:
                    motion, radius = bounds(name, left, right, at, target_lo, target_hi)
                    maximum = np.maximum(maximum, motion)
                    min_radius = min(min_radius, radius)
            pp = PROBE @ controls(name, x, z, at)
            stub = np.linspace(pp[0] - [0, CRIMP_STUB, 0], pp[0], 36)
            pt = np.concatenate([stub[:-1], pp])
            segment = np.linalg.norm(np.diff(pt, axis=0), axis=1)
            s = np.r_[0, np.cumsum(segment)]
            delta = pt[:, None, :] - pt[None, :, :]
            dis = np.sum(delta * delta, axis=-1)
            dis[np.abs(s[:, None] - s) < 4.5] = 1e10
            selfgap = min(selfgap, np.sqrt(dis.min()) - 1.42)
        output[name] = dict(
            maximum_centerline_displacement_from_nearest_station_mm=round(
                maximum[0], 7
            ),
            maximum_free_centerline_motion_relative_to_moving_plug_mm=round(
                max(maximum[1:]), 7
            ),
            relative_displacement_by_sixteen_equal_bezier_parameter_intervals_mm=np.round(
                maximum[1:], 7
            ).tolist(),
            continuous_centerline_bend_radius_lower_bound_mm=round(
                min_radius - 0.000001, 6
            ),
            minimum_sampled_self_gap_for_centerline_arc_separation_at_least_4p5_mm=round(
                selfgap, 6
            ),
            reference_length_bounds_mm=[round(target_lo, 7), round(target_hi, 7)],
        )
        print(name, output[name], flush=True)
    result = dict(
        form_sha256=hashlib.sha256((HERE / "loop-forms.json").read_bytes()).hexdigest(),
        station_count=N,
        travel_pitch_mm=STROKE / (N - 1),
        wire=output,
        scope="Continuous centerline travel bound, including the straight translating stub. Applies directly to round swept envelopes about the centerline. The separate minimum jacket-to-part mesh distances also include flat end caps; an independent cap comparison is needed to use those distances as certified sphere-envelope clearances. Self distances are sampled, with adjacent portions excluded by arc length.",
    )
    (HERE / "motion-bound.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
