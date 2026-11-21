"""Verify native annotated FDM model-deposition bounds and optional local path witnesses."""

from argparse import ArgumentParser
from collections import defaultdict
from dataclasses import dataclass
from hashlib import file_digest
from io import TextIOWrapper
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

MODEL = frozenset({
    "Bottom surface", "Bridge", "External bridge", "Floating vertical shell",
    "Gap infill", "Inner wall", "Internal bridge", "Internal solid infill",
    "Ironing", "Outer wall", "Overhang wall", "Sparse infill", "Top surface",
})
NON_MODEL = frozenset({
    "Brim", "Custom", "Flush", "Prime tower", "Skirt", "Skirt/Brim", "Wipe tower",
    "Support", "Support interface", "Support transition",
})
TOOL = re.compile(r"^T(\d+)\s*$", re.I)
COMMAND = re.compile(r"^([GM])(\d+(?:\.\d+)?)\s*(.*)$", re.I)
LETTER = re.compile(r"([XYEIJR])\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))", re.I)
LAYER_TOLERANCE_MM = 0.0005
EPS = 1e-9
TAU = math.tau


class Unverified(ValueError):
    """Inputs do not establish the requested digital result."""


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise Unverified(f"{label} must be a finite number")
    return float(value)


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def unique(values, label):
    if len(set(values)) != len(values):
        raise Unverified(f"duplicate {label}")


def metadata(node, key):
    values = node.findall(f"metadata[@key='{key}']")
    if len(values) != 1 or not values[0].get("value"):
        raise Unverified(f"missing/ambiguous native metadata: {key}")
    return values[0].attrib["value"]


def instance_index(archive):
    root = ET.fromstring(archive.read("Metadata/model_settings.config"))
    definitions = root.findall("object")
    unique([o.attrib["id"] for o in definitions], "native object definition")
    names = {o.attrib["id"]: metadata(o, "name") for o in definitions}
    plates = {}
    for node in root.findall("plate"):
        plate = int(metadata(node, "plater_id"))
        if plate in plates:
            raise Unverified(f"duplicate native plate {plate}")
        rows = [(metadata(p, "identify_id"), names[metadata(p, "object_id")])
                for p in node.findall("model_instance")]
        unique([key for key, _ in rows], f"instance ID on plate {plate}")
        plates[plate] = dict(rows)
    return plates


def expected_plates(report, native):
    if type(report["return_code"]) is not int or report["return_code"] != 0:
        raise Unverified("native slicer did not report a successful return code")
    found = {}
    for plate in report["sliced_plates"]:
        k = plate["id"]
        if type(k) is not int or k < 1 or k in found or k not in native:
            raise Unverified(f"invalid, duplicate, or unmatched report plate {k}")
        if not isinstance(plate["warning_message"], str):
            raise Unverified(f"missing/invalid warning field for plate {k}")
        by_name = defaultdict(list)
        for key, name in native[k].items():
            by_name[name].append(key)
        objects = {}
        for obj in plate["objects"]:
            name = obj["name"]
            if not isinstance(name, str) or len(by_name[name]) != 1:
                raise Unverified(f"cannot uniquely match {name!r} on plate {k}")
            key, = by_name[name]
            if key in objects:
                raise Unverified(f"duplicate reported instance {key} on plate {k}")
            lower_mm = number(obj["bbox"]["z"], "bbox.z")
            height_mm = number(obj["bbox"]["height"], "bbox.height")
            if height_mm <= 0:
                raise Unverified(f"nonpositive mesh height for {name!r}")
            objects[key] = (name, lower_mm, lower_mm + height_mm)
        if not objects or objects.keys() != native[k].keys():
            raise Unverified(f"unmatched or empty native instances on plate {k}")
        found[k] = (objects, plate["warning_message"])
    if not found:
        raise Unverified("no plates reported")
    return found


@dataclass(frozen=True)
class Feature:
    plate: int
    instance: str
    name: str
    reference: str
    rectangle: tuple
    layers: tuple
    length: float


