"""Check the separate clear guide cores, opaque sleeves, and LED-to-window paths."""
import argparse,itertools,json
from pathlib import Path
import numpy as np
import vtk
from audit_port import read,locator
Q=Path(__file__).resolve().parent; R=Q.parent; H=R.parents[1]
p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);a=p.parse_args()
house=read(R/'CAD/housing-battery-bay.brep'); mask=read(R/'CAD/usb-c-shield-mask.brep')
blue=read(H/'electronics/usb-status-r0003/placed/USB-D1.brep')
population=read(a.cache/'A1-population.brep')
cores={name:read(R/'CAD'/('status-'+name+'-guide.brep')) for name in ['charge','usb','power']}
front={'power':(-49.97,6.05,13.10),'charge':(-49.97,-6.05,13.10),'usb':(-49.97,0,13.10)}
target={'charge':(-38.75,-10.021,20.75),'usb':(-42.352,0,13.10),'power':(-38.75,9.979,20.75)}
tree=locator([house,mask])
t,sid,cid=vtk.reference(0.),vtk.reference(0),vtk.reference(0)
pt,pc,cell=[0.]*3,[0.]*3,vtk.vtkGenericCell()
def clear(a,b):
    return not tree.IntersectWithLine(a,b,.00001,t,pt,pc,sid,cid,cell)
def rays(start,end):
    # Sample emission face to window interior. 25 viewer/window positions × 9 emission positions.
    rays=[clear((start[0]-.015,start[1]+u,start[2]+v),(end[0]-.001,end[1]+s,end[2]+h))
          for u,v in itertools.product((-.36,-.18,0,.18,.36),repeat=2)
          for s,h in itertools.product((-.2,0,.2),repeat=2)]
    return dict(lines=len(rays),open_lines=sum(rays),center_open=clear(start,end))
results={}
for name,guide in cores.items():
    relevant=blue if name=='usb' else population.Solids()[505 if name=='charge' else 506]
    results[name]=dict(front_center_mm=front[name],source_target_mm=target[name],
        core_to_source_mm=round(guide.distance(relevant),4),
        core_to_housing_mm=round(guide.distance(house),4),
        core_housing_intersection_mm3=round(guide.intersect(house).Volume(),6),
        core_to_other_cores_mm={k:round(guide.distance(other),3) for k,other in cores.items() if k!=name},
        sight_to_emitters={key:rays(front[name],xyz) for key,xyz in target.items()})
(Q/'optical-paths.json').write_text(json.dumps(results,indent=2)+'\n')
for k,r in results.items():print(k,r)
