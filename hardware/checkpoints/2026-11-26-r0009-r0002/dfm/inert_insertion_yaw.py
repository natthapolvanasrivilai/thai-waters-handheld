"""Exact-source conservative continuous vertical inert-gauge insertion screen."""
import cadquery as cq, json, hashlib, math
from pathlib import Path
P=Path(__file__).parent
def read(name,digest):
    p=P/name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
    s,=cq.importers.importStep(str(p)).val().Solids()
    assert s.isValid()
    return s
shell=read('housing.step','dbea143bbe452069f60fbcec954038f8abf357c15469f1030fbab4adc392f0ce')
gauge=read('pcb-gauge.step','8259c95ca00ad9f6a05c805d8278c685207b98dba977544d198aca7279192a52').rotate((0,0,0),(1,0,0),180).translate((13,-14,18.5))
b=gauge.BoundingBox()
def vol(s):
    return sum(t.Volume() for t in s.Solids())
assert all(f.geomType() in ("PLANE","CYLINDER") for f in gauge.Faces())
faces=[f for f in gauge.Faces() if f.geomType()=="PLANE" and f.normalAt().z<-.99999]
# Each vertical XY column begins on a downward face. Preserve its holes.
def envelope(top):
    parts=[cq.Solid.extrudeLinear(f.outerWire(),f.innerWires(),cq.Vector(0,0,top-f.Center().z)) for f in faces]
    return parts[0].fuse(*parts[1:]).clean()
base=envelope(b.zmax)
assert vol(gauge.cut(base))<1e-6
assert vol(base.cut(gauge))<1e-6
env=envelope(b.zmax+32)
assert env.isValid() and len(env.Solids())==1
def score(dx,dy,dz=0):
    return vol(shell.intersect(env.translate((dx,dy,dz))))
board=max(faces,key=lambda f:f.Area())
bb=board.BoundingBox()
mx,my=(bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2
bottom=board.Center().z
top=b.zmax+32
def span(l,u,v,w,a):
    # Extremal rotated projections over the whole yaw interval, not angular samples.
    xs,ys=[],[]
    for x,y in [(l,v),(l,w),(u,v),(u,w)]:
        for C,D,values in [(x,-y,xs),(y,x,ys)]:
            poles=[math.atan2(D,C)+k*math.pi for k in range(-2,3)]
            for t in (-a,a,*[p for p in poles if -a<p<a]):
                values.append(C*math.cos(t)+D*math.sin(t))
    return min(xs),max(xs),min(ys),max(ys)
board0=cq.Solid.extrudeLinear(board.outerWire(),[],cq.Vector(0,0,top-bottom))
def plate(a,d):
    rad=1.5
    u,v=bb.xlen/2-rad,bb.ylen/2-rad
    x0,x1,y0,y1=span(-u,u,-v,v,a)
    return (cq.Workplane('XY').rect(x1-x0+2*(rad+d),y1-y0+2*(rad+d)).extrude(top-bottom)
        .edges('|Z').fillet(rad+d).val().translate((mx,my,bottom)))
assert vol(board0.cut(plate(0,0)))<1e-6
def score(a,d):
    parts=[('substrate',plate(a,d))]
    for i,f in enumerate(faces):
        if f is board: continue
        j=f.BoundingBox()
        x0,x1,y0,y1=span(j.xmin-mx,j.xmax-mx,j.ymin-my,j.ymax-my,a)
        z=f.Center().z
        p=cq.Solid.makeBox(x1-x0+2*d,y1-y0+2*d,top-z,cq.Vector(mx+x0-d,my+y0-d,z))
        parts.append((i,p))
    bad=[]
    for key,p in parts:
        v=vol(shell.intersect(p))
        if v>=1e-6: bad.append([key,v])
    return bad
# Verify analytic extrema enclose odd increments and preserve exact zero-span.
assert span(-2,7,-9,4,0)==(-2,7,-9,4)
for l,u,v,w in [(-1,3,-4,2), (1,3,4,6), (-2,5,-7,-3),(-3,-1,4,7)]:
    a=.11
    x0,x1,y0,y1=span(l,u,v,w,a)
    for k in range(31):
        t=a*(k-15)/15
        for x in (l,u):
            for y in (v,w):
                q=x*math.cos(t)-y*math.sin(t);r=x*math.sin(t)+y*math.cos(t)
                assert x0-1e-10<=q<=x1+1e-10 and y0-1e-10<=r<=y1+1e-10
rows=[]
for deg,d in [(0,0),(0,.70),(.5,.5), (1,.5), (1.5,.4),(2,.2),(3,0),(5,.5)]:
    rows.append(dict(yaw_each_side_deg=deg,xy_disk_radius_mm=d,collisions=score(math.radians(deg),d)))
assert not rows[0]['collisions'] and not rows[1]['collisions'] and rows[-1]['collisions']
exact_rows=[]
for t,d in [(1,.5),(1.5,.4),(3,0),(5,.5)]:
    for sign in (-1,1):
        s=env.rotate((mx,my,0),(mx,my,1),sign*t).translate((d,0,0))
        exact_rows.append(dict(yaw_deg=sign*t,xy_offset_mm=[d,0],overlap_mm3=vol(shell.intersect(s))))
print(json.dumps(dict(scope='Exact hash-checked R0009 inert parts; conservative bound over full vertical 32 mm path, all XY translations in disk and all yaw angles within stated limits; level, no tilt or native/physical outcome.',
 yaw_axis_xy_mm=[mx,my],rows=rows,exact_spot_checks=exact_rows),indent=2))
