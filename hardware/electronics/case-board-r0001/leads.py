"""Terminate the three located power leads on the new board. Keep the A1 ends fixed."""
import json
import sys
from pathlib import Path
import cadquery as cq
from build import A5
sys.path.insert(0,str(A5/"installed-leads"))
from form import COPPER, JACKET, curved, sweep

def installed():
    rows=json.loads((A5/"installed-leads/routes.json").read_bytes())
    parts={}
    specs={}
    for ref,row in rows.items():
        vertices=[cq.Vector(*p) for p in row["dressing_points_mm"]]
        top=vertices[0]
        # The board back moved up 0.70. Adjust the stripped tail and the first
        # bend, preserving all far-side branches, solder and splice geometry.
        vertices[0]=cq.Vector(top.x,top.y,19.0)
        vertices[1]=vertices[1]+cq.Vector(0,0,.35)
        if ref=="W3":vertices[3]=vertices[3]+cq.Vector(0,0,.40)
        lead,radius=curved(vertices)
        pin=cq.Vector(top.x,top.y,17.46 if ref=="W7" else 17.61)
        end=vertices[-1]
        if ref=="W3":far=end-cq.Vector(1.4,0,0)
        else:far=cq.Vector(end.x,end.y,20.751 if ref=="W2" else 17.34)
        corepath=cq.Wire.assembleEdges([cq.Edge.makeLine(pin,vertices[0]),*lead.Edges(),
                                       cq.Edge.makeLine(end,far)])
        core=sweep(corepath,COPPER)
        parts[ref+" copper"]=core
        parts[ref+" jacket"]=sweep(lead,JACKET).cut(core)
        solder=cq.Solid.makeCone(.52,.16,.25,cq.Vector(top.x,top.y,18.54))
        parts[ref+" board fillet"]=solder.cut(core)
        specs[ref]=dict(length_mm=round(corepath.Length(),3),min_bend_radius_mm=round(radius,3),
                        board_end=vertices[0].toTuple(),far_end=far.toTuple())
    return parts,specs
