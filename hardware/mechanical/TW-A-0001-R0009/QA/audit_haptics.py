"""Compare every R0009 placed haptic member against assembled and mating geometry."""
import argparse,json,sys,itertools
from pathlib import Path
import cadquery as cq
QA=Path(__file__).resolve().parent
REV=QA.parent
HARD=REV.parents[1]
sys.path.insert(0,str(REV.with_name('TW-A-0001-R0008')/'QA'))
from audit_fit import IDS,possible,bounds
p=argparse.ArgumentParser();p.add_argument('--cache',required=True,type=Path);a=p.parse_args()
def read(p):return cq.Shape.importBrep(str(p))
def bins(sh):return [(s,bounds(s)) for s in sh.Solids()]
def vol(aa,bb):
    return sum(sum(x.Volume() for x in a.intersect(b).Solids()) for a,ab in aa for b,bx in bb if possible(ab,bx))
h={p.stem:read(p) for p in (HARD/'electronics/haptic-r0009/placed').glob('*.brep')}
o={p.stem:read(p) for p in a.cache.glob('*.brep') if p.stem not in h}
o.update({name:read(REV/'CAD'/(stem+'.brep')) for stem,name in IDS.items()})
o.update({p.stem:read(p) for p in (HARD/'electronics/usb-status-r0003/placed').glob('*.brep')})
loom=HARD/'electronics/harness-r0003/placed'
o.update({p.stem:read(p) for p in loom.glob('w1*.brep')})
hb={k:bins(s) for k,s in h.items()};ob={k:bins(s) for k,s in o.items()}
hits={}
for k in h:
    for n in o:
        v=vol(hb[k],ob[n])
        if v>.0001:hits[k+' / '+n]=round(v,6)
for k,n in itertools.combinations(h,2):
    v=vol(hb[k],hb[n])
    if v>.0001:hits[k+' / '+n]=round(v,6)
print(hits,flush=True)
(QA/'haptic-contacts.json').write_text(json.dumps(hits,indent=2)+'\n')
