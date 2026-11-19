"""Place official component CAD and the two controlled carriers in handheld coordinates."""
from pathlib import Path
import json, math
import cadquery as cq

HERE=Path(__file__).resolve().parent
OUT=HERE/'placed'
OUT.mkdir(exist_ok=True)
AIM=HERE.parents[1]/'mechanical'/'TW-A-0001-R0009'/'CAD'
R_BOARD=(-21,18.0,17.6)
W_DIAM=.52
def step(file):
    return cq.importers.importStep(str(file)).val()
def pipe(points,radius):
    vs=[cq.Vector(*p) for p in points]
    route=cq.Edge.makeSpline(vs)
    ring=cq.Wire.makeCircle(radius,vs[0],route.tangentAt(0))
    return cq.Solid.sweep(ring,[],cq.Wire.assembleEdges([route]),isFrenet=True)
def bounds(s):
    b=s.BoundingBox()
    return [round(x,4) for x in (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)]
led=step(HERE/'source-cad/APG1608.STEP').rotate((0,0,0),(0,0,1),90).translate((-42.152,0,13.1))
res=step(HERE/'source-cad/LCSC-C114612.stp').rotate((0,0,0),(0,0,1),-90).translate((R_BOARD[0],R_BOARD[1],R_BOARD[2]+.61))
led_board=step(HERE/'USB-blue-substrate.step').rotate((0,0,0),(0,1,0),-90).rotate((0,0,0),(1,0,0),-90).translate((-41.5,0,13.1))
r_board=step(HERE/'USB-limit-substrate.step').translate(R_BOARD)
PS={'USB-D1':led,'USB-R1':res,'USB-PCB1':led_board,'USB-PCB2':r_board}
control={
 'USB-W4A': [(-19.06,19.82,20.50),(-19.06,19.60,20.05),(-19.13,19.05,19.04),(-19.57,18.62,18.77),(-19.98,18.47,18.50)],
 'USB-W4B': [(-22.02,18.47,17.38),(-22.10,18.45,16.84),(-23.0,18.40,16.05),(-27,17.65,15.7),(-32,14,15.0),(-35.6,9.4,14.35),(-37.6,4.3,13.8),(-39.5,1.7,13.1),(-41.00,1.7,13.1),(-41.28,1.7,13.1)],
 'USB-W4C': [(-16.52,19.82,20.50),(-16.52,19.60,20.05),(-16.7,18.8,17.5),(-19.3,16.45,15.65),(-24.5,16.0,15.15),(-29,14,14.6),(-33.8,9.8,15.25),(-36.1,4.5,13.55),(-37.8,0,13.2),(-39.4,-1.7,13.1),(-40.9,-1.7,13.1),(-41.28,-1.7,13.1)]}
for k,p in control.items():PS[k]=pipe(p,W_DIAM/2)
# The uninsulated wire tail projects from the insulated end to the plated hole
# or solder fillet. Keep copper separately for accurate optical and pin checks.
tails={'USB-W4A-Cu':[((-19.06,19.82,20.50),(-19.06,19.82,20.75)),((-19.98,18.47,18.50),(-19.98,18.47,17.58))],
 'USB-W4B-Cu':[((-22.02,18.47,17.38),(-22.02,18.47,18.23)),((-41.28,1.7,13.1),(-42.14,1.7,13.1))],
 'USB-W4C-Cu':[((-16.52,19.82,20.50),(-16.52,19.82,20.75)),((-41.28,-1.7,13.1),(-42.14,-1.7,13.1))]}
for k,ends in tails.items():
    seg=[]
    for a,b in ends:
        d=cq.Vector(*b)-cq.Vector(*a)
        seg.append(cq.Solid.makeCylinder(.127,d.Length,cq.Vector(*a),d.normalized()))
    PS[k]=cq.Compound.makeCompound(seg)
def overlap(a,b):
    ba=a.BoundingBox()
    bb=b.BoundingBox()
    if ba.xmax<=bb.xmin or ba.xmin>=bb.xmax or ba.ymax<=bb.ymin or ba.ymin>=bb.ymax or ba.zmax<=bb.zmin or ba.zmin>=bb.zmax:
        return 0.
    v=a.intersect(b).Volume()
    return round(max(0,v),6)
checks={}
references={n:cq.Shape.importBrep(str(AIM/(n+'.brep'))) for n in ['housing-battery-bay','usb-c-shield-mask','status-usb-guide','status-power-guide','status-charge-guide','battery-wire-bridge','Adafruit-258-CAD-with-PCM-and-stubs','key-board-retainer-west']}
controller=step(AIM.parents[1]/'rev-E/scripts/inputs/Waveshare.stp').rotate((0,0,0),(0,0,1),-90).translate((0,0,27.4))
for i,body in enumerate(controller.Solids()):
    bb=body.BoundingBox()
    if bb.xmin < -14 and bb.xmax>-43 and bb.ymin<21 and bb.ymax>-3 and bb.zmin<21 and bb.zmax>11:
        references['A1.'+str(i)]=body
# DOWSIL 3145 process envelopes. The lower flange wets the FR4 and a side rib
# meets the measured moulded wall of A1.525 at Y20.39. Never enter the contacts.
def rounded_block(x,y,z,dx,dy,dz,r):
    return cq.Workplane('XY').box(dx,dy,dz,centered=False).edges().fillet(r).val().translate((x,y,z))
bead=rounded_block(-21.9,17.25,17.15,2.30,1.88,.58,.14).fuse(
     rounded_block(-20.47,18.72,17.15,1.22,1.69,1.16,.10)).fuse(
     rounded_block(-20.46,19.94,16.99,1.99,.60,1.59,.17))
j8=references['A1.525']
# Exact finished body is trimmed against the two interfaces and conductors.
for solid in [r_board,j8,*PS.values()]:
    bead=bead.cut(solid)
bead=bead.clean()
assert len(bead.Solids())==1 and bead.distance(r_board)<1e-5 and bead.distance(j8)<1e-5
bond_contacts={'adhesive':'DOWSIL 3145 RTV gray','housing_face_y_mm':20.39,
               'cured_volume_mm3':round(bead.Volume(),3),'clearance_to_pcb2_mm':round(bead.distance(r_board),6),
               'clearance_to_header_wall_mm':round(bead.distance(j8),6)}
PS['USB-BOND']=bead
for k,s in PS.items():
    s.exportBrep(str(OUT/(k+'.brep')))
    checks[k]={n:v for n,ref in references.items() if (v:=overlap(s,ref))>.00001}
pair={}
for i,(k,s) in enumerate(PS.items()):
    for n,t in list(PS.items())[i+1:]:
        v=overlap(s,t)
        if v>.00001:pair[k+' / '+n]=v
result={'units':'mm, mm3','retention':bond_contacts,'wire_nominal_outer_diameter_mm':W_DIAM,'wire_control_points':control,'bounds':{k:bounds(s) for k,s in PS.items()},'intersections_by_reference_mm3':checks,'pair_intersections_mm3':pair}
(OUT/'placement.json').write_text(json.dumps(result,indent=2)+'\n')
print(checks,pair,flush=True)
