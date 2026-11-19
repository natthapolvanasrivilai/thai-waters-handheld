"""Model two recovered 6 mm cuts of TE Raychem RNF-100-1/16-0-SP on the W2 loom."""
from pathlib import Path
import cadquery as cq
from math import sqrt
HERE=Path(__file__).resolve().parent
# Conserve polymer cross-section against 0.90 mm measured/proposed insulation.
# TE nominal fully recovered ID 0.8 mm, wall 0.43 mm; applied ID 0.90.
r=sqrt((.40+.43)**2-.40**2+.45**2)
for index,(x,y,z) in enumerate([(4.,-14.80,14.35),(-4.,-16.25,14.53)]):
    axis=cq.Vector(1,0,0);p=cq.Vector(x,y,z)
    form=cq.Solid.makeCylinder(r,6,p,axis).cut(cq.Solid.makeCylinder(.45,6.2,p-axis*.1,axis))
    form.exportBrep(str(HERE/("shrink"+str(index)+".brep")))
print("Installed OD",round(2*r,4))
