"""Millimetre geometry shared by the dressing fixture and service checks."""
import cadquery as cq

V = cq.Vector

def cylinder(a, b, radius):
    a,b=V(*a),V(*b)
    return cq.Solid.makeCylinder(radius,(b-a).Length,a,(b-a).normalized())

def box(x,y,z,dx,dy,dz):
    return cq.Solid.makeBox(dx,dy,dz,V(x,y,z))

def sweep(edge, radius):
    return cq.Solid.sweep(cq.Wire.makeCircle(radius,edge.startPoint(),edge.tangentAt(0)),[],edge,True,False)

def polyline(points, radius):
    segments=[cylinder(a,b,radius) for a,b in zip(points,points[1:])]
    balls=[cq.Solid.makeSphere(radius,V(*p),angleDegrees1=-90,angleDegrees2=90) for p in points[1:-1]]
    return segments[0].fuse(*segments[1:],*balls).clean()

