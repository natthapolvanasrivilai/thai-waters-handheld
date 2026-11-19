"""Rigid offset of the OEM connector inside the fixed, uncompressed flexible mask."""
import argparse,itertools,json
from pathlib import Path
from audit_port import read,sight,R9,QA,MOUTH
p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);a=p.parse_args()
fixed=[read(R9/'CAD'/(k+'.brep')) for k in ('housing-battery-bay','bezel','usb-c-shield-mask')]
usb=read(a.cache/'A1-usb.brep')
rows=[]
for dx,dy,dz in itertools.product((-.15,.15),repeat=3):
    planes=sight(fixed,usb.translate((dx,dy,dz)),(dy,dz),steps=(0,30),pitch=.20,mouth=MOUTH+dx,planes=(-38.,-36.))
    result={x:{k:sum(g[k] for g in r) for k in ('checked','around_shield','through_mouth')} for x,r in planes.items()}
    rows.append(dict(socket_offset_mm=[dx,dy,dz],planes=result))
    print(rows[-1],flush=True)
(QA/'offset-privacy.json').write_text(json.dumps(rows,indent=2)+'\n')
