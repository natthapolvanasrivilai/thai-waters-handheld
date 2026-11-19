"""Independent USB insertion and external sightline tests. All CAD and measurements are in millimeters."""
import argparse
import itertools
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

QA = Path(__file__).resolve().parent
R9 = QA.parent
R8 = R9.with_name("TW-A-0001-R0008")
MOUTH = -40.0
CY, CZ = 0.0, 19.33


def read(path):
    return cq.Shape.importBrep(str(path))


def capsule(x0, x1, w, h, radius, dy=0., dz=0.):
    # A rectangular section with four circular corners; thickness is limited by h.
    work = cq.Workplane("YZ", origin=(x0, CY+dy, CZ+dz))
    prism = work.rect(w, h).extrude(x1-x0)
    return prism.edges("|X").fillet(radius).val()


def locator(shapes):
    points, faces = [], []
    for shape in shapes:
        vertices, triangles = shape.tessellate(.025, .07)
        offset = len(points)
        points.extend(v.toTuple() for v in vertices)
        faces.extend((3, offset+a, offset+b, offset+c) for a,b,c in triangles)
    pts = vtk.vtkPoints()
    pts.SetData(numpy_to_vtk(np.array(points, dtype=np.float64), deep=True))
    tri = vtk.vtkCellArray()
    tri.SetCells(len(faces), numpy_to_vtkIdTypeArray(np.array(faces, dtype=np.int64).ravel(),deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(pts)
    poly.SetPolys(tri)
    tree = vtk.vtkStaticCellLocator()
    tree.SetDataSet(poly)
    tree.BuildLocator()
    return tree


def sight(shapes, usb, yz_shift=(0.,0.), steps=(0,15,30), pitch=.2, mouth=MOUTH, planes=(-39.90,-38.00,-36.00)):
    tree = locator([*shapes,usb])
    t,sid,cid=vtk.reference(0.),vtk.reference(0),vtk.reference(0)
    hit,pc,cell=[0.,0.,0.],[0.,0.,0.],vtk.vtkGenericCell()
    # At these x values the approved socket CAD has a rounded metal envelope.
    # Exclude its intended projection including the connector's central mating volume.
    # Test all surrounding material, including slight gaps between the shroud and the mask.
    results = {}
    dx0=-60.
    off_y,off_z = yz_shift
    for end in planes:
        counts=[]
        for ay,az in itertools.product(sorted({d*s for d in steps for s in (-1,1)}),repeat=2):
            sy=math.tan(math.radians(ay))
            sz=math.tan(math.radians(az))
            examples=[]
            along_mouth=0
            checked=opened=0
            for y in np.arange(-7.8,7.8+.001,pitch):
                for z in np.arange(CZ-4.7,CZ+4.7+.001,pitch):
                    # If inside conservative 8.94 x 3.16 outer shell projection, the
                    # OEM connector is the intended visible component. Rounded corners
                    # outside this envelope are still checked. Shroud metal itself blocks rays.
                    rr=1.25
                    ry=max(0.,abs(y-off_y)-(4.47-rr))
                    rz=max(0.,abs(z-CZ-off_z)-(1.58-rr))
                    if ry*ry+rz*rz<=rr*rr:
                        continue
                    checked+=1
                    p1=(end,y,z)
                    p0=(dx0,y-(end-dx0)*sy,z-(end-dx0)*sz)
                    if not tree.IntersectWithLine(p0,p1,.00001,t,hit,pc,sid,cid,cell):
                        # A clear segment which crosses through the OEM mouth is
                        # distinct from a second opening around the socket perimeter.
                        lip_y=y-(end-mouth)*sy-off_y
                        lip_z=z-(end-mouth)*sz-CZ-off_z
                        mry=max(0.,abs(lip_y)-(4.47-rr))
                        mrz=max(0.,abs(lip_z)-(1.58-rr))
                        if mry*mry+mrz*mrz<=rr*rr:
                            along_mouth+=1
                            continue
                        opened+=1
                        if len(examples)<2:
                            examples.append([round(y,3),round(z,3)])
            counts.append(dict(yaw_deg=ay,pitch_deg=az,checked=checked,around_shield=opened,through_mouth=along_mouth,clear=opened+along_mouth,
                               sample_visible_yz_mm=examples))
        results[str(end)]=counts
    return results


def sweep(shapes, w, h, radius, offset, allowance, metal=False):
    # Assembly displacement moves the plug center together with its mating socket.
    # allowance dilates the keepout on each printed side as an adverse print allowance.
    # At worst shoulder lead-in: 6.55 mm sleeve less 6.40 mm insertion leaves 0.15 mm.
    # For the shell test start at the mating shoulder, then include full external approach as well.
    rows=[]
    for dx,dy,dz in itertools.product(*[(-v,v) if v else (0.,) for v in offset]):
        end=MOUTH+dx+(6.40 if metal else -.15)
        plug=capsule(-68.,end,w+2*allowance,h+2*allowance,radius+allowance,dy,dz)
        hits={}
        gaps={}
        for name,shape in shapes.items():
            inter=plug.intersect(shape)
            volume=sum(s.Volume() for s in inter.Solids())
            hits[name]=round(volume,6)
            gaps[name]=round(plug.distance(shape),5)
        rows.append(dict(offset_mm=[dx,dy,dz],furthest_x_mm=round(end,4),intersection_mm3=hits,
                         minimum_clearance_mm=gaps))
    return rows


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--legacy",action="store_true")
    p.add_argument("--cache",type=Path,required=True,help="Rev G reference extraction from R0008 audit_fit.py")
    p.add_argument("--printed",nargs="+",default=["housing-battery-bay","bezel"],help="Printed CAD file stems in assembly axes")
    p.add_argument("--mask-metal",nargs="*",default=[],help="Other opaque assembled CAD file stems (omit transparent optical elements)")
    p.add_argument("--offset",type=float,nargs=3,default=[.15,.15,.15])
    p.add_argument("--print-allowance",type=float,default=.10)
    p.add_argument("--grid",type=float,default=.2)
    p.add_argument("--view",type=float,nargs="+",default=[0.,15.,30.])
    p.add_argument("--custom",nargs=3,type=float,metavar=("W","H","R"))
    args=p.parse_args()
    rev=R8 if args.legacy else R9
    shapes={stem:read(rev/"CAD"/(stem+".brep")) for stem in args.printed}
    opaque=[read(rev/"CAD"/(stem+".brep")) for stem in args.mask_metal]
    usb=read(args.cache/"A1-usb.brep")
    result=dict(revision=rev.name,socket_mouth_x_mm=MOUTH,socket_axis_yz_mm=[CY,CZ],
                real_mating_insert_range_mm=[6.00,6.40],old_gauge_nose_x_mm=-40.,
                old_gauge_axis_yz_mm=[0.,19.70],old_gauge_engagement_mm=0.,
                print_allowance_each_side_mm=args.print_allowance,assembly_shift_each_axis_mm=args.offset,
                printed=list(shapes),geometric_exterior_only=True)
    result["nominal_rounded_overmold"]=sweep(shapes,12.35,6.50,1.,[0.,0.,0.],0.)
    result["max_rounded_overmold"]=sweep(shapes,12.35,6.50,1.,args.offset,args.print_allowance)
    # The USB sleeve has continuous curved ends. A smaller 1 mm corner radius
    # conservatively enlarges those corners relative to the USB plug outline.
    result["max_metal_shell"]=sweep(shapes,8.28,2.43,1.,args.offset,args.print_allowance,metal=True)
    if args.custom:
        result["custom_w_h_r_mm"]=args.custom
        result["custom_body"]=sweep(shapes,*args.custom,args.offset,args.print_allowance)
    result["ray_grid_pitch_mm"]=args.grid
    result["exterior_visibility"]=sight([*shapes.values(),*opaque],usb,steps=args.view,pitch=args.grid)
    path=QA/("legacy-port.json" if args.legacy else "usb-port.json")
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(path)
    for label,rows in result.items():
        if isinstance(rows,list) and rows and isinstance(rows[0],dict) and "intersection_mm3" in rows[0]:
            print(label,max(max(row["intersection_mm3"].values()) for row in rows),min(min(row["minimum_clearance_mm"].values()) for row in rows))
    for x,rows in result["exterior_visibility"].items():
        print(x,sum(r["clear"] for r in rows),sum(r["checked"] for r in rows))


if __name__=="__main__":
    main()
