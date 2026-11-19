"""Recheck the released battery corridor and mechanism against the R0009 housing and hardware."""
import argparse,itertools,json,sys
from pathlib import Path
import cadquery as cq
Q=Path(__file__).resolve().parent;R=Q.parent;H=R.parents[1]
sys.path.insert(0,str(R.with_name("TW-A-0001-R0008")/"QA"))
import audit_fit as fit
sys.path.insert(0,str(R));import speaker
p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);a=p.parse_args()
def read(p):return cq.Shape.importBrep(str(p))
old={p.stem:read(p) for p in a.cache.glob('*.brep')}
for stem,k in fit.IDS.items():old[k]=read(R.with_name("TW-A-0001-R0008")/'CAD'/(stem+'.brep'))
new=old.copy()
for stem,k in fit.IDS.items():new[k]=read(R/'CAD'/(stem+'.brep'))
for f in [*(H/'electronics/haptic-r0009/placed').glob('*.brep'),*(H/'electronics/usb-status-r0003/placed').glob('*.brep'),*(H/'components/standard-fasteners/placed').glob('*.brep'),*(H/'components/gobilda-2800-0003-0010').glob('*.brep'),*(H/'components/radial-8995').glob('*.brep'),*(H/'components/reel-fasteners/placed').glob('*.brep'),*(H/'electronics/power-key-r0009').glob('*.brep')]:new[f.stem]=read(f)
new['Speaker']=cq.Compound.makeCompound(list(speaker.speaker_parts().values()))
for stem in ('usb-c-shield-mask','status-usb-guide','status-charge-guide','status-power-guide'):
    new[stem]=read(R/'CAD'/(stem+'.brep'))
q=fit.battery_qualification(new)
additional={}
def prism(s):
    b=s.BoundingBox()
    return cq.Solid.makeBox(b.xlen,b.ylen,40-b.zmin,cq.Vector(b.xmin,b.ymin,b.zmin))
for k in ('Cell','cellDrawing','cellAlt'):
    path=cq.Compound.makeCompound([prism(s) for s in new[k].Solids()])
    additional[k]={n:fit.round_volume(fit.overlap(path,v)) for n,v in new.items() if n not in old or n in ('whVCC','whGND','whSDA','whSCL','wm0','wm1','drvParts')}
q['additional_insertion_obstacles_mm3']=additional
(Q/'battery-fit.json').write_text(json.dumps(q,indent=2)+'\n')
print('Battery fit',additional,flush=True)
# Motion audit uses only additional shell material. Source/receiver screw variants have a
# separate absolute contact and retention test in components/standard-fasteners/verify.py.
added={'Housing':new['Housing'].cut(old['Housing']).clean()}
# Fully exercise new reel hardware in all relative poses. A cylinder centred on
# the hinge is invariant when the stem turns about Z. Washers and screw heads
# on that axis have only the nominal axial bearing contacts.
for k in ('reel0','reel1','reel2','H3-1','H3-2','H5'):
    added[k]=new[k]
moving,stops=fit.mechanism(old,new,added)
(Q/'mechanism.json').write_text(json.dumps(dict(motion_against_shell_gain_and_real_reel_hardware=moving,installed_stops_mm3=stops),indent=2)+'\n')