def read_features(path, plates):
    if path is None:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data["features"]:
        raise Unverified("explicit feature list cannot be empty")
    out = []
    for item in data["features"]:
        k, key = item["plate"], item["object_id"]
        name, reference = item["name"], item["reference"]
        if type(k) is not int or k not in plates or key not in plates[k][0]:
            raise Unverified("feature references an unknown plate/instance ID")
        if not all(isinstance(s, str) and s.strip() for s in (name, reference)):
            raise Unverified("feature requires a name and independent reference")
        x, y = item["xy_mm"]
        xmin, xmax = [number(v, "feature X") for v in x]
        ymin, ymax = [number(v, "feature Y") for v in y]
        if xmin >= xmax or ymin >= ymax:
            raise Unverified("feature XY window has empty interior")
        zs = tuple(sorted(number(v, "feature layer") for v in item["required_layers_z_mm"]))
        if not zs or zs[0] <= 0 or any(b - a <= 2 * LAYER_TOLERANCE_MM for a, b in zip(zs, zs[1:])):
            raise Unverified("feature layer heights must be positive, distinct and unambiguous")
        length = number(item["minimum_path_mm"], "feature minimum path")
        if length <= 0:
            raise Unverified("feature minimum path must be positive")
        out.append(Feature(k, key, name, reference, (xmin, xmax, ymin, ymax), zs, length))
    unique([(f.plate, f.instance, f.name) for f in out], "feature name for an instance")
    return out


def line_inside(a, b, rectangle):
    """Liang–Barsky-style intersection length for a line segment and an open rectangle."""
    lo, hi = 0.0, 1.0
    for p, q, m, n in zip(a, b, rectangle[::2], rectangle[1::2]):
        delta = q - p
        if abs(delta) <= EPS:
            if not m < p < n:
                return 0.0
            continue
        i, j = sorted(((m - p) / delta, (n - p) / delta))
        lo, hi = max(lo, i), min(hi, j)
    return max(0.0, hi - lo) * math.dist(a, b)


@dataclass(frozen=True)
class Arc:
    center: tuple
    radius: float
    theta: float
    sign: int
    sweep: float

    def inside(self, rectangle):
        """Partition at exact circle/rectangle intersections; ignore tangent contacts."""
        cx, cy = self.center
        bounds = [0.0, self.sweep]
        for edge, c, x_boundary in [(x, cx, True) for x in rectangle[:2]] + [
                (y, cy, False) for y in rectangle[2:]]:
            val = (edge - c) / self.radius
            if abs(val) > 1:
                continue
            phi = math.acos(val) if x_boundary else math.asin(val)
            options = (phi, -phi) if x_boundary else (phi, math.pi - phi)
            for angle in options:
                delta = (self.sign * (angle - self.theta)) % TAU
                if EPS < delta < self.sweep - EPS:
                    bounds.append(delta)
        low_x, high_x, low_y, high_y = rectangle
        total = 0.0
        bounds.sort()
        for a, b in zip(bounds, bounds[1:]):
            angle = self.theta + self.sign * (a + b) / 2
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            if low_x < x < high_x and low_y < y < high_y:
                total += (b - a) * self.radius
        return total


def arc_from(a, b, params, clockwise):
    if "R" in params or not ({"I", "J"} & params.keys()):
        raise Unverified("unsupported model arc: require relative I/J XY arc center")
    i, j = params.get("I", 0), params.get("J", 0)
    cx, cy = center = a[0] + i, a[1] + j
    radius = math.hypot(i, j)
    if radius <= EPS or abs(math.dist(b, center) - radius) > max(0.003, radius * 0.0001):
        raise Unverified("inconsistent native XY arc endpoints")
    theta = math.atan2(-j, -i)
    sign = -1 if clockwise else 1
    sweep = TAU if math.dist(a, b) <= EPS else (sign * (math.atan2(b[1] - cy, b[0] - cx) - theta)) % TAU
    return Arc(center, radius, theta, sign, sweep)


