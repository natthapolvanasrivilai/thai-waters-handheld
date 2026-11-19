"""Independent check of the off-tool diaphragm and modeled elastic positions against native OEM CAD."""
import argparse,itertools,json,math,sys
from pathlib import Path
from audit_port import read,sight,R9,QA,MOUTH,CZ,capsule
sys.path.insert(0,str(R9));import build
p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);a=p.parse_args()
house=read(R9/'CAD/housing-battery-bay.brep');bezel=read(R9/'CAD/bezel.brep');usb=read(a.cache/'A1-usb.brep')
free=build.shield_mask(free=True)
rows=[]
for dx,dy,dz in itertools.product((-.15,.15),repeat=3):
    moving=usb.translate((dx,dy,dz))
    mounted=build.shield_mask(offset=(dx,dy,dz))
    planes=sight([house,bezel,mounted],moving,(dy,dz),steps=(0,15,30),pitch=.20,mouth=MOUTH+dx,planes=(-38.,-36.))
    r={x:{k:sum(g[k] for g in rr) for k in ('checked','around_shield','through_mouth')} for x,rr in planes.items()}
    plugs={}
    for k,end,w,h in [('cable shoulder',MOUTH+dx-.15,12.35,6.50),('plug shell',MOUTH+dx+6.4,8.28,2.43)]:
        shape=capsule(-68,end,w+.2,h+.2,1.1,dy,dz)
        plugs[k]=dict(mask_gap_mm=round(shape.distance(mounted),5),housing_gap_mm=round(shape.distance(house),5))
    row=dict(offset_mm=[dx,dy,dz],planes=r,plugs=plugs,
             free_lip_interference_with_metal_mm3=round(free.intersect(moving).Volume(),6),
             mounted_lip_interference_with_metal_mm3=round(mounted.intersect(moving).Volume(),6),
             mounted_lip_housing_overlap_mm3=round(mounted.intersect(house).Volume(),6))
    rows.append(row);print(row,flush=True)
results=dict(assumption='Elastic inner lip follows the installed socket; fixed retaining bead. Verify strain return, opaque contact and insertion physically.',neutral_radial_interference_mm=.38,
             nominal_factory_positive_mold_tolerance_mm=.10,
             corner_normal_min_geometric_preload_mm=round(.38-math.sqrt(2)*.15-.10,5),poses=rows)
(QA/'tracking-diaphragm.json').write_text(json.dumps(results,indent=2)+'\n')
