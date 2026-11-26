"""Check the mounted PCB, dressed leads and service motions against installed hardware."""
import argparse
import json
import sys
from pathlib import Path

from mount import HERE, ROOT, SCREWS, BACK, FLOOR, mounted, floor, stock
from fit import check, bounds, nearby, BASE, OLD
from leads import installed
import motion
import insertion
import cadquery as cq

def harness():
    # Keep both W2 terminations fixed and lift its centerline over the rectangular edge.
    return installed({"W2": (3,(5.5,14.85,19.02))})

def static(cache):
    parts=mounted()
    wires,specs=harness()
    reference=json.loads((BASE/'installed-step.json').read_bytes())['components']
    parts.update(wires)
    ext=[bounds(s) for s in parts.values()]
    fixed={}
    for name,row in reference.items():
        if name in OLD or name=='Housing' or not any(nearby(b,row['bounds_mm'],.05) for b in ext):
            continue
        sh=cq.Shape.importBrep(str(cache/(name+'.brep')))
        solids=sh.Solids()
        if name.startswith(('A5-W2','A5-W3','A5-W7')) and not name.endswith('cover'):
            solids=[s for s in solids if name.endswith('solder') and bounds(s)[1]<0]
        fixed[name]=[(s,bounds(s)) for s in solids]
    def group(shape):
        return [(s,bounds(s)) for s in shape.Solids()]
    fixed['maximum pack']=group(motion.maximum_drawing_pack())
    base=floor()
    # The inset roots intentionally extend 0.4 mm into the floor.
    fixed['housing without posts']=group(base)
    out=check({k:v for k,v in parts.items() if not (k.startswith('boss') or k=='rest')},fixed)
    above=cq.Solid.makeBox(100,100,30,cq.Vector(-50,-50,FLOOR+.001))
    out.update(check({k:v.intersect(above) for k,v in parts.items() if k.startswith('boss') or k=='rest'},fixed))
    # Screws intentionally engage pilot walls and leads intentionally share their own terminals.
    for k,v in parts.items():
        if k.startswith('screw'): continue
        peers={n:group(s) for n,s in parts.items() if n!=k and
               not (n.startswith(k.split()[0]) and k in wires) and
               not ((k.startswith('boss') or k=='rest') and n.startswith('screw'))}
        out[k+' vs assembly']=check({k:v},peers)[k]
    report={'overlap_mm3':out,'lead_routes':specs}
    (HERE/'fit.json').write_text(json.dumps(report,indent=2)+'\n')
    problem={k:dict(v) for k,v in out.items() if v}
    if 0<problem.get('W2 copper',{}).get('A1-J8',0)<.001:
        del problem['W2 copper']['A1-J8']
    assert not any(problem.values()),problem

def run(mode,cache):
    if mode=='static':return static(cache)
    if mode=='service':
        return motion.run(cache,mounted=mounted(),leads=harness()[0],output=HERE/'motion.json')
    kicad_holes=[(x+87,y+114) for x,y in SCREWS]
    insertion.run(cache,pcb=mounted()['PCB'],mounts=kicad_holes,output=HERE/'insertion.json',housing=floor())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('static','service','insertion'))
    p.add_argument('registered_brep_cache',type=Path)
    a=p.parse_args()
    run(a.mode,a.registered_brep_cache)
