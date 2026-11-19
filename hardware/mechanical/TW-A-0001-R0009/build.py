"""R0009 west-side USB-C well, soft shield mask and three independent status guides.
Assembly millimetres. West is -X. The USB shield face is X=-40, Y=0, Z=19.33.
"""
from pathlib import Path
import hashlib,json,math,shutil
import cadquery as cq
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/"TW-A-0001-R0008"
V=cq.Vector
O=(0,0,0)
ZC=19.33

def box(x,y,z,w,d,h):
    return cq.Solid.makeBox(w,d,h,V(x,y,z))

def rr(x,y,z,w,h,r):
    """Wire on an X station, containing true quadrant arcs."""
    work=cq.Workplane("YZ",origin=(x,y,z))
    dx,dz=w/2,h/2
    return (work.moveTo(-dx+r,-dz).lineTo(dx-r,-dz).radiusArc((dx,-dz+r),-r)
        .lineTo(dx,dz-r).radiusArc((dx-r,dz),-r).lineTo(-dx+r,dz)
        .radiusArc((-dx,dz-r),-r).lineTo(-dx,-dz+r).radiusArc((-dx+r,-dz),-r).close().val())

def loft(*wires):
    return cq.Solid.makeLoft(list(wires),True)

def rounded(x0,x1,y,z,w,h,r):
    return loft(rr(x0,y,z,w,h,r),rr(x1,y,z,w,h,r))

def polygon(x,y,z,points):
    vs=[V(x,y+dy,z+dz) for dy,dz in points]
    return cq.Wire.makePolygon(vs+[vs[0]])

def octagon(x,y,z,r):
    chamfer=r*(math.sqrt(2)-1)
    return polygon(x,y,z,[(-chamfer,-r),(chamfer,-r),(r,-chamfer),(r,chamfer),
                         (chamfer,r),(-chamfer,r),(-r,chamfer),(-r,-chamfer)])

def bar(a,b,r):
    return loft(octagon(*a,r),octagon(*b,r))

# Each physically separate straight optical core has a planar polished face at each end.
# Westmost point remains within 0.04 mm of the plate's exterior surface.
GUIDES={
    "statusChgGuide":((-49.97,-6.05,13.10),(-39.13,-10.021,20.75),.60),
    "statusUsbGuide":((-49.97,0.,13.10),(-42.65,0.,13.10),.60),
    "statusPwrGuide":((-49.97,6.05,13.10),(-39.13,9.979,20.75),.60),
}
STEMS={"usbSurround":"usb-c-shield-mask","statusChgGuide":"status-charge-guide",
       "statusUsbGuide":"status-usb-guide","statusPwrGuide":"status-power-guide"}

def marking(y,char):
    # 0.50 mm line weight, 2.2 mm high. Closed depressions in opaque plastic.
    z=12.00
    y+=2.20
    strokes={"C":[(-.8,0,.5,2.2),(-.8,0,1.60,.5),(-.8,1.7,1.60,.5)],
             "U":[(-.8,0,.5,2.2),(.30,0,.5,2.2),(-.8,0,1.6,.5)],
             "P":[(-.8,0,.5,2.2),(-.8,1.7,1.6,.5),(.3,.8,.5,1.4),(-.8,.8,1.6,.5)]}
    bits=[box(-50.03,y-dy-w,z+dz,.36,w,h) for dy,dz,w,h in strokes[char]]
    return bits[0].fuse(*bits[1:]).clean()

def mask_blank():
    return loft(rr(-39.78,0,ZC,13.64,7.77,.86),
                rr(-39.56,0,ZC,13.88,8.01,.98),
                rr(-39.27,0,ZC,13.64,7.77,.86))

