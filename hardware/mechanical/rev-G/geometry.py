"""Rev G battery bay and harness. Assembly coordinates and dimensions are millimetres."""
import math
import cadquery as cq

V = cq.Vector
CX, CY, Z = -10.4, -.65, 3.6
EDGE = 4.2   # centerline radius of the lead turnaround, three assumed wire diameters
PLUG = (14., -25., 8.65)
def box(x,y,z,w,l,h):
    return cq.Solid.makeBox(w,l,h,V(x,y,z))
def round_box(x,y,z,w,l,h,r):
    return cq.Workplane('XY').box(w,l,h).edges('|Z').fillet(r).val().translate((x,y,z+h/2))

def skew(part):
    return part.rotate((-31.85,18.5,0),(-31.85,18.5,1),-7.4)

def housing(old):
    # Both obsolete fences stop at Z4.9. Start at the existing floor surface.
    cut = box(-31.1,-24,2.5,39.3,48,3)
    # The full drawing block fits within the rectangular bay. The PCM stubs use the local exit.
    bay = box(-29.55,-32.4,3.1,38.3,63.6,7.3)
    outer = cq.Workplane(obj=round_box(CX,33.25,3.2,32,12.9,13.8,5)).edges('>Z or <Z').fillet(1.65).val()
    inner = cq.Workplane(obj=round_box(CX,32.75,5.2,28.0,10.0,9.8,3.1)).edges('>Z or <Z').fillet(.75).val()
    # A re-entrant exit shares the main cavity. Remove any material of the outer
    # reinforcement that projects into the body or cap insertion path.
    # Put the captive key-carrier screw on the west side so an unflexed
    # maximum pack can drop in vertically. Preserve the two straight switch guides.
    boss=cq.Solid.makeCylinder(2.5,8.15,V(-43.2,28.7,9.5)).fuse(box(-44.7,28.55,9.5,3.,4.25,8.15))
    west_pilot=cq.Solid.makeCylinder(.8,5.3,V(-43.2,28.7,12.8))
    boss=boss.cut(west_pilot,box(-41.7,27.65,7.5,11.4,1.28,15))
    east_tip=box(-29.25,26.4,9.49,3.55,6.1,8.18)
    # Trim the pod roof at the full vertical entry, while retaining the cable tunnel.
    outer=outer.cut(box(-29.55,-32.4,2.45,38.3,63.6,25))
    shell = old.cut(east_tip).fuse(outer,boss).cut(cut,bay,inner,box(-22.7,26.6,2.5,24.6,6.05,19)).clean()
    rails=[round_box(x,0,2.45,1.2,40,2.65,.48) for x in (-30.15,9.35)]
    # Thin compliant mounting strips go on these two smooth lands, outside the end folds.
    lands=[round_box(CX,y,2.45,23,6,.65,1.9) for y in (-15,14)]
    # The adapter half is supported outboard of the M3 nut keeper. Its factory mate
    # disconnects toward -X. Side cheeks take the lateral pull on the mated pair.
    x,y,z=PLUG
    seat=round_box(x+10.65,y+2,2.45,5.4,5.8,z-2.45-.25,.6)
    guides=[round_box(x+10.65,yy,2.45,5.5,1.0,z-2.45+1.3,.45) for yy in (y-.85,y+4.85)]
    # The wire bridge lifts out before gauge insertion. Its two screw bosses
    # stand outside the enlarged pouch envelope, away from the protection cap.
    pillars=[cq.Solid.makeCylinder(2.1,7.10,V(xx,18.5,2.45)) for xx in (-31.85,11.1)]
    holes=[cq.Solid.makeCylinder(.80,4.4,V(xx,18.5,5.45)) for xx in (-31.85,11.1)]
    return shell.fuse(*rails,*lands,seat,*guides,*map(skew,pillars)).cut(*map(skew,holes),west_pilot).clean()

def bridge():
    deck=round_box(-10.375,18.5,9.55,47.45,6.4,1.2,1.5)
    high_pad=round_box(-2.05,18.5,10.7,6.9,6.4,2.18,.8)
    holes=[cq.Solid.makeCylinder(1.16,3,V(xx,18.5,9)) for xx in (-31.85,11.1)]
    # A pair of slots per wire carries thin insulating tape around the shelf.
    slots=[round_box(xx,18.5,9.3,1.05,3.7,4.0,.36) for xx in (-23.4,-15.4,-5.96,1.92)]
    return skew(deck.fuse(high_pad).cut(*holes,*slots).clean())
def bridge_screw(x):
    head=cq.Solid.makeCylinder(1.85,1.5,V(x,18.5,10.75))
    return skew(head.fuse(cq.Solid.makeCylinder(1.,4,V(x,18.5,6.75))).clean())