def scan(stream, objects, features):
    layers = defaultdict(dict)
    lengths = defaultdict(float)
    by_instance = defaultdict(list)
    for f in features:
        by_instance[f.instance].append(f)
    x = y = 0.0
    tool = "implicit"
    e_position = defaultdict(float)
    retract_debt = defaultdict(float)
    model_job_started = False
    unsupported_control = None
    z = height = None
    instance = role = ""
    xy_relative = False
    relative_e = None
    xy_plane, relative_arc_center = True, True
    for raw in stream:
        line = raw.strip()
        if line in ("; CHANGE_LAYER", "; LAYER_CHANGE"):
            instance, z, height = "", None, None
            model_job_started = True
        elif line.startswith("; Z_HEIGHT:"):
            z, instance = float(line.split(":", 1)[1]), ""
        elif line.startswith("; LAYER_HEIGHT:"):
            height = float(line.split(":", 1)[1])
        elif line.startswith("; OBJECT_ID:"):
            instance = line.split(":", 1)[1].strip()
        elif line.startswith("; FEATURE:"):
            role = line.split(":", 1)[1].strip()
        elif line.lower().startswith("; stop printing object, unique label id:"):
            # The next OBJECT_ID may already have been emitted before old-object stop.
            stopped = line.split(":", 1)[1].strip()
            if stopped == instance:
                instance = ""
        command = line.split(";", 1)[0].rstrip()
        if (selector := TOOL.fullmatch(command)):
            selected = selector.group(1)
            if model_job_started and selected != tool:
                unsupported_control = "mid-job tool change"
            tool = selected
            continue
        if not (m := COMMAND.match(command)):
            continue
        family, opcode, args = m.group(1).upper(), m.group(2), m.group(3)
        num = int(opcode) if "." not in opcode else None
        if family == "M":
            if model_job_started and num in {6, 600}:
                unsupported_control = f"tool/filament change (M{opcode})"
            if num in {82, 83}:
                relative_e = num == 83
            continue
        if opcode in {"90.1", "91.1"}:
            relative_arc_center = opcode == "91.1"
        elif num in {10, 11}:
            unsupported_control = "firmware retract/recover (G10/G11)"
        elif num in {17, 18, 19}:
            xy_plane = num == 17
        elif num == 20:
            raise Unverified("inch-mode G-code is unsupported")
        elif num in {90, 91}:
            xy_relative = num == 91
        elif num in {0, 1, 2, 3, 92}:
            p = {k.upper(): float(v) for k, v in LETTER.findall(args)}
            if num == 92:
                x, y = p.get("X", x), p.get("Y", y)
                if "E" in p:
                    e_position[tool] = p["E"]
                continue
            a = (x, y)
            x = p.get("X", 0) + x if xy_relative else p.get("X", x)
            y = p.get("Y", 0) + y if xy_relative else p.get("Y", y)
            b = (x, y)
            if "E" not in p:
                continue
            if relative_e is None:
                if instance in objects and role not in NON_MODEL and (a != b or num in {2, 3}):
                    raise Unverified(f"extrusion mode undefined for instance {instance}")
                if model_job_started:
                    unsupported_control = "extruder move without explicit M82/M83"
                continue
            if relative_e:
                extrusion = p["E"]
                e_position[tool] += extrusion
            else:
                extrusion = p["E"] - e_position[tool]
                e_position[tool] = p["E"]
            if extrusion < -EPS:
                retract_debt[tool] -= extrusion
                continue
            if extrusion <= EPS:
                continue
            # Feed-only and non-model moves also pay down outstanding retractions.
            paid = min(extrusion, retract_debt[tool])
            retract_debt[tool] -= paid
            if (instance not in objects or (a == b and num not in {2, 3})
                    or role in NON_MODEL):
                continue
            if unsupported_control:
                raise Unverified(f"unsupported extrusion control: {unsupported_control}")
            if role not in MODEL:
                raise Unverified(f"unknown deposition role for instance {instance}: {role!r}")
            if extrusion - paid <= EPS:
                continue
            recovery_ratio = paid / extrusion
            if z is None or height is None or not all(math.isfinite(n) and n > 0 for n in (z, height)):
                raise Unverified(f"invalid layer markers for instance {instance}")
            arc = None
            if num in {2, 3}:
                if not xy_plane:
                    raise Unverified("non-XY model arc")
                if not relative_arc_center:
                    raise Unverified("absolute model arc center mode (G90.1) is unsupported")
                arc = arc_from(a, b, p, num == 2)
                if arc.sweep <= EPS:
                    continue
                arc = Arc(arc.center, arc.radius, arc.theta + arc.sign * arc.sweep * recovery_ratio,
                          arc.sign, arc.sweep * (1 - recovery_ratio))
            elif recovery_ratio:
                a = tuple(x + (y - x) * recovery_ratio for x, y in zip(a, b))
            # Native adaptive features can use several thicknesses at one Z.
            hmin, hmax = layers[instance].get(z, (height, height))
            layers[instance][z] = min(hmin, height), max(hmax, height)
            for f in by_instance[instance]:
                for target in f.layers:
                    if abs(z - target) <= LAYER_TOLERANCE_MM:
                        length = arc.inside(f.rectangle) if arc else line_inside(a, b, f.rectangle)
                        lengths[(f.name, instance, target)] += length
        elif model_job_started:
            fields = {field.upper() for field, _ in LETTER.findall(args)}
            if fields & {"E", "X", "Y"} or num in {5, 28, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 68, 69}:
                # Standalone dwell and ordinary startup positioning are safe. If
                # an unknown in-job move might carry deposition, do not even
                # accept earlier measurements as complete.
                if instance in objects and "E" in fields and role not in NON_MODEL:
                    raise Unverified(f"unsupported model motion G{opcode}")
                unsupported_control = f"unsupported coordinate or extrusion motion G{opcode}"
    return layers, lengths