def tracking_regions(offset=(0.,0.,0.), free=False):
    """Continuous registered TPU membrane. The bead stays in the housing groove."""
    dx,dy,dz=offset
    if free and any(offset):raise ValueError("Report the free part at its own centered datum")
    preload=.38 if free else 0.
    front=-39.78
    end=-39.27
    def fixed(x):return rr(x,0,ZC,12.60,6.82,1.78)
    def outer(x):return rr(x+dx,dy,ZC+dz,10.44-2*preload,4.66-2*preload,2.03-preload)
    def opening(x):return rr(x+dx,dy,ZC+dz,8.94-2*preload,3.16-2*preload,1.28-preload)
    flange=mask_blank().cut(loft(fixed(front-.01),fixed(end+.01)))
    def area(w,h,r):return w*h-(4-math.pi)*r*r
    af=area(12.60,6.82,1.78)
    ao=area(10.44,4.66,2.03)
    ai=area(8.94,3.16,1.28)
    free_outer=area(9.68,3.90,1.65)
    free_inner=area(8.18,2.40,.90)
    # Preserve the volume of each nominally incompressible polymer region.
    thickness=.32 if free else .32*(af-free_outer)/(af-ao)
    lip_depth=.51 if free else .51*(free_outer-free_inner)/(ao-ai)
    rear=front+thickness
    web=loft(fixed(front),fixed(rear))
    if dx>1e-8:
        web=web.fuse(loft(fixed(rear),outer(rear))).cut(loft(fixed(front),outer(front)))
    elif dx< -1e-8:
        web=web.fuse(loft(outer(front),fixed(front))).cut(loft(outer(rear),fixed(rear)))
    web=web.cut(loft(outer(front-abs(dx)-.02),outer(rear+abs(dx)+.02))).clean()
    skin=flange.fuse(web).clean()
    lip=loft(outer(front),outer(front+lip_depth)).cut(loft(opening(front-.01),opening(front+lip_depth+.01))).clean()
    if not (skin.isValid() and lip.isValid()):raise ValueError(("Invalid TPU material region",skin.isValid(),lip.isValid(),web.isValid(),web.Volume(),skin.Volume()))
    return {"usbSurround":skin,"usbEscutcheonLip":lip}

def shield_mask(offset=(0.,0.,0.), free=False):
    skin,lip=tracking_regions(offset,free).values()
    return skin.fuse(lip).clean()

SPEAKER_X=-40.52
SPEAKER_Z=4.95

def speaker_gasket():
    # Custom die-cut closed-cell adhesive ring. The speaker's cloth front faces
    # the original bottom grille. The gasket bounds the acoustic front cavity.
    def xy(w,h,r,z,t):
        return cq.Workplane("XY").box(w,h,t).edges("|Z").fillet(r).val().translate((SPEAKER_X,0,z+t/2))
    return xy(19.55,29.24,2.2,4.25,.50).cut(xy(17.23,26.92,1.43,4.24,.53)).clean()

def speaker_cradle(base):
    # Outward local extension retains the working west wall while keeping the
    # bezel, board mount, battery entry path and rod receiver on their datums.
    outline=[(-52.22,-15.30),(-49.4,-18.12),(-47.05,-18.12),
             (-47.05,18.12),(-49.4,18.12),(-52.22,15.30)]
    cheek=cq.Workplane("XY",origin=(0,0,0)).polyline(outline).close().extrude(11.56).edges("|Z").fillet(1.10).val()
    # The lower transition extends the existing oblique bed land continuously.
    xz=lambda pts:cq.Workplane("XZ",origin=(0,30,0)).polyline(pts).close().extrude(60).val()
    bottom=xz([(-65,-10),(-38,-10),(-65,17)])
    # Under the engraved legends the upper shoulder returns to the existing wall.
    top=xz([(-57,8),(-52.22,10.12),(-49.83,11.56),(-49.83,12),(-57,12)])
    cheek=cheek.cut(bottom,top)
    body=base.fuse(cheek)
    # A compliant continuous gasket sits on an annular shelf. Its inner opening
    # feeds the original west grille. Leave the rest of the battery rail intact.
    outer=cq.Workplane("XY").box(20.50,30.20,5).edges("|Z").fillet(1.5).val().translate((SPEAKER_X,0,6.75))
    body=body.cut(outer)
    seat=cq.Workplane("XY").box(20.50,30.20,1.86).edges("|Z").fillet(1.5).val().translate((SPEAKER_X,0,3.32))
    empty=cq.Workplane("XY").box(17.12,26.80,2.2).edges("|Z").fillet(1.42).val().translate((SPEAKER_X,0,3.30))
    body=body.fuse(seat.cut(empty))
    # Locate the long sides with short ridges outside the 19.9 mm package.
    # Remove all stock in the installed gasket and supplier bounding footprint;
    # the 0.30 mm side allowance is measured against the actual supplied frame.
    upper=box(SPEAKER_X-10.25,-15.10,9.23,20.50,30.20,1.10)
    # The speaker slides sideways above the rails. Its magnet extends a little
    # farther into the west inner wall before it can drop onto the gasket.
    mag=box(-48.75,-8.1,9.22,8.2,16.2,1.43)
    return body.cut(upper,mag,bottom).clean()

