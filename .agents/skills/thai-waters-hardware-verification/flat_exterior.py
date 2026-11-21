"""Exact nominal plane/stock check. Uses CAD solids, not STL or print preview."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import cadquery as cq


def volume(shape):
    if not shape.isValid():
        raise ValueError("CAD boolean gave an invalid shape")
    return sum(q.Volume() for q in shape.Solids())


def number(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"{name} must be a finite number")
    return v


def footprint(v):
    if not isinstance(v, list) or len(v) != 2:
        raise ValueError("footprint_mm must be two ordered [lower, upper] intervals")
    for item in v:
        if not isinstance(item, list) or len(item) != 2 or number(item[1], "upper") <= number(item[0], "lower"):
            raise ValueError("footprint_mm must have positive area")
    return v


def text(v, name):
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{name} must be nonempty")
    return v


def exclusions(r, key, fp):
    names = set()
    out = r.get(key, [])
    if not isinstance(out, list):
        raise ValueError(f"{key} must be a list")
    for e in out:
        name = text(e["name"], "exclusion name")
        text(e["reason"], "exclusion reason/source")
        if name in names:
            raise ValueError(f"duplicate {key}: {name}")
        names.add(name)
        bounds = footprint(e["footprint_mm"])
        if not all(a <= x < y <= b for (a, b), (x, y) in zip(fp, bounds)):
            raise ValueError(f"exclusion outside its region: {name}")
    return out


def subtract(stock, cuts):
    return stock.cut(*cuts) if cuts else stock


def audit(shape, regions, volume_tol_mm3=1e-5):
    """Check signed protrusion and required stock as independent Booleans."""
    if not isinstance(regions, list) or not regions:
        raise ValueError("at least one named region is required")
    if not 0 <= number(volume_tol_mm3, "numerical volume tolerance") <= .001:
        raise ValueError("numerical volume tolerance must be between 0 and .001 mm³")
    if len(shape.Solids()) != 1 or volume(shape) <= 0:
        raise ValueError("supply one valid, exact part solid, not an assembly or mesh")
    rows = []
    names = set()
    for r in regions:
        name = text(r["name"], "region name")
        if name in names:
            raise ValueError(f"duplicate region: {name}")
        names.add(name)
        a = ("x", "y", "z").index(r["axis"])
        p = number(r["plane_mm"], "datum plane")
        s = number(r["outward"], "outward direction")
        depth = number(r["stock_depth_mm"], "inboard stock depth")
        if s not in (-1, 1) or depth <= 0:
            raise ValueError("outward must be ±1 and stock_depth_mm must be positive")
        fp = footprint(r["footprint_mm"])

        def prism(f, low, high):
            # Distances are signed along outward; CAD coordinate is p+s*d.
            normal = iter(sorted((p+s*low, p+s*high)))
            t = iter(f)
            xyz = [list(normal) if i == a else next(t) for i in range(3)]
            return cq.Solid.makeBox(*(hi-lo for lo, hi in xyz), cq.Vector(*(lo for lo, _ in xyz)))

        allowed = exclusions(r, "allowed_protrusions", fp)
        stock_openings = exclusions(r, "stock_openings", fp)
        height = max(0, s*(getattr(shape.BoundingBox(), r["axis"] + ("max" if s > 0 else "min"))-p))
        caps = [number(e["max_height_mm"], "approved maximum height") for e in allowed]
        if any(h <= 0 for h in caps):
            raise ValueError("approved maximum height must be positive")
        remaining = None
        if height > 1e-8:
            allowed_shapes = [prism(e["footprint_mm"], 0, h) for e, h in zip(allowed, caps)]
            remaining = subtract(shape.intersect(prism(fp, 0, height)), allowed_shapes)
        required = subtract(prism(fp, -depth, 0), [prism(e["footprint_mm"], -depth, 0) for e in stock_openings])
        if volume(required) <= volume_tol_mm3:
            raise ValueError(f"stock openings eliminate the verification region: {name}")
        missing = volume(required.cut(shape))
        outer = volume(remaining) if remaining is not None else 0
        surviving_solids = [q for q in remaining.Solids() if q.Volume() > volume_tol_mm3] if remaining is not None else []
        maximum = max((s*(getattr(q.BoundingBox(), r["axis"] + ("max" if s > 0 else "min"))-p) for q in surviving_solids), default=0)
        rows.append({
            "name": name, "axis": r["axis"], "plane_mm": p, "outward": s, "footprint_mm": fp,
            "stock_depth_mm": depth, "allowed_protrusions": allowed, "stock_openings": stock_openings,
            "required_stock_mm3": volume(required), "missing_stock_mm3": missing,
            "unexpected_outer_mm3": outer, "unexpected_outer_solids": len(surviving_solids),
            "max_unexpected_height_mm": maximum, "pass": outer <= volume_tol_mm3 and missing <= volume_tol_mm3,
        })
    return {"pass": all(r["pass"] for r in rows), "regions": rows, "numerical_volume_tol_mm3": volume_tol_mm3}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("part_file", type=Path)
    cli.add_argument("region_file", type=Path)
    a = cli.parse_args()
    try:
        ext = a.part_file.suffix.lower()
        if ext in (".step", ".stp"):
            roots = cq.importers.importStep(str(a.part_file)).vals()
            if len(roots) != 1:
                raise ValueError("supply one STEP root; isolate and identify the exact target solid")
            part = roots[0]
        elif ext == ".brep":
            part = cq.Shape.importBrep(str(a.part_file))
        else:
            raise ValueError("expected STEP/STP/BREP, not STL or 3MF")
        spec = json.loads(a.region_file.read_bytes())
        report = audit(part, spec["regions"])
        report.update({f"{k}_sha256": hashlib.sha256(f.read_bytes()).hexdigest() for k, f in (
            ("part", a.part_file), ("regions", a.region_file),
        )})
        print(json.dumps(report, indent=2))
    except Exception as exc:
        print(f"UNVERIFIED: {exc}", file=sys.stderr)
        return 2
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
