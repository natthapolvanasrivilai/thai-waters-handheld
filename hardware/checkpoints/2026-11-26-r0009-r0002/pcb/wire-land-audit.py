from pathlib import Path
import sys,hashlib,json,re
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base/'case-board-r0001'))
from build import parse,items,one
pcb=base/'case-board-r0002/case-board.kicad_pcb'
sha='aaab9d33b5b04815a3178a40aac9649dac80e361524bcfb1b8363dae45bd1267'
assert hashlib.sha256(pcb.read_bytes()).hexdigest()==sha
out={}
for f in items(parse(pcb),'footprint'):
    props={p[1].strip('"'):p[2].strip('"') for p in items(f,'property')}
    ref=props['Reference']
    if not re.fullmatch(r'W10[1-7]|J(?:[1-9]|1[0-3])',ref):continue
    x,y=map(float,one(f,'at')[1:3])
    row={'value_mark':props['Value'],'pcb_xy_mm':[x,y],'mounted_xy_mm':[round(x-87,6),round(y-114,6)],'pads':[]}
    for p in items(f,'pad'):
        def vals(k):
            z=list(items(p,k))
            return z[0][1:] if z else None
        row['pads'].append({'pin':p[1].strip('"'),'mount':p[2],'net':vals('net')[0].strip('"') if vals('net') else None,'land_dims_mm':vals('size'),'drill_mm':vals('drill')})
    row['required_missing_evidence']=('no conductor per DNP; inspect for unintended protrusion' if ref=='W106' else 'actual joint protrusion on each populated face and installed wire or mating assembly envelope')
    out[ref]=row
assert len(out)==20 and all(len(x['pads'])>0 for x in out.values()) and out['W101']['pads'][0]['net']=='ENTRY'
print(json.dumps({'pcb_sha256':sha,'scope':'Native PCB land registration only; not solder/wire geometry','rows':out},indent=2))