def line(a,b): return cq.Edge.makeLine(V(*a),V(*b))
def arc(a,m,b): return cq.Edge.makeThreePointArc(V(*a),V(*m),V(*b))
def rounded(points,r):
    p=[V(*q) for q in points]; end=p[0]; edges=[]
    for before,corner,after in zip(p,p[1:],p[2:]):
        u=(before-corner).normalized();v=(after-corner).normalized()
        theta=u.getAngle(v)
        if abs(math.pi-theta)<1e-6:continue
        run=r/math.tan(theta/2)
        a=corner+u*run;b=corner+v*run;bis=(u+v).normalized()
        m=corner+bis*(r/math.sin(theta/2)-r)
        if (a-end).dot(u)>1e-5:raise ValueError('Fillets consume adjacent segment')
        if (a-end).Length>1e-7:edges.append(cq.Edge.makeLine(end,a))
        edges.append(cq.Edge.makeThreePointArc(a,m,b));end=b
    edges.append(cq.Edge.makeLine(end,p[-1]));return edges
def sweep(edges,radius):
    path=cq.Wire.assembleEdges(edges)
    circle=cq.Wire.makeCircle(radius,edges[0].startPoint(),edges[0].tangentAt(0))
    return cq.Solid.sweep(circle,[],path,True,False),path.Length()

def factory_lead(variant,i):
    # Native CAD stubs run three millimetres beyond the PCM. The external route
    # begins at their tips. The other pack envelopes start directly on their end face.
    x=CX+((-2,2) if variant=='alt' else (-1.45,1.45))[i]
    y=CY+dict(alt=33.,drawing=31.15,catalog=31.)[variant]
    z=Z+dict(alt=5.5,drawing=2.65,catalog=2.5)[variant]
    high=11.55+i*2.15
    turn_z=11.55+.15*i
    dz=(turn_z-z)/2;dx=(1 if i else -1)*math.sqrt(EDGE**2-dz**2)
    a=(x,y,z);m=(x+dx,y+EDGE,z+dz);b=(x+2*dx,y,turn_z)
    ex,ey,ez=PLUG
    ey+=1.05+1.9*i;ez+=1.6
    def path(detour):
        pts=[b,(b[0],y-3,turn_z),(b[0],y-9,high),(b[0],14-i*3,high),(b[0]-detour,6-i*3,high),
             (b[0]-detour,-15+i*4,high),(ex-6.1,ey,ez),(ex,ey,ez)]
        return [arc(a,m,b),*rounded(pts,3.0)]
    # Take up the stock length with a broad planar bow. Preserve the molded segment.
    target=100-(3 if variant=='alt' else 0)
    lo,hi=0.,22.
    for _ in range(24):
        n=(lo+hi)/2;length=sum(e.Length() for e in path(n))
        if length>target:hi=n
        else:lo=n
    edges=path((lo+hi)/2);body,length=sweep(edges,.70)
    assert abs(length-target)<.02,(variant,i,length,target)
    return body,dict(external_length_mm=round(length,3),molded_stub_mm=100-target,
                     minimum_design_radius_mm=3.0,exit_turn_radius_mm=EDGE,insulation_od_mm=1.4,
                     centerline_mm=[tuple(round(v,3) for v in cq.Wire.assembleEdges(edges).positionAt(k/100).toTuple()) for k in range(101)])
def adapter_lead(i):
    x,y,z=PLUG
    a=(x+13.3,y+1.0+2*i,z+1.35+.50*i)
    b=(32.15-1.95*i,a[1],a[2])
    points=[a,b,(32.15-1.95*i,-14.8-1.45*i,14.35+.18*i),(-24.4-1.75*i,-14.8-1.45*i,14.35+.18*i),
            (-26.4-i*1.65,-7.5+i*2,12.4+i*1.15),(-27.25+1.70*i,16,13.0+i*1.60),
            (-25.8+i*1.62,22.8,15.6+i*1.15)]
    edges=rounded(points,2.0);body,length=sweep(edges,.45)
    # Place insulation on a long straight section, away from the wire's bend.
    straight=next(e for e in edges if e.geomType()=='LINE' and e.Length()>40)
    direction=straight.tangentAt(0);p=straight.positionAt(.44)
    sleeve=cq.Solid.makeCylinder(.72,3.75,p,direction).cut(cq.Solid.makeCylinder(.46,3.95,p-direction*.1,direction))
    return body,sleeve,dict(centerline_corners_mm=points,length_mm=round(length,3),insulation_od_mm=.9,fillet_radius_mm=2.)


def key_keeper(original):
    left=original.mirror('YZ',(-36,0,0))
    fill=cq.Solid.makeCylinder(1.11,1.5,V(-43.7,29.65,17.65))
    bore=cq.Solid.makeCylinder(1.1,2.0,V(-43.2,28.7,17.45))
    cavity=round_box(4.25,0,6.,103.9,64.4,18.,7.7)
    return left.fuse(fill).cut(bore).intersect(cavity).clean()
