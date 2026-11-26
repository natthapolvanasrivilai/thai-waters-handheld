"""Measure retained model backing where the support exclusions cross a roof."""
from pathlib import Path
import sys,json
from project import HERE
from housing_features import DX,DY,Point,box,footprints
def inspect(g):
    rear=lambda y:Point(DX+51,DY+y).buffer(2.8)
    cases=[('status window',box(DX-50.02,DY-2,DX-47.7,DY+2),17.6),
           ('USB opening above the window',box(DX-50,DY-8,DX-47.7,DY+8),26.8),
           ('rear left screw shoulder',rear(-24),26.),('rear right screw shoulder',rear(24),26.)]
    rows=[]
    for label,roi,z in cases:
        layers=footprints(g,roi,z-.61,z+.001)
        cur=layers[z]['model'];previous=layers[round(z-.2,2)]
        # A support interface intentionally ends below the bridge. Include it
        # only as a separate measurement; contact to prior model is mandatory.
        overlap=cur.intersection(previous['model']).area
        rows.append(dict(feature=label,z_mm=z,model_mm2=round(cur.area,3),backed_by_prior_model_mm2=round(overlap,3),added_span_mm2=round(cur.area-overlap,3)))
    print(rows,flush=True)
    assert all(r['backed_by_prior_model_mm2']>1 and r['added_span_mm2']>1 for r in rows)
    (HERE/'roof-paths.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':inspect(Path(sys.argv[1]))
