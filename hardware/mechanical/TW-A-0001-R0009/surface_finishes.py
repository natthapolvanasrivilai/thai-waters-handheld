"""Restore OEM face colours on placed electrical component shapes in the offline viewer."""
from pathlib import Path
import sys
import json
import cadquery as cq
from build import HERE
HARD=HERE.parents[1]
sys.path.insert(0,str(HARD/"visualization"))
from vendor_colours import colors,signature,compressed

def transfer(shape,colours):
    vertices=[];triangles=[];tints=[];matched=0
    for face in shape.Faces():
        tint=colours.get(signature(face,lambda x,y,z:(x,y,z)))
        matched+=bool(tint)
        pts,indices=face.tessellate(.035,.10)
        start=len(vertices)
        vertices.extend(tuple(round(v*100) for v in point.toTuple()) for point in pts)
        triangles.extend(tuple(start+i for i in tri) for tri in indices)
        tints.extend([tint or (135,137,131)]*len(pts))
    return dict(v=compressed(vertices,"<i2"),t=compressed(triangles,"<u4"),c=compressed(tints,"u1"),styledFaces=matched,faceCount=len(shape.Faces()))

def main():
    comps=HARD/"components";elec=HARD/"electronics"
    cases=[
        (comps/"boardoza-drv2605l/DRV2605L.step",elec/"haptic-r0009/placed",{"drvParts":"drvParts","drvBoard":"drvBoard"},lambda x,y,z:(x-107.35,y+52.75,z+4.6)),
        (comps/"sparkfun-rob-08449/8449.STEP",elec/"haptic-r0009/placed",{"motor":"motor"},lambda x,y,z:(-y+19,x+19,z+3)),
        (elec/"usb-status-r0003/source-cad/APG1608.STEP",elec/"usb-status-r0003/placed",{"USB-D1":"USB-D1"},lambda x,y,z:(-y-42.152,x,z+13.1)),
        (elec/"usb-status-r0003/source-cad/LCSC-C114612.stp",elec/"usb-status-r0003/placed",{"USB-R1":"USB-R1"},lambda x,y,z:(y-21,-x+18,z+18.21)),
        (elec/"harness-r0003/source-cad/C2883842.stp",elec/"harness-r0003/placed",{"W1-P":"J8plug"},lambda x,y,z:(x+11.419,z+12.66,-y+10.92)),
    ]
    result={}
    for source,placed,keys,transform in cases:
        shades=colors(source,transform)
        for file,key in keys.items():
            shape=cq.Shape.importBrep(str(placed/(file+".brep")))
            row=transfer(shape,shades)
            print(key,row["styledFaces"],row["faceCount"],flush=True)
            if row["styledFaces"]:result[key]=row
    (HERE/"Installed/source-surfaces.json").write_text(json.dumps(result,separators=(",",":")),encoding="utf8")

if __name__=="__main__":main()