def housing(base):
    # Fill the historical 15.5 x 8.4 hole on its own straight part of the wall.
    patch=box(-50,-8.05,15.97,2.4,16.10,8.49)
    guard=rounded(-49.8,-39.21,0,ZC,17.52,10.36,1.48)
    # Side/back/floor privacy cup inside the main case. Its open top accepts the
    # OEM connector descending with its PCB; everything remains below PCB Z21.
    inner_guard=box(-39.58,-5.63,16.50,7.92,11.26,4.27)
    cavity=box(-39.80,-4.84,17.43,7.43,9.68,4.)
    inner_guard=inner_guard.cut(cavity)
    s=base.fuse(patch,guard,inner_guard,box(-40.2,-5.65,14.57,2.25,11.30,2.26))
    # Shell-colour lead-in and well continue for the entire overmold insertion stroke.
    # Largest inspected overmold is 12.35 x 6.5, seated as far as X=-40.15.
    entry=loft(rr(-50.12,0,ZC,14.74,8.46,1.56),rr(-47.2,0,ZC,13.62,7.76,.85))
    throat=rounded(-47.21,-39.23,0,ZC,13.62,7.76,.85)
    s=s.cut(entry,throat)
    # At the rear the rigid baffle returns behind the lower and side portions
    # of the flexible diaphragm. The continuously seated perimeter closes the
    # oblique sightline without occupying any portion of the cable shoulder.
    rear=rounded(-39.42,-38.70,0,ZC,17.52,10.36,1.48)
    rear=rear.cut(box(-39.19,-9,20.81,1.1,18,8),
                  rounded(-39.6,-38.4,0,ZC,10.0,4.23,1.46))
    s=s.fuse(rear).cut(mask_blank())
    # Individual opaque sheaths keep each core separate up to its original emitter.
    for k,(front,rear,r) in GUIDES.items():
        a=np.array(front);b=np.array(rear);d=(b-a)/(b[0]-a[0])
        outer_a=a+d*(-49.85-a[0]); outer_b=b.copy()
        if k!="statusUsbGuide":
            # Limit the end collector height to avoid the PCB at z >= 21.
            outer_b=b-d*.26
        sleeve=bar(tuple(outer_a),tuple(outer_b),r+.85)
        s=s.fuse(sleeve)
    # Blue LED board guides, with two captured edges and a lower seating shelf.
    s=s.fuse(box(-43.25,-2.92,10.82,2.00,5.84,.61),
             box(-43.25,-2.95,11.32,2.00,.59,3.55),box(-43.25,2.36,11.32,2.00,.59,3.55))
    s=s.cut(box(-42.20,-2.52,11.39,.81,5.04,4.00))
    for front,rear,r in GUIDES.values():
        a=np.array(front);b=np.array(rear);d=(b-a)/(b[0]-a[0])
        s=s.cut(bar(tuple(a-d*.35),tuple(b+d*.14),r+.12))
    for y,ch in [(-6.05,"C"),(0,"U"),(6.05,"P")]:
        s=s.cut(marking(y,ch))
    # Cut the full mated overmold envelope again after adding the sheaths so
    # an intersection of the optical shroud cannot intrude into the cable path.
    s=s.cut(entry,rounded(-47.21,-39.78,0,ZC,13.62,7.76,.85),mask_blank(),rounded(-39.32,-38.40,0,ZC,10.0,4.23,1.46))
    # The concealed rear half of the groove follows an 11 degree taper.
    rear_relief=loft(rr(-39.56,0,ZC,13.88,8.01,.98),rr(-39.25,0,ZC,13.76,7.89,.92))
    s=s.cut(rear_relief,rounded(-39.33,-39.09,0,ZC,12.0,6.20,1.95))
    # W2-A genuine 6.00 mm JST header sits on the original Z8.40 saddle.
    # Move the cheeks to either side of the sourced body and leave the
    # PHR-2 completely free to withdraw west along the original mating axis.
    s=s.cut(box(20.0,-26.18,8.40,7.75,6.36,6.3))
    for y in (-26.88,-19.82):
        s=s.fuse(box(21.65,y,2.45,4.8,.70,7.50))
    return s.clean()

def shape_sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def plate(name,s,up):
    axis=np.cross(up,[0,0,1]);angle=math.degrees(math.acos(np.clip(np.dot(up,[0,0,1]),-1,1)))
    if np.linalg.norm(axis)<1.e-8:axis=np.array([1,0,0])
    t=s.rotate(O,tuple(axis),angle)
    b=t.BoundingBox()
    shift=(-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin)
    p=HERE/"Print"/(name+".stl")
    cq.exporters.export(t.translate(shift),str(p),tolerance=.015,angularTolerance=.065)
    q=trimesh.load_mesh(p)
    if not (q.is_watertight and q.is_volume and len(q.split())==1):raise ValueError((name,"nonmanifold STL"))
    mat=trimesh.transformations.rotation_matrix(math.radians(angle),axis)
    mat[:3,3]=shift
    return p,mat,q

