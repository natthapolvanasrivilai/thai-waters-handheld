"""Place source CAD and form the four W1 leads relative to the controller's J8 cavities."""
from pathlib import Path
import json, math
import cadquery as cq

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'placed'
OUT.mkdir(exist_ok=True)
ORIGIN=(0,0,0)

def wire(points,radius):
    vectors=[cq.Vector(*p) for p in points]
    parts=[]
    for a,b in zip(vectors,vectors[1:]):
        span=b-a
        parts.append(cq.Solid.makeCylinder(radius,span.Length,a,span.normalized()))
    for p in vectors[1:-1]:
        parts.append(cq.Solid.makeSphere(radius,p,angleDegrees1=-90,angleDegrees2=90))
    return parts[0].fuse(*parts[1:]).clean() if len(parts)>1 else parts[0]

def bounds(shape):
    b=shape.BoundingBox()
    return [round(x,4) for x in (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)]

header=cq.importers.importStep(str(ROOT/'source-cad/C2883842.stp')).val()
header=header.rotate(ORIGIN,(1,0,0),-90).translate((11.419,12.66,10.92))
header.exportBrep(str(OUT/'W1-P.brep'))
rows={}
for i,(label,y,terminal_x) in enumerate([('VCC',-6.35,19.039),('GND',-1.27,16.499),('SDA',3.81,13.959),('SCL',1.27,11.419)]):
    z=9.1+1.06*i
    # Tee remains at x30,y17 to service the independently routed Boardoza branch.
    lane_y=12.85-i*1.08
    points=[(39.48,y,8.45),(37.6,y,8.45),(36.2,y,z),(30,y,z),(30,17,z),(28.8,17,z),(27.4,15.2,z),(26.2,lane_y,z),(terminal_x+1.2,lane_y,z),(terminal_x,lane_y+1,12.23),(terminal_x,14.61,12.23)]
    if label=='SCL':
        # Cross the bridge screw above its head. The final stripped tail descends
        # onto the solder pin beyond the head; keep insulation off the driver recess.
        points=points[:-3]+[(terminal_x+1.8,lane_y,13.65),(terminal_x,13.30,13.65),(terminal_x,14.80,13.15)]
    s=wire(points,.4)
    # Four stripped and individually insulated taps on the straight trunk.
    tee_y=(1.2,3.4,5.8,7.8)[i]
    window=cq.Solid.makeBox(1.2,2.8,1.2,cq.Vector(29.4,tee_y-1.4,z-.6))
    s=s.cut(window)
    bare=wire([(30,tee_y-1.4,z),(30,tee_y+1.4,z)],.127)
    branch=wire([(29.,tee_y,z),(30,tee_y,z)],.127)
    joint=bare.fuse(branch)
    joint.exportBrep(str(OUT/('tee-'+label+'-Cu.brep')))
    # Individually overcoat each soldered tap; mask touches both insulation ends.
    cover=wire([(30,tee_y-1.4,z),(30,tee_y+1.4,z)],.46).fuse(wire([(29.,tee_y,z),(30,tee_y,z)],.42))
    cover.cut(joint).exportBrep(str(OUT/('tee-'+label+'-seal.brep')))
    s.exportBrep(str(OUT/('w1'+label+'.brep')))
    rows[label]={'insulation_diameter_mm':.8,'pad_end_and_route_mm':points,'stripped_tinned_tip_mm':[terminal_x,15.30,12.23],'finished_path_mm':round(sum(math.dist(a,b) for a,b in zip(points,points[1:]))+.69,3)}
(OUT/'w1.json').write_text(json.dumps({'case_units':'mm','connector':'XKB X6511WR-04H-C60D30R1 / LCSC C2883842','mating_pin_insertion_mm':3.80,'header_bounds_mm':bounds(header),'wires':rows},indent=2)+'\n')

