"""Rev F rigid slide-lock rod handle. CadQuery 2.8, millimetres, +Z toward LCD.

Slide +Y to seat the male dovetail; the M3 lock screw advances along +Z.
The female shoe, upper travel stop and nut boss are part of the housing.
"""
from pathlib import Path
import base64
import json
import math
import zlib
import cadquery as cq
import numpy as np

ROOT=Path(__file__).resolve().parent
X,Y=17.,-24.5
STOP=5.
SEAT=-3.2
HEAD_SEAT=-5.10
RETRACT=5.30

def rounded(w,d,y,z,h,r):
    return (cq.Workplane("XY").workplane(offset=z).center(X,y).rect(w,d)
            .extrude(h).edges("|Z").fillet(r).val())

def cyl(r,z,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(X,Y,z))

def hex_prism(af,z,h):
    return (cq.Workplane("XY").workplane(offset=z).center(X,Y)
            .polygon(6,af/math.cos(math.pi/6)).extrude(h).val())

def prism(profile,y_start,y_end):
    # The XZ plane has its positive normal toward -Y.
    return (cq.Workplane("XZ",origin=(X,y_end,0)).polyline(profile).close()
            .extrude(y_end-y_start).val())

def receiver_channel():
    # The parallel flanks undercut by 3.2 mm each across their 4 mm height.
    return prism([(-9.9,-5.),(9.9,-5.),(9.9,SEAT),(13.1,.80),
                  (-13.1,.80),(-9.9,SEAT)],-38,STOP)

def add_mount(housing):
    # Rounded shoe blends into stock rear shell; no through slot into electronics.
    shoe=rounded(35.8,45.5,-11.8,SEAT,3.7,5.2)
    shoe=cq.Workplane(obj=shoe).edges("<Z").fillet(.6).val()
    nut_boss=cyl(4.9,1.6,4.4)
    case=housing.fuse(shoe,nut_boss).cut(receiver_channel())
    # Hex nut drops in from the inside. Keeper closes the nut pocket under the PCB.
    return (case.cut(cyl(1.80,-.1,7),hex_prism(5.88,2.15,4.3),
                     cyl(3.99,5.09,1.2)).clean())

def palm_grip():
    stations=[(3,-6.1,7.,2.6),(-7,-7.3,9.2,3.7),(-21,-9.8,11.3,5.6),
              (-32,-11.2,12.2,6.2),(-45,-12.8,13.0,7.4),(-56,-14.2,14.0,9.0),
              (-69,-16.2,13.3,10.9),(-85,-18.5,14.6,12.3),
              (-102,-20.7,14.2,12.3),(-115,-22.2,13.6,11.6),
              (-121,-22.9,10.8,8.9),(-124.5,-23.3,5.7,4.6),(-125.4,-23.4,2.0,1.6)]
    wires=[cq.Workplane("XZ",origin=(X,y,z)).ellipse(rx,rz).val()
           for y,z,rx,rz in stations]
    return cq.Solid.makeLoft(wires)

def saddle():
    # Broad external shoulder faces bear against the shoe as the screw clamps.
    shoulder=rounded(31.,38.,-14.,-7.1,3.9,2.6)
    tongue=prism([(-9.52,-4.),(9.52,-4.),(9.52,SEAT),(12.49,.51),
                  (-12.49,.51),(-9.52,SEAT)],-30,STOP)
    # Remove the sharp leading corners on the male key, leaving a flat end stop.
    for side in (-1,1):
        wedge=(cq.Workplane("XY").workplane(offset=-4.1)
               .polyline([(X+side*11.0,STOP),(X+side*13.,STOP-2.0),
                          (X+side*15.,STOP-2.0),(X+side*15.,STOP+.2),
                          (X+side*11.,STOP+.2)]).close().extrude(5.).val())
        tongue=tongue.cut(wedge)
    cup=cyl(6.85,-15.2,10.4)
    body=shoulder.fuse(tongue,palm_grip(),cup)
    # 8.35 mm head chamber allows the screw to withdraw below the channel roof.
    return body.cut(cyl(1.78,-16,18),cyl(3.12,-19,19+HEAD_SEAT),
                    cyl(4.63,-19,5.53)).clean()

def mount_parts():
    # Conservative unthreaded hardware envelopes with real tool access geometry.
    head=cyl(2.75,HEAD_SEAT-3.,3.)
    screw=head.fuse(cyl(1.5,HEAD_SEAT,10.)).cut(hex_prism(2.5,HEAD_SEAT-3.1,1.9)).clean()
    nut=hex_prism(5.50,2.15,2.40).cut(cyl(1.50,2.1,3))
    grip_keeper=cyl(4.51,-15.06,1.59).cut(cyl(1.85,-15.2,2.))
    # A blind ceiling above the tip keeps the nut captive, with a central relief.
    nut_keeper=cyl(3.85,5.12,.83).cut(cyl(1.80,5.0,.55))
    return {"Grip lock screw":screw,"Grip screw keeper":grip_keeper,
            "Receiver nut":nut,"Receiver nut keeper":nut_keeper}

def export_mesh(part,path,name="Rod grip"):
    vs,fs=part.tessellate(.065,.16)
    def pack(a):return base64.b64encode(zlib.compress(a.tobytes(),9)).decode()
    data=dict(n=name,k=1,p=pack(np.rint(np.array([v.toTuple() for v in vs])*100).astype("<i2")),
              t=pack(np.asarray(fs,dtype="<u4")))
    path.write_text(json.dumps(data,separators=(",",":")),encoding="utf8")

def stl(part,path):
    b=part.BoundingBox();part=part.translate((-b.xmin,-b.ymin,-b.zmin))
    cq.exporters.export(part,str(path),tolerance=.04,angularTolerance=.12)

if __name__=="__main__":
    dst=ROOT/"Print";dst.mkdir(parents=True,exist_ok=True)
    cad=ROOT/"CAD";cad.mkdir(parents=True,exist_ok=True)
    part=saddle();parts=mount_parts()
    assert part.isValid() and len(part.Solids())==1
    # Broad side of the slide shoulder is the print datum; main tongue laminations
    # run along the handle. Apply support to the recessed leading/palm overhang.
    stl(part.rotate((0,0,0),(0,1,0),-90),dst/"rod-grip.stl")
    stl(parts["Grip screw keeper"],dst/"grip-screw-keeper.stl")
    stl(parts["Receiver nut keeper"],dst/"receiver-nut-keeper.stl")
    cq.exporters.export(part,str(cad/"rod-grip.step"))
    print("Rod handle volume",round(part.Volume(),1),"mm3")