def main(prior=OLD):
    (HERE/"CAD").mkdir(exist_ok=True)
    (HERE/"Print").mkdir(exist_ok=True)
    meta=json.loads((prior/"part-orientations.json").read_text())
    for name,r in meta.items():
        if name!="housing-battery-bay":
            shutil.copyfile(prior/r["assembly_brep"],HERE/r["assembly_brep"])
            shutil.copyfile(prior/r["print_stl"],HERE/r["print_stl"])
            r["original_stl"]="TW-A-0001-R0008/"+r["print_stl"]
    # Keep the hinge seat height and enlarge only the H2 head counterbore to suit
    # the sourced ISO 14583 M2 pan head. The inherited diagonal print land remains intact.
    r=cq.Shape.importBrep(str(prior/"CAD/rotor.brep"))
    r=r.cut(cq.Solid.makeCylinder(2.20,8.0,V(53.6,7.8,19.60))).clean()
    assert r.isValid() and len(r.Solids())==1
    r.exportBrep(str(HERE/"CAD/rotor.brep"))
    up=np.array(meta["rotor"]["build_up_assembly"]);up/=np.linalg.norm(up)
    rp,rm,rmesh=plate("rotor",r,up)
    meta["rotor"].update(assembly_volume_mm3=round(r.Volume(),4),sha256=shape_sha(rp),
                         extents_mm=rmesh.extents.round(4).tolist(),assembly_to_print=rm.round(10).tolist())
    h=cq.Shape.importBrep(str(prior/"CAD/housing-battery-bay.brep"))
    hs=speaker_cradle(housing(h))
    shapes={"Housing":hs,"usbSurround":shield_mask()}
    for k,(a,b,r) in GUIDES.items():
        shapes[k]=bar(a,b,r)
    for key,s in shapes.items():
        name="housing-battery-bay" if key=="Housing" else STEMS[key]
        if not s.isValid() or len(s.Solids())!=1:raise ValueError((name,"invalid CAD",len(s.Solids())))
        s=s.Solids()[0];s.exportBrep(str(HERE/"CAD"/(name+".brep")))
        if key=="Housing":
            up=np.array([1.,0,1.])/math.sqrt(2);bed="West rear 45-degree land";brim="8 mm outer brim";material="Opaque PETG, case colour"
        elif key=="usbSurround":
            up=np.array([1.,0,0]);bed="Full outward-facing diaphragm";brim="None";material="Opaque TPU 95A, shell-colour flange and matte charcoal lip"
        else:
            # Put a complete longitudinal flat on the bed. Select the widest
            # viable contact side that keeps both polished facet ends upright.
            a,b,_=GUIDES[key]
            vector=np.array(b)-a
            up=np.array([-vector[1]/vector[0],1.,0]);up=up/np.linalg.norm(up)
            bed="Longitudinal guide flat";brim="3 mm outer brim";material="Clear optical-grade resin or transparent PETG fit prototype"
        print_body=shield_mask(free=True) if key=="usbSurround" else s
        p,mat,q=plate(name,print_body,up)
        if key=="usbSurround":
            print_body.exportBrep(str(HERE/"CAD/usb-c-shield-mask-unloaded.brep"))
        meta[name]=dict(viewer_id=key,coordinate_frame="assembly",original_stl=("TW-A-0001-R0008/Print/"+name+".stl" if key=="Housing" else None),
                assembly_brep="CAD/"+name+".brep",print_stl="Print/"+p.name,assembly_to_print=mat.round(10).tolist(),build_up_assembly=up.round(10).tolist(),
                bed_face=bed,brim=brim,material=material,assembly_volume_mm3=round(s.Volume(),4),
                extents_mm=q.extents.round(4).tolist(),sha256=shape_sha(p))
        if key=="usbSurround":
            meta[name].update(print_source_brep="CAD/usb-c-shield-mask-unloaded.brep",
                              shape_state="Preloaded service shape in assembly_brep; stress-free shape in print_source_brep and print_stl.",
                              print_volume_mm3=round(print_body.Volume(),4),radial_preload_mm=.38)
        print(key,s.Volume(),flush=True)
    (HERE/"part-orientations.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf8")

if __name__=="__main__":
    if OLD.is_dir():
        main()
    else:
        import tempfile
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as scratch:
            target=Path(scratch)
            with ZipFile(HERE/"inputs/R0008-print-inputs.zip") as archive:
                for name in archive.namelist():
                    dest=(target/name).resolve()
                    if not dest.is_relative_to(target.resolve()):raise ValueError(name)
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes(archive.read(name))
            main(target)



