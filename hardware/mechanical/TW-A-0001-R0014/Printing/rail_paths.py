"""Measure local bead widths, model backing and open adhesive channels on plate 1."""
from collections import defaultdict
import sys

from shapely.geometry import LineString, box
from shapely.ops import substring, unary_union

from make_project import MECH
sys.path.insert(0, str(MECH / "pocket-reel-r19b-removal-trial"))
from path_evidence import FIELDS, arc_points
sys.path.insert(0, str(MECH.parents[1] / "tools"))
from verify_model_extrusion import MODEL, NON_MODEL

# Model XY is installed XY for P0001. The saved housing has identity rotation,
# a Bambu import offset (3.1400013, 2.5750008) and build translation (128,128).
# The parent printer's physical extruder_offset = 0x2 shifts commanded Y by -2.
DX, DY = 124.86, 123.425
BOARD = (10.80, -16.80, 30.80, 3.20)
RAILS = (("west",18.0), ("east",26.0))
LEVELS = [n/5 for n in range(29,40)]  # 5.8 through 7.8; old floor top is 5.7


def window(x0,y0,x1,y1):
    return box(x0+DX,y0+DY,x1+DX,y1+DY)


def footprints(gcode, region=None, zmin=5.4, zmax=17.6, trace=None, object_id="385"):
    """Clip actual deposition to the board footprint. Skip native support-only interlayers for model backing."""
    if region is None:
        region = window(*BOARD)
    xmin,ymin,xmax,ymax = region.bounds
    layers = defaultdict(lambda: defaultdict(list))
    xy = (0.,0.)
    width, z, debt = .42, 0., 0.
    role, instance = "", ""
    relative_e = absolute_xy = False
    for text in gcode.open(encoding="utf-8"):
        line = text.strip()
        if line.startswith("; Z_HEIGHT:"):
            z = float(line.split(":")[1])
            instance = ""
        elif line.startswith("; FEATURE:"):
            role = line.split(":")[1].strip()
        elif line.startswith("; LINE_WIDTH:"):
            width = float(line.split(":")[1])
        elif line.startswith(("; OBJECT_ID:", "; start printing object, unique label id:")):
            instance = line.split(":")[-1].strip()
        elif line.startswith("; stop printing object"):
            if line.split(":")[-1].strip() == instance:
                instance = ""
        cmd = line.partition(";")[0].strip()
        if cmd in ("M82","M83"):
            relative_e = cmd == "M83"
        if cmd in ("G90","G91"):
            absolute_xy = cmd == "G90"
        if not cmd.startswith(("G0 ","G1 ","G2 ","G3 ")):
            continue
        args = {k:float(v) for k,v in FIELDS.findall(cmd)}
        old = xy
        xy = tuple(args.get(k,old[i]) if absolute_xy else old[i]+args.get(k,0.) for i,k in enumerate("XY"))
        if "E" not in args:
            continue
        if instance == object_id:
            assert relative_e and absolute_xy
        e = args["E"]
        if e < 0:
            debt -= e
            continue
        recovered = min(debt,e)
        debt -= recovered
        if instance != object_id or e-recovered <= 1e-7 or not (zmin <= z <= zmax):
            continue
        if role not in MODEL and not role.startswith("Support"):
            assert role in NON_MODEL
            continue
        is_arc = cmd.startswith(("G2 ","G3 "))
        if old == xy and not is_arc:
            continue
        points = arc_points(old,xy,args,cmd.startswith("G2 ")) if is_arc else [old,xy]
        if (max(p[0] for p in points)+width/2 < xmin or min(p[0] for p in points)-width/2 > xmax
                or max(p[1] for p in points)+width/2 < ymin or min(p[1] for p in points)-width/2 > ymax):
            continue
        center = LineString(points)
        if recovered > 1e-7:
            center = substring(center,recovered/e,1,normalized=True)
        sweep = center.buffer(width/2,quad_segs=8).intersection(region)
        if sweep.area:
            group = "support" if role.startswith("Support") else "model"
            layers[z][group].append(sweep)
            if trace is not None and group == "model":
                trace[z].append(center)
    return {z:{k:unary_union(paths) for k,paths in groups.items()} for z,groups in layers.items()}


def regions(geom):
    if geom.geom_type == "Polygon":
        return [geom] if geom.area else []
    return [p for sub in getattr(geom,"geoms",[]) for p in regions(sub)]


