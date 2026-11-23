"""Run with KiCad Python to compare fixed A3 features and package clearances."""
import hashlib
import json
import math
from pathlib import Path

import pcbnew as pcb

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "pcb-haptic-cie-r0001/A3-CIE-R0001.kicad_pcb"
NEW = HERE / "A3-CIE-R0002.kicad_pcb"


def point(v):
    return (v.x, v.y)


def perimeter(board):
    outline = pcb.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(outline, False) and outline.OutlineCount() == 1
    ring = outline.COutline(0)
    pts = [point(ring.CPoint(i)) for i in range(ring.PointCount())]
    return sorted(tuple(sorted((a, b))) for a, b in zip(pts, pts[1:] + pts[:1]))


def pads(footprint):
    return sorted((p.GetNumber(), p.GetNetname(), point(p.GetPosition()), point(p.GetSize()),
                   point(p.GetDrillSize()), p.GetOrientationDegrees()) for p in footprint.Pads())


def project(board):
    ref = board.FindFootprintByReference
    header = ref("J1").GetCourtyard(pcb.F_CrtYd).BBox()
    result = {}
    for name in ("C1", "C2", "U1", "R1", "R2"):
        fp = ref(name)
        box = fp.GetCourtyard(pcb.F_CrtYd).BBox()
        dx = max(header.GetLeft() - box.GetRight(), box.GetLeft() - header.GetRight())
        dy = max(header.GetTop() - box.GetBottom(), box.GetTop() - header.GetBottom())
        result[name] = dict(xy_mm=[pcb.ToMM(v) for v in point(fp.GetPosition())],
                            rotation_deg=fp.GetOrientationDegrees(), dnp=fp.IsDNP(),
                            J1_bbox_separation_mm=round(math.hypot(max(0, dx), max(0, dy)) / 1e6, 5))
    return result


def run():
    prior, current = (pcb.LoadBoard(str(f)) for f in (OLD, NEW))
    assert perimeter(prior) == perimeter(current)
    for ref in ("J1", "TP1", "TP2"):
        a, b = (board.FindFootprintByReference(ref) for board in (prior, current))
        assert pads(a) == pads(b)
        assert a.GetCourtyard(pcb.F_CrtYd).BBox().Format() == b.GetCourtyard(pcb.F_CrtYd).BBox().Format()
    for fp in (HERE / "TW_Haptic.pretty").iterdir():
        assert fp.read_bytes() == (OLD.parent / "TW_Haptic.pretty" / fp.name).read_bytes()
    assert prior.GetDesignSettings().m_MinClearance == current.GetDesignSettings().m_MinClearance
    thickness = current.GetDesignSettings().GetBoardThickness()
    assert prior.GetDesignSettings().GetBoardThickness() == thickness
    settings = json.loads(NEW.with_suffix(".kicad_pro").read_bytes())["board"]["design_settings"]
    assert settings["rule_severities"]["courtyards_overlap"] == "error" and not settings["drc_exclusions"]
    historical = json.loads((OLD.parent / "drc.json").read_bytes())
    assert len(historical["violations"]) == 3
    assert {frozenset(i["description"] for i in v["items"]) for v in historical["violations"]
            if v["type"] == "courtyards_overlap"} == {frozenset(("Footprint J1", "Footprint " + ref))
                                                     for ref in ("C1", "R1", "U1")}
    original, revised = project(prior), project(current)
    assert all(r["J1_bbox_separation_mm"] > 0 for r in revised.values())
    assert all(original[r]["J1_bbox_separation_mm"] == 0 for r in ("C1", "R1", "U1"))
    assert {n for n, r in revised.items() if r["dnp"]} == {"R1", "R2"}
    return dict(old_sha256=hashlib.sha256(OLD.read_bytes()).hexdigest(),
                new_sha256=hashlib.sha256(NEW.read_bytes()).hexdigest(),
                board_thickness_mm=pcb.ToMM(thickness), matching_rounded_outline_segments=len(perimeter(current)),
                fixed_pad_positions_and_geometries=["J1", "TP1", "TP2"],
                unchanged_footprint_library=True, courtyard_rule="error", exclusions=[],
                original_placement=original, new_placement=revised)


if __name__ == "__main__":
    (HERE / "placement.json").write_text(json.dumps(run(), indent=2) + "\n", encoding="utf8")
