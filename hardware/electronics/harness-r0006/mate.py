"""Form W4's four service leads with both the display stack and W1 seated.

Distances are millimetres. The stored form parameters define each degree-seven
Bezier guide relative to the unchanged crimp and overcoat datums of R0005.
"""

import importlib.util
import json
import math
from functools import lru_cache
from pathlib import Path
import sys

import cadquery as cq
import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
BASE = HERE.with_name("harness-r0005")
if str(BASE) not in sys.path:
    sys.path.append(str(BASE))
spec = importlib.util.spec_from_file_location("w4_r0005", BASE / "mate.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
from geometry import V, sweep

NET_PIN, TAP_Y, JACKET_OD, STROKE = (
    base.NET_PIN,
    base.TAP_Y,
    base.JACKET_OD,
    base.STROKE,
)
RELEASE_DEG, PIVOT, actuate, split_latch = (
    base.RELEASE_DEG,
    base.PIVOT,
    base.actuate,
    base.split_latch,
)
arc_length = base.arc_length
FREE_START_Y = 0.25
CRIMP_STUB = FREE_START_Y + 5.35


def endpoints(net, tx, z, travel=0):
    start, end = base.endpoints(net, tx, z, travel)
    start[1] = FREE_START_Y + travel
    return start, end


FORM = json.loads((HERE / "loop-forms.json").read_text())
T, WEIGHTS = np.polynomial.legendre.leggauss(96)
T, WEIGHTS = 0.5 * (T + 1), 0.5 * WEIGHTS


def bernstein(degree, t):
    t = np.asarray(t)
    return np.stack(
        [
            math.comb(degree, i) * (1 - t) ** (degree - i) * t**i
            for i in range(degree + 1)
        ],
        axis=-1,
    )


DEGREE = 7
KNOTS = np.linspace(0, 1, DEGREE + 1)
TO_POLES = np.linalg.inv(bernstein(DEGREE, KNOTS))
SPEED_BASIS = DEGREE * bernstein(DEGREE - 1, T)


def base_poles(net, tx, z, travel):
    """Bezier coefficients before the constant-length bow correction."""
    a, b = endpoints(net, tx, z, travel)
    p = FORM[net]
    r = travel / STROKE
    tangent_start = p[6] * (1 - r) + p[8] * r
    tangent_end = p[7] * (1 - r) + p[9] * r
    c = a + [0, tangent_start, 0]
    e = b + [0, -0.70 * tangent_end, tangent_end]
    cubic = bernstein(3, KNOTS) @ np.array([a, c, e, b])
    t = KNOTS[:, None]
    belly = 16 * t * t * (1 - t) ** 2
    shift = [p[0] + r * p[14], p[4] + r * p[13], p[2] + r * p[11]]
    tilt = [p[1] + r * p[10], p[5], p[3] + r * p[12]]
    u = 2 * t - 1
    quadratic = np.array(p[15:18]) + r * np.array(p[21:24])
    cubic_tilt = np.array(p[18:21]) + r * np.array(p[24:27])
    form = TO_POLES @ (
        cubic + belly * (shift + u * tilt + u**2 * quadratic + u**3 * cubic_tilt)
    )
    # A short reference curve shares both endpoints and tangent directions.
    # Scaling from it preserves the contact and tap axes at every position.
    reference = TO_POLES @ (
        bernstein(3, KNOTS) @ np.array([a, a + [0, 2, 0], b + [0, -1.4, 2], b])
    )
    return reference, form - reference


def free_length(poles):
    return WEIGHTS @ np.linalg.norm(SPEED_BASIS @ np.diff(poles, axis=0), axis=1)


@lru_cache(maxsize=4096)
def controls(net, tx, z, travel):
    raw, correction = base_poles(net, tx, z, travel)
    if travel == 0:
        return raw + correction
    target = free_length(controls(net, tx, z, 0))

    def residual(q):
        return free_length(raw + q * correction) - target

    # Arc length is convex in the scale. A reference shorter than the target
    # and a bracket above it give one positive root throughout the stroke.
    amplitude = brentq(residual, 0.0, 40.0, xtol=1e-12)
    return raw + amplitude * correction


def guide(net, tx, z, travel, count=49):
    return (
        bernstein(DEGREE, np.linspace(0, 1, count)) @ controls(net, tx, z, travel)
    ).tolist()


def loop_edge(net, tx, z, travel):
    return cq.Edge.makeBezier([V(*p) for p in controls(net, tx, z, travel)])


def jacket(net, tx, z, travel=0):
    edge = loop_edge(net, tx, z, travel)
    tip = edge.startPoint()
    start = V(tip.x, -5.35 + travel, tip.z)
    path = cq.Wire.assembleEdges([cq.Edge.makeLine(start, tip), edge])
    return sweep(path, JACKET_OD / 2), CRIMP_STUB + arc_length(edge)
