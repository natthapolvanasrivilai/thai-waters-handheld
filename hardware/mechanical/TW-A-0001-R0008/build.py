"""R0008 print solids. Millimetres. Source coordinates are the installed Rev G datums.
Run with CadQuery 2.8, numpy and trimesh. Each BREP is in assembly (or gauge) coordinates.
"""
import hashlib
import json
import math
from pathlib import Path
import tempfile
from zipfile import ZipFile

import cadquery as cq
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
V = cq.Vector
ORIGIN = (0, 0, 0)


def box(x,y,z,w,d,h):
    return cq.Solid.makeBox(w,d,h,V(x,y,z))


def rounded(x,y,z,w,d,h,r):
    return cq.Workplane("XY").box(w,d,h).edges("|Z").fillet(r).val().translate((x,y,z+h/2))


def cyl(radius, length, start, axis):
    return cq.Solid.makeCylinder(radius,length,V(*start),V(*axis))


def roof(center, axis, up, radius, length):
    """Triangular cap tangent to the parent circle at +/-45 degrees. Extrude on bore axis."""
    c, a, u = V(*center), V(*axis).normalized(), V(*up).normalized()
    side = a.cross(u).normalized()
    tangent = radius/math.sqrt(2)
    vertices = [c+u*tangent-side*tangent,c+u*(2*tangent),c+u*tangent+side*tangent]
    wire = cq.Wire.makePolygon(vertices+[vertices[0]])
    return cq.Solid.extrudeLinear(wire,[],a*length)


def prism_xy(points, z, height):
    return cq.Workplane("XY",origin=(0,0,z)).polyline(points).close().extrude(height).val()


def case(s):
    # Reinstate the sharp stock just around the west heel, then cut a stable 45-degree
    # print land. The original east-side reel well and the rear shoe run are untouched.
    shell_blank=rounded(4.25,0,0,108.5,69,30,10)
    round_blank=cq.Workplane(obj=shell_blank).edges(">Z or <Z").fillet(4.5).val()
    heel=shell_blank.cut(round_blank).intersect(box(-55,-37,-.1,15,74,4.7))
    shoe=rounded(17,-11.8,-3.2,35.8,45.5,3.7,5.2)
    rounded_shoe=cq.Workplane(obj=shoe).edges("<Z").fillet(.6).val()
    # Leave the dovetail untouched at both open ends.
    shoe_delta=shoe.cut(rounded_shoe).cut(box(3.8,-40,-4,26.4,45.01,5))
    # Restore a sharp outside base and a sharp inside roof at the harness pod.
    pod=rounded(-10.4,33.25,3.2,32,12.9,13.8,5)
    round_pod=cq.Workplane(obj=pod).edges(">Z or <Z").fillet(1.65).val()
    delta=pod.cut(round_pod).intersect(box(-28,25,3.19,36,16,1.67))
    delta=delta.cut(box(-29.55,-32.4,2.45,38.3,63.6,25),box(-22.7,26.6,2.5,24.6,6.05,19))
    ceiling=rounded(-10.4,32.75,14.25,28,10,.75,3.1)
    # Restrict to the pod. The front part was already open for vertical battery insertion.
    ceiling=ceiling.intersect(box(-26,31.2,14.24,32,10,1))
    # x+z >= -48. The resulting diagonal bed land is 2.83 mm wide on the straight edge.
    clip=(cq.Workplane("XZ",origin=(0,60,0))
          .polyline([(-100,-50),(2,-50),(-78,30),(-100,30)]).close().extrude(120).val())
    s=s.fuse(heel,shoe_delta,delta).cut(clip,ceiling)
    # Eliminate the shallow round corner of the rectangular service access.
    s=s.cut(box(-30,-35.5,17.5,26,10,6))
    # Both steps retain their round lower and side bearing arc.
    for y0,y1,r in [(25,33.55,4.15),(33.55,35.,3.)]:
        s=s.cut(roof((-36,y0,12.5),(0,1,0),(1,0,1),r,y1-y0))
    return s.clean()


