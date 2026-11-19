"""Section the actual spring leads against the carrier, and evaluate cap approach and travel."""
import argparse,json
from pathlib import Path
import cadquery as cq
Q=Path(__file__).resolve().parent;R=Q.parent;H=R.parents[1]
p=argparse.ArgumentParser();p.add_argument('--cache',required=True,type=Path);a=p.parse_args()
def read(p):return cq.Shape.importBrep(str(p))
def vol(s,t):return round(sum(x.Volume() for x in s.intersect(t).Solids()),6)
keys={p.stem:read(p) for p in (H/'components/omron-b3f-1002-g').glob('*.brep')}
legacy=read(a.cache/'Key PCB.brep')
pcb=read(H/'electronics/power-key-r0009/Key PCB.brep')
case,top,contacts=[keys[k] for k in ('Switch case','Switch plunger','Trimmed terminals')]
cap=read(R/'CAD/power-cap.brep');ret=read(R/'CAD/key-board-retainer-west.brep');hs=read(R/'CAD/housing-battery-bay.brep')
g=cap.distance(top)
j=dict(rest_cap_to_plunger_mm=round(g,6),legacy_1p10mm_drill_interference_mm3=vol(contacts,legacy),finished_bore_nominal_mm=1.00,terminals_to_pcb_interference_mm3=vol(contacts,pcb),case_to_pcb_interference_mm3=vol(case,pcb),pins=[])
for s in contacts.Solids():
 x=s.BoundingBox();j['pins'].append(dict(center_xz_mm=[round(s.Center().x,4),round(s.Center().z,4)],below_pcb_mm=round(pcb.BoundingBox().ymin-x.ymin,4),board_overlap_mm3=vol(s,pcb)))
# Vary the finished four-hole profile without moving the OEM spring legs.
plate=cq.Solid.makeBox(11.,1.,10.,cq.Vector(-41.5,27.65,7.5))
j['finished_hole_series']=[]
for diameter in (.95,.975,1.00,1.025,1.05):
    holes=[cq.Solid.makeCylinder(diameter/2,1.4,cq.Vector(x,27.45,z),cq.Vector(0,1,0)) for x in (-39.25,-32.75) for z in (10.25,14.75)]
    coupon=plate.cut(*holes)
    j['finished_hole_series'].append(dict(finished_bore_mm=diameter,undeformed_leg_overlap_mm3=vol(contacts,coupon),individual_mm3=[vol(t,coupon) for t in contacts.Solids()]))
j['stroke']=[]
# Keep metal case/upper plate fixed. The source's top includes both an embossed
# stationary plate and the central moving actuator; full physically closed stroke
# comes from the data sheet, distinct from generous empty-enclosure travel.
for i in range(15):
 m=cap.translate((0,-.05*i,0))
 j['stroke'].append(dict(cap_translation_mm=round(i*.05,2),case_mm3=vol(m,case),housing_mm3=vol(m,hs),keeper_mm3=vol(m,ret),stationary_source_plunger_contact_mm3=vol(m,top)))
(Q/'power-key.json').write_text(json.dumps(j,indent=2)+'\n');print(j['rest_cap_to_plunger_mm'],j['terminals_to_pcb_interference_mm3'],j['pins'],j['stroke'][-1])