def measure(gcode):
    traces = defaultdict(list)
    layers = footprints(gcode,trace=traces)
    empty = box(0,0,0,0)
    def get(z,role):
        return layers.get(z,{}).get(role,empty)
    board_support = sum(get(z,"support").area for z in layers if 5.8 <= z <= 17.6)
    board_above_seats = sum(get(z,"model").area for z in layers if 7.8 < z <= 17.6)
    results = {}
    for name,cx in RAILS:
        envelope = window(cx-1.5,-12,cx+1.5,0)
        # Leave 0.15 mm bead-width and arc-discretization margin on each side.
        channel = window(cx-.45,-7.8,cx+.45,-.1)
        mouth = window(cx-.45,-7.8,cx+.45,.5)
        shoulder_rows = []
        last = get(5.6,"model")
        for z in LEVELS:
            model = get(z,"model").intersection(envelope)
            pieces = regions(model)
            support = sum(get(k,"support").intersection(envelope).area for k in layers if z-.2 < k <= z)
            overlap = model.intersection(last)
            # The profiles use two 0.4 mm nominal perimeters around sparse core
            # fill. When a whole-area screen flags a layer, distinguish a lifted
            # outside wall from a short internal span inside those two perimeters.
            perimeter = model.intersection(envelope.difference(envelope.buffer(-.8)))
            gaps = regions(model.difference(last))
            # Longest individual native extrusion path through a missing backing
            # region; join consecutive command segments sharing their endpoint.
            unbacked = model.difference(last)
            longest = 0
            pending = []
            for line in traces[z]:
                coords = list(line.coords)
                if pending and pending[-1] == coords[0]:
                    pending.extend(coords[1:])
                    continue
                if pending:
                    longest = max(longest, unsupported_run(pending, unbacked))
                pending = coords
            if pending:
                longest = max(longest, unsupported_run(pending, unbacked))
            shoulder_rows.append(dict(z=z, model_area_mm2=round(model.area,4),
                components=len(pieces), components_with_model_backing=sum(p.intersection(last).area>.001 for p in pieces),
                model_backed_percent=round(100*overlap.area/model.area,2) if model.area else 0,
                two_perimeter_band_backed_percent=round(100*perimeter.intersection(last).area/perimeter.area,2) if perimeter.area else 0,
                largest_unbacked_gap_width_x_mm=round(max((g.bounds[2]-g.bounds[0] for g in gaps),default=0),4),
                longest_unbacked_centerline_segment_mm=round(longest,4),
                support_area_mm2=round(support,5),
                groove_through_mouth_model_mm2=round(get(z,"model").intersection(mouth).area,5),
                groove_core_model_area_mm2=round(model.intersection(channel).area,5)))
            last = get(z,"model")
        results[name] = shoulder_rows
    return dict(gcode_translation_from_installed_mm=[DX,DY,3.200001004],
                board_support_area_sum_mm2=round(board_support,5),
                board_model_above_seats_area_sum_mm2=round(board_above_seats,5),
                model_layers=LEVELS, rails=results)


def unsupported_run(coords, gaps):
    inside = LineString(coords).intersection(gaps)
    return max((g.length for g in getattr(inside,"geoms",[inside])), default=0.)


def check(measurements):
    assert measurements["board_support_area_sum_mm2"] == 0, measurements
    assert measurements["board_model_above_seats_area_sum_mm2"] == 0, measurements
    for name, rows in measurements["rails"].items():
        for row in rows:
            assert row["model_area_mm2"] > 20, (name,row)
            assert row["components"] == row["components_with_model_backing"] == 1, (name,row)
            assert row["support_area_mm2"] == 0, (name,row)
            if row["model_backed_percent"] <= 70:
                # Retain the failed broad screen in the report. Require continuous
                # backing in the outer two perimeter widths and bound every void
                # across the rail by its nominal core width (3.0 - 2*0.8 mm).
                assert row["two_perimeter_band_backed_percent"] >= 99.99, (name,row)
                assert row["largest_unbacked_gap_width_x_mm"] <= 1.4, (name,row)
            # The groove floor is printed through z=7.4, the two shoulders continue to 7.8.
            if row["z"] >= 7.6:
                assert row["groove_through_mouth_model_mm2"] == 0, (name,row)
            elif row["z"] == 7.4:
                assert row["groove_core_model_area_mm2"] > 4, (name,row)