def bezel(s):
    # Match the original housing seam at Z27.8 and replace the cosmetic upper
    # rollover with a single 45-degree outer bevel all around the touchscreen.
    blank=rounded(4.25,0,0,108.5,69,30,10)
    bevel=cq.Workplane(obj=blank).edges(">Z").chamfer(2.84).val()
    stock=cq.Workplane(obj=blank).edges(">Z or <Z").fillet(4.5).val()
    extra=bevel.cut(stock).intersect(box(-52,-36,27.8,112,72,2.2))
    # The extra rim is purely exterior. Trim the same circular rotor mouth through it.
    mouth=cyl(13.35,11.85,(60.5,0,14.8),(-1,0,0))
    lead=cq.Solid.makeCone(14.2,13.35,1.1,V(58.5,0,14.8),V(-1,0,0))
    return s.fuse(extra.cut(mouth,lead)).intersect(bevel).clean()


def rotor(s):
    # Axial and hinge bores both incline 45 degrees to the plate. Restore the
    # small cosmetic roll at the bed corner to a sharp cylinder before adding
    # the sole. The original finger scoop continues through the new material.
    disk=cyl(12.75,8.5,(57.5,0,14.8),(-1,0,0))
    roll=cq.Workplane(obj=disk).edges(">X").fillet(.9).val()
    delta=disk.cut(roll).intersect(box(48,-14,1.,11,28,6.))
    scoop=cyl(4.9,7.3,(59.5,-6.2,11.3),(-1,0,0))
    s=s.fuse(delta.cut(scoop))
    # Keep z-x >= -53.2. The magnet journal and full hinge cheeks are untouched.
    clip=(cq.Workplane("XZ",origin=(0,20,0))
          .polyline([(40,-20),(65,-20),(65,11.8),(40,-13.2)]).close().extrude(40).val())
    return s.cut(clip).clean()


def stem(s):
    # The eye and axle are each 45 degrees to the plate. The sole touches only
    # the leading outside corner of the eye, clear of the pin and the journal.
    clip=(cq.Workplane("YZ",origin=(49,0,0))
          .polyline([(-15,-5),(15,-5),(15,18.2),(-15,-11.8)]).close().extrude(10).val())
    return s.cut(clip).clean()


def retainer(s):
    # Trim the upper outside corner of the two tiny stops at 45 degrees. The
    # working lower contact and both vertical guides retain the original span.
    trim=(cq.Workplane("YZ",origin=(-47,0,0))
          .polyline([(31.8,13.32),(32.4,12.72),(32.4,13.33),(31.8,13.33)])
          .close().extrude(18).val())
    return s.cut(trim).clean()


def knob(s):
    # Keep the twelve scallops and the sleeve's running bore. A 45-degree lower
    # bevel removes the shallow part of the legacy 1.15 mm cosmetic rollover.
    tool=cyl(3.75,9.30,(53.6,-7.95,14.8),(0,1,0))
    tool=cq.Workplane(obj=tool).edges("<Y").chamfer(1.15).val()
    return s.intersect(tool).clean()


def handle(s):
    # A flat nose and short 45-degree corners seat directly on the bed at Y=5.
    # The shoulder's lower face is the original rod clamping datum Z=-3.2.
    outline=[(1.5,-30.4),(4.1,-33),(29.9,-33),(32.5,-30.4),
             (32.5,2.4),(29.9,5),(4.1,5),(1.5,2.4)]
    old=rounded(17,-14,-7.1,31,38,3.9,2.6)
    new=prism_xy(outline,-7.1,3.9)
    s=s.cut(old.cut(new))
    # Extend the outer cup with tangent lead-ins and retain sufficient wall at
    # the apex of the keeper pocket. All additions lie below the clamp shoulder.
    for direction in [(0,1,0),(0,-1,0)]:
        s=s.fuse(roof((17,-24.5,-15.2),(0,0,1),direction,6.85,10.4))
    for z0,z1,r in [(-20.,-13.47,4.63),(-13.47,-5.10,3.12),(-5.10,.52,1.78)]:
        s=s.cut(roof((17,-24.5,z0),(0,0,1),(0,-1,0),r,z1-z0))
    # A 45-degree underside lead-in replaces the shelf at the palm/root joint.
    lead=(cq.Workplane("YZ",origin=(8,0,0))
          .polyline([(-1,-11.1),(4,-11.1),(4,-7.1),(3,-7.1)]).close().extrude(18).val())
    return s.cut(lead).clean()


def pkcell():
    s=box(-17.65,-31.15,0,35.3,62.3,5.3)
    for x in [-1.45,1.45]:
        c=(x,31.35,2.65)
        s=s.cut(cyl(.80,6,c,(0,-1,0)),roof(c,(0,-1,0),(0,0,1),.80,6))
    return s.clean()


