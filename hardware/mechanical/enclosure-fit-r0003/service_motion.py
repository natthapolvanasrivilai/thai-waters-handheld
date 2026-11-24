from pathlib import Path
import sys
import cadquery as cq
from mount import geometry,BASE,HERE,PINS
from closure import CENTRES,features
sys.path.insert(0,str(BASE))
from motion import run
if __name__=='__main__':
    cache=Path(sys.argv[1])
    _,_,shelf,posts,_=geometry()
    fast=cq.importers.importStep(str(BASE.parents[1]/'components/standard-fasteners/6mm.step')).val()
    bosses,_,pads,bores=features()
    added={'shelf':shelf,'shelf posts':cq.Compound.makeCompound(posts),'shelf screw':fast.translate((*PINS[1],12)), 'case bosses':cq.Compound.makeCompound(bosses)}
    closing={'bezel feet':cq.Compound.makeCompound(pads),'bezel screws':cq.Compound.makeCompound([fast.translate((x,y,28.30)) for x,y in CENTRES])}
    run(cache,added,closing,HERE/'service-motion.json')
