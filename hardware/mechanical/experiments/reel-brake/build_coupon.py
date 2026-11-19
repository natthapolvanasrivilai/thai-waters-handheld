"""Standalone B0 brake coupon, mm. CAD is arranged for a horizontal tabletop."""
from pathlib import Path
import json
import cadquery as cq
from cadquery import exporters
import trimesh

OUT=Path(__file__).resolve().parent; PRINT=OUT/'Print'
def box(x1,x2,y1,y2,z1,z2):
    return cq.Workplane('XY').box(x2-x1,y2-y1,z2-z1,centered=False).translate((x1,y1,z1))
def zcyl(x,y,z,r,h):
    return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z))
def ycyl(x,y,z,r,h):
    return cq.Workplane('XY').newObject([cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(0,1,0))])
def chain(*shapes):
    result=shapes[0]
    for p in shapes[1:]:result=result.union(p)
    return result

# Print the plate flat. Slotted side windows remain open for the slip measurement.
base=box(-18,74,-18,24,0,3).edges('|Z').fillet(3)
seat=zcyl(0,0,2.8,4.6,3.2)
base=base.union(seat).cut(zcyl(0,0,-1,1.65,10))
for y in [6.2,15.6]:
    ear=box(20,28,y,y+3,2.8,17.3).cut(ycyl(24,y-1,13.4,1.65,5))
    base=base.union(ear)
# At rest the arm underside touches the lower stop. The fixed upper stop limits
# lift to 2.10 at x58.5, before any removable adjustment shims.
base=chain(base,box(57,60,11,15,2.8,12.0),box(56,61,6.8,9.7,2.8,19.95),
           box(56,61,16.3,19.2,2.8,19.95),box(56,61,9.65,16.35,16.90,19.95))
anchor=box(65,71,3,7,2.8,8).cut(ycyl(68,2,5.7,1,6))
base=base.union(anchor)
for x,y in [(-13,-13),(-13,19),(69,-12),(69,19)]:
    base=base.cut(zcyl(x,y,-1,2.1,6))

# Two-piece rotor so all overhanging parts have a flat print orientation.
# D-flat keyed section transmits the finger crank load at the hub.
rotor=chain(zcyl(0,0,6,12.75,4),zcyl(0,0,9.8,4.45,12.2))
key=zcyl(0,0,21.9,4.45,3.1).cut(box(3,5,-5,5,21.8,25.2))
rotor=rotor.union(key).cut(zcyl(0,0,5,1.72,22))
crank=chain(zcyl(0,0,22,6,3),box(0,7.8,-3.25,3.25,22,25),
            zcyl(7.8,0,22,3.25,3),zcyl(7.8,0,24.8,2.5,8.2))
keyhole=zcyl(0,0,21,4.65,5).cut(box(3.2,6,-6,6,20,28))
crank=crank.cut(keyhole)
# The tip spring's free span runs tangentially to the disc, independent of the lever pivot.
arm=box(8.5,69,10.9,15.1,12,14.8)
arm=chain(arm,ycyl(24,10.9,13.4,3.5,4.2),box(8.5,13.5,12,15.1,11,12.2),
          box(8.5,13.5,-1.6,12.1,11,12.2)).cut(ycyl(24,10,13.4,1.72,6))
arm=arm.cut(zcyl(63,13,10,1.15,7)).cut(zcyl(67,13,10,1.05,7))
# Pad is stock material, shown only in assembly. Height set AFTER bonding.
pad=box(9.75,12.25,-1.5,1.5,10.25,11)
parts={'base':base,'rotor':rotor,'crank':crank,'rocker':arm}
colors={'base':(.48,.55,.53),'rotor':(.3,.53,.47),'crank':(.83,.53,.22),'rocker':(.35,.47,.67)}
asm=cq.Assembly(name='BrakeCoupon')
for name,shape in parts.items():
    asm.add(shape,name=name,color=cq.Color(*colors[name]))
    # The leaf lies along the print layers. Support the higher rocker overhangs.
    printable=shape
    bb=printable.val().BoundingBox()
    printable=printable.translate((-bb.xmin,-bb.ymin,-bb.zmin))
    exporters.export(printable,str(PRINT/(name+'.stl')),tolerance=.05,angularTolerance=.12)
    mesh=trimesh.load_mesh(PRINT/(name+'.stl'))
    assert mesh.is_watertight and len(mesh.split())==1,name
asm.add(pad,name='Replaceable_friction_pad',color=cq.Color(.63,.47,.30))
asm.save(str(OUT/'brake-coupon.step'))
# Dimension and seated-static checks. Purposeful touching faces have zero volume.
for key,a in parts.items():
    for name,b in parts.items():
        if key < name:
            vol=a.val().intersect(b.val()).Volume()
            assert vol<1e-5,(key,name,vol)
dimensions={'rotor_radius_mm':12.75,'crank_throw_mm':7.8,'pad_center_radius_mm':11,
 'free_pad_gap_mm':.25,'hard_stop_rise_mm':2.1,'pad_lever_arm_mm':13,'stop_arm_mm':34.5,'cable_arm_mm':39,
 'max_pad_travel_mm_at_stop_center':2.1*13/34.5,'max_nominal_pad_compression_mm_at_stop_center':2.1*13/34.5-.25,
 'nominal_motion_reduction':3,'valid_solid_meshes':len(parts),'static_overlap_mm3':0}
(OUT/'geometry.json').write_text(json.dumps(dimensions,indent=2)+'\n')
print(dimensions)