def alternate():
    source=HERE/"inputs/Adafruit-258.step"
    if not source.is_file():
        source=HERE.parent/"rev-F/review/inputs/Adafruit-258.step"
    ss=cq.importers.importStep(str(source)).val().Solids()
    return ss[0].fuse(*ss[1:]).clean()


# Rotation about world axis, in degrees, converts assembly coordinates to build coordinates.
PARTS={
    "housing-battery-bay":("Housing",case,(0,1,0),-45,"West rear 45-degree land", "8 mm outer brim"),
    "bezel":("Bezel",bezel,(1,0,0),180,"Front bezel face","None"),
    "rotor":("Rotor",rotor,(0,1,0),45,"Oblique outer rim land","5 mm outer brim"),
    "folding-stem":("Stem",stem,(1,0,0),-45,"Oblique flat on hinge eye","5 mm outer brim"),
    "grip":("Grip",knob,(1,0,0),90,"Sleeve end","None"),
    "collar":("Collar",None,(0,1,0),90,"Annular thrust face","None"),
    "power-cap":("Key cap",None,(1,0,0),90,"Back flange face","None"),
    "rod-grip":("Removable rod grip",handle,(1,0,0),-90,"Flat dovetail leading nose","8 mm outer brim"),
    "grip-screw-keeper":("Grip screw keeper",None,(1,0,0),0,"Washer face","None"),
    "receiver-nut-keeper":("Receiver nut keeper",None,(1,0,0),180,"Closed flat cap face","None"),
    "key-board-retainer-west":("Retainer",retainer,(1,0,0),180,"Top bar face","None"),
    "battery-wire-bridge":("bridge",None,(1,0,0),0,"Flat deck underside","None"),
    "PKCELL-max-body-with-wire-sockets":(None,pkcell,(1,0,0),0,"Maximum-pack broad face","None"),
    "Adafruit-258-CAD-with-PCM-and-stubs":(None,alternate,(1,0,0),90,"Flat end opposite lead stubs","5 mm outer brim"),
}


def build():
    (HERE/"CAD").mkdir(exist_ok=True)
    (HERE/"Print").mkdir(exist_ok=True)
    orientations={}
    with tempfile.TemporaryDirectory() as tmp, ZipFile(HERE/"inputs/rev-G-print-datums.zip") as archive:
        for name,(key,update,axis,deg,face,brim) in PARTS.items():
            if key:
                path=Path(tmp)/(key+".brep")
                path.write_bytes(archive.read(path.name))
                stock=cq.Shape.importBrep(str(path))
                s=update(stock) if update else stock
            else:
                s=update()
            assert s.isValid() and len(s.Solids())==1,name
            # Do not propagate the mesh triangulations from source CAD into the STL export.
            s=s.Solids()[0]
            s.exportBrep(str(HERE/"CAD"/(name+".brep")))
            tilted=s.rotate(ORIGIN,axis,deg)
            b=tilted.BoundingBox()
            translation=(-(b.xmax+b.xmin)/2,-(b.ymax+b.ymin)/2,-b.zmin)
            plate=tilted.translate(translation)
            folder="Inert-gauges" if not key and (HERE/"Inert-gauges").is_dir() else "Print"
            out=HERE/folder/(name+".stl")
            cq.exporters.export(plate,str(out),tolerance=.015,angularTolerance=.065)
            mesh=trimesh.load_mesh(out)
            assert mesh.is_volume and mesh.is_watertight and len(mesh.split())==1,name
            assert abs(mesh.volume-s.Volume()) < s.Volume()*.004,name
            matrix=trimesh.transformations.rotation_matrix(math.radians(deg),axis)
            matrix[:3,3]=translation
            orientations[name]=dict(viewer_id=key,coordinate_frame="assembly" if key else "supplier gauge",
                original_stl=("rev-G/Print/" if key else "rev-F/review/gauges/")+out.name,
                assembly_brep="CAD/"+name+".brep", print_stl=folder+"/"+out.name,
                assembly_to_print=matrix.round(10).tolist(),build_up_assembly=matrix[2,:3].round(10).tolist(),
                bed_face=face,brim=brim,assembly_volume_mm3=round(s.Volume(),4),
                extents_mm=mesh.extents.round(4).tolist(),sha256=hashlib.sha256(out.read_bytes()).hexdigest())
            print(name, round(s.Volume(),2), flush=True)
    (HERE/"part-orientations.json").write_text(json.dumps(orientations,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    build()
