from pathlib import Path
import cadquery as cq
import numpy as np, math
from functools import lru_cache
ROOT=Path(__file__).resolve().parent
# Reproduction bundle has all three supplied inputs in inputs/.
INPUT=ROOT/'inputs'
case=(INPUT/'Pocket.step') if INPUT.exists() else ROOT.parent/'right-reel/Pocket.step'
board=(INPUT/'Waveshare.stp') if INPUT.exists() else next((ROOT.parent/'boardvendor').glob('*.stp'))
encoder=(INPUT/'AS5600.step') if INPUT.exists() else ROOT/'AS5600.step'
def load(f):return cq.importers.importStep(str(f)).val()
def compound(seq):return cq.Compound.makeCompound(list(seq))
def box(x,y,z,w,d,h):return cq.Solid.makeBox(w,d,h,cq.Vector(x,y,z))
def cx(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(1,0,0))
def bb(s):
 b=s.BoundingBox();return (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)
def boundgap(a,b):
 return math.sqrt(sum(max(a[i]-b[i+1],b[i]-a[i+1],0)**2 for i in [0,2,4]))
def possible(a,b):
 return all(a[i]<b[i+1]-.00001 and b[i]<a[i+1]-.00001 for i in (0,2,4))
def rot(s,ang):return s.rotate((58.5,0,14.8),(59.5,0,14.8),ang) if ang else s
def fold(s,ang):return s.rotate((53.6,7.8,14.8),(53.6,7.8,15.8),ang) if ang else s
D=load(case).Solids()
labels=['Housing','Bezel','Rotor','Folding stem','Grip','Collar','Hinge screw','Grip retainer','Magnet','Cell envelope','Speaker envelope']
E=load(encoder).rotate((0,0,0),(1,1,1),120).translate((39.48,-12.7,5.91)).Solids()
A=load(board).rotate((0,0,0),(0,0,1),-90).translate((0,0,27.4)).Solids()
def revised():
 h=D[0]
 # Remove only two old projections up to the inboard annular well wall, X=47.
 for s in [-1,1]:
  h=h.cut(box(42.59,s*9-1.56,10.29,4.41,3.12,9.02))
 # Four corner adhesive lands, two short registration pins. 0.25 mm adhesive seat.
 for y in [-10.16,10.16]:
  for dz in [-6.35,6.35]:
   h=h.fuse(cx(41.30,y,14.8+dz,1.85,6.6))
   if (y>0)==(dz>0): h=h.fuse(cx(39.68,y,14.8+dz,0.93,1.75))
 return h.clean()
if (ROOT/'candidate.brep').exists():
 H=cq.Shape.importBrep(str(ROOT/'candidate.brep'))
else:
 H=revised()
 H.exportBrep(str(ROOT/'candidate.brep'))