def audit(project, native_report, features_path, tolerance):
    report = json.loads(native_report.read_text(encoding="utf-8"))
    with ZipFile(project) as archive:
        plates = expected_plates(report, instance_index(archive))
        features = read_features(features_path, plates)
        checks, local, warnings = [], [], []
        for plate, (objects, warning) in plates.items():
            if warning.strip():
                warnings.append({"plate": plate, "warning": warning})
            f_by_plate = [f for f in features if f.plate == plate]
            with archive.open(f"Metadata/plate_{plate}.gcode") as raw, TextIOWrapper(raw, encoding="utf-8") as stream:
                layers, lengths = scan(stream, objects, f_by_plate)
            for instance, (name, bottom, top) in objects.items():
                check = dict(plate=plate, name=name, object_id=instance,
                             mesh_bottom_mm=bottom, mesh_top_mm=top)
                data = layers[instance]
                if not data:
                    checks.append(dict(check, status="hold", reason="no model deposition"))
                    continue
                z0, z1 = min(data), max(data)
                bottom_tol, top_tol = ((tolerance, tolerance) if tolerance is not None else
                                       (max(data[z0][0] + .03, .27), max(data[z1][0] + .03, .27)))
                actual_bottom = z0 - data[z0][1]
                ok = abs(actual_bottom - bottom) <= bottom_tol + EPS and abs(z1 - top) <= top_tol + EPS
                checks.append(dict(check, model_bottom_mm=round(actual_bottom, 6), model_top_mm=z1,
                                   model_layers=len(data), bottom_tolerance_mm=bottom_tol,
                                   top_tolerance_mm=top_tol, status="pass" if ok else "hold"))
            for f in f_by_plate:
                layers_for_feature = []
                for z in f.layers:
                    length = lengths[(f.name, f.instance, z)]
                    layers_for_feature.append(dict(z_mm=z, path_mm=round(length, 6),
                                                   status="pass" if length + EPS >= f.length else "hold"))
                ok = all(r["status"] == "pass" for r in layers_for_feature)
                local.append(dict(plate=plate, object_id=f.instance, name=f.name, reference=f.reference,
                                  minimum_path_mm=f.length, layers=layers_for_feature,
                                  status="pass" if ok else "hold"))
    ok = not warnings and all(r["status"] == "pass" for r in checks + local)
    inputs = dict(sliced_3mf_sha256=digest(project), native_report_sha256=digest(native_report))
    if features_path:
        inputs["features_sha256"] = digest(features_path)
    return dict(status="pass" if ok else "hold", inputs=inputs, warnings=warnings, objects=checks,
                features=local, scope="digital planned model paths only, not physical print acceptance")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("sliced_3mf", type=Path)
    parser.add_argument("native_report", type=Path)
    parser.add_argument("--features", type=Path)
    parser.add_argument("--height-tolerance-mm", type=float)
    args = parser.parse_args()
    try:
        t = args.height_tolerance_mm
        if t is not None and (not math.isfinite(t) or t < 0):
            raise Unverified("height tolerance must be a finite, nonnegative number")
        result = audit(args.sliced_3mf, args.native_report, args.features, t)
        rc = 0 if result["status"] == "pass" else 1
    except (ValueError, TypeError, KeyError, AttributeError, OSError, BadZipFile, ET.ParseError) as e:
        result = {"status": "unverified", "reason": str(e)}
        rc = 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
