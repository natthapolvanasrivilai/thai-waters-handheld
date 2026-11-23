"""Check the keyed corners and four switch clearances in two independent Bambu slices."""
import json
import sys
from pathlib import Path

from shapely.geometry import Point, box
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.with_name("TW-A-0001-R0014")/"Printing"))
from rail_paths import footprints
from make_project import digest

def audit(folder):
    gcode=folder/"plate_1.gcode"
    summary=json.loads((folder/"result.json").read_bytes())
    plate=summary["sliced_plates"][0] if "sliced_plates" in summary else summary["plates"][0]
    assert len(plate["objects"])==1 and not plate["warning_message"]
    # 128,128 build centre, 0x2 physical extruder offset. +Z installed points to -Y here.
    cx,cy=128,126
    layers=footprints(gcode,box(cx-5,cy-5,cx+5,cy+5),0,2,object_id="391")
    rows={}
    for z,roles in sorted(layers.items()):
        assert "support" not in roles
        reach=3.40 if z<=.56 else 2.15  # Inside the rounded top edge, beyond the former circle.
        witness=Point(cx+reach,cy-reach).buffer(.09)
        coverage=roles["model"].intersection(witness).area/witness.area
        assert coverage>.80,(z,coverage)
        rows[z]=round(coverage,3)
    assert min(rows)==.20 and max(rows)>=1.26
    for x in (-2.15,2.15):
        for y in (-2.15,2.15):
            assert layers[.20]["model"].intersection(Point(cx+x,cy+y).buffer(.50)).area<1e-5
    return dict(layers_key_corner_fraction=rows,first_layer_rivet_witnesses_clear=4,
                support=False,gcode_sha256=digest(gcode),slicer_warnings=plate["warning_message"],
                estimated_seconds=round(plate["total_predication"]))
if __name__=="__main__":
    output=[audit(Path(p)) for p in sys.argv[1:]]
    assert len(output)==2 and output[0]["layers_key_corner_fraction"]==output[1]["layers_key_corner_fraction"]
    (HERE/"QA/native-print.json").write_text(json.dumps(dict(project_sha256=digest(
        HERE/"Print/R0017-keyed-power-cap-X1C.3mf"),slices=output),indent=2)+"\n")
