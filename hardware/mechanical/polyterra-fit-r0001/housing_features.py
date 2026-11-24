"""Check the status window and two rear screw passages in the PLA toolpaths."""
from pathlib import Path
import json,sys
from shapely.geometry import Point,box
from project import HERE
sys.path.insert(0,str(HERE.parent/'TW-A-0001-R0014/Printing'))
from rail_paths import footprints, DX,DY
def run(gcode):
    rows=[]
    # Check a centre patch inside the status aperture and inside the narrower
    # rear screw shanks across the usable height, excluding their transition faces.
    features=[('Status aperture',box(DX-49.9,DY-1.05,DX-44.25,DY+1.05),15.6,17.0)]
    for y in (-24,24):
        features.append((f'Rear driver {y:+}',Point(DX+51,DY+y).buffer(2.02),3.8,25.55))
        features.append((f'Rear screw {y:+}',Point(DX+51,DY+y).buffer(1.0),26.05,28.70))
    for x in (-36,36):
        for y in (-24.25,24.25):
            features.append((f'Controller access {x:+} {y:+}',Point(DX+x,DY+y).buffer(2.02),3.8,12.2))
    features.append(('Key opening centre',box(DX-37.5,DY+33.65,DX-34.5,DY+33.9),14.6,16.9))
    for y in (-18,18):
        features.append((f'Hook pocket {y:+}',box(DX-47.84,DY+y-1.5,DX-46.9,DY+y+1.5),28.1,30.7))
    for label,region,lo,hi in features:
        # Include a surrounding rim as a positive control for layer registration.
        paths=footprints(gcode,region.buffer(3),lo,hi,object_id='385')
        max_model=max((q['model'].intersection(region).area for q in paths.values() if 'model' in q),default=0)
        max_support=max((q['support'].intersection(region).area for q in paths.values() if 'support' in q),default=0)
        model_layers=sum('model' in q for q in paths.values())
        rows.append(dict(feature=label,rim_model_layers=model_layers,maximum_model_in_opening_mm2=round(max_model,4),maximum_support_in_opening_mm2=round(max_support,4)))
    print(rows,flush=True)
    (HERE/'housing-features.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert all(r['rim_model_layers'] and r['maximum_model_in_opening_mm2']<.001 and r['maximum_support_in_opening_mm2']<.001 for r in rows)
if __name__=='__main__':run(Path(sys.argv[1]))
