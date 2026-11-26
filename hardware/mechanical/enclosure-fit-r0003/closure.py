"""Serviceable four-point bezel closure and access to the obstructed controller screw."""
from pathlib import Path
import json
import cadquery as cq
V=cq.Vector
CENTRES=[(-37.,-33.65),(24.,-33.65),(-20.,33.65),(24.,33.65)]
def cyl(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,V(x,y,z))
def clip(shape,y):
    inner=30.82
    return shape.intersect(cq.Solid.makeBox(130,18,40,V(-65,inner if y>0 else -inner-18,0)))
def features():
    adds=[];cuts=[];pads=[];bores=[]
    for x,y in CENTRES:
        ramp=cq.Solid.makeCone(.60,3.55,3.8,V(x,y,17.7))
        adds.append(clip(ramp.fuse(cyl(x,y,21.5,3.55,4.95)),y))
        # A broad open notch ends at the boss face. There is no freestanding thin
        # ring around the lower bezel foot. The front circumference covers the notch.
        cuts.extend([cyl(x,y,26.45,3.39,2.0),cyl(x,y,21.55,.82,5.1)])
        lower=clip(cyl(x,y,26.55,3.08,1.30),y)
        front=clip(cyl(x,y,27.8,3.55,2.20),y)
        pads.append(lower.fuse(front))
        bores.extend([cyl(x,y,26.0,1.15,4.5),cyl(x,y,28.30,2.18,2.0)])
    # Relieve the outer edge of the receiver sole, keeping its interior dovetail.
    cuts.append(cyl(36,-24.25,-3.5,2.25,4.05))
    return adds,cuts,pads,bores
