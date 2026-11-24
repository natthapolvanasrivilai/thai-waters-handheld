"""Verify slide-in order with the optical parts, lamp, shelf and speaker present."""
import json,sys
from pathlib import Path
import cadquery as cq
from interfaces import HERE,box
from service import swept
from mount import b,near
from gauges import other
def run(cache, housing_path=None, report_path=None):
    def read(n):
        path = housing_path if n == 'housing' and housing_path else HERE/(n+'.step')
        return cq.importers.importStep(str(path)).val()
    shell,shelf,lens,lamp=map(read,['housing','shelf','diffuser','rgb-gauge'])
    spk=other(cache)[0]; report={}
    def record(name,parts,targets):
        hits={}
        for part in parts:
            for k,t in targets.items():
                if near(b(part),b(t)):
                    v=part.intersect(t).Volume()
                    if v>1e-5:hits[k]=max(hits.get(k,0),round(v,5))
        report[name]=hits;print(name,hits,flush=True)
    def rectpath(q,vec):
        a=b(q);offset=list(vec);return box(*[a[2*i]+min(0,offset[i]) for i in range(3)],*[a[2*i+1]+max(0,offset[i]) for i in range(3)])
    # The lens is inserted before the shelf and speaker. Sweep the two actual
    # rectangular prisms separately to preserve the stepped shoulder.
    pieces=[box(-49.95,-1.05,12.30,-43.05,1.05,13.90),box(-44.20,-1.75,11.52,-43.65,1.75,13.90)]
    record('diffuser_lower_22mm_inboard',[rectpath(q.translate((22,0,0)),(0,0,24)) for q in pieces],{'shell':shell})
    record('diffuser_outward_22mm',[rectpath(q,(22,0,0)) for q in pieces],{'shell':shell})
    targets={'shell':shell,'diffuser':lens,'speaker gauge':spk}
    for n,off,vec in [('shelf_lower',(14,0,0),(0,0,24)),('shelf_outward',(0,0,0),(14,0,0))]:
        record(n,swept(shelf.translate(off),vec),targets)
    board=cq.Shape.importBrep(str(cache/'USB-PCB1.brep'))
    led=box(board.BoundingBox().xmin-.7,-.8,12.3,board.BoundingBox().xmin,.8,13.9)
    targets['shelf']=shelf
    record('lamp_lower_at_service_end',[rectpath(q.translate((0,-18,0)),(0,0,24)) for q in (board,led)],targets)
    record('lamp_slide_18mm',[rectpath(q,(0,-18,0)) for q in (board,led)],targets)
    (report_path or HERE/'light-motion.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not any(report.values()),report
if __name__=='__main__':run(Path(sys.argv[1]))
