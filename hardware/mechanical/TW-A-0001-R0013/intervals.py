"""Bound the in-between motion of each constant-length W4 guide against fixed CAD meshes.

The controls are R(d) + q D(d), where both R and D are affine in travel. q is the positive
solution of L(R+qD)=L0. L is the same positive-weight norm sum as the route solver.
"""
import argparse
import itertools
import math
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.optimize import brentq

from assemble import HERE, WIRES, digest, load, save
from stroke import new_leads
from service_check import read_shapes, tri, model, meshgap, maximum_drawing_pack

def pole_motion(m, net, tx, z, start, end):
    mid=(start+end)/2
    r0,d0=m.base_poles(net,tx,z,start)
    r1,d1=m.base_poles(net,tx,z,end)
    r,d=(r0+r1)/2,(d0+d1)/2
    # Fail closed if a future generator changes the affine-in-travel assumption.
    for u in (.25,.5,.75):
        rv,dv=m.base_poles(net,tx,z,start+(end-start)*u)
        assert np.allclose(rv,r0+(r1-r0)*u,rtol=0,atol=2e-12)
        assert np.allclose(dv,d0+(d1-d0)*u,rtol=0,atol=2e-12)
    length=m.free_length
    target=length(m.controls(net,tx,z,0))
    def upper(q):
        return max(length(r0+q*d0),length(r1+q*d1))-target
    def lower(q):
        return length(r+q*d)-.5*length(r1-r0+q*(d1-d0))-target
    assert upper(0)<0 and lower(40)>0
    lo=brentq(upper,0,40)-1e-9
    hi=brentq(lower,0,40)+1e-9
    center=m.controls(net,tx,z,mid)
    movement=max(np.linalg.norm(rr+q*dd-center,axis=1).max() for rr,dd in ((r0,d0),(r1,d1)) for q in (lo,hi))
    return center,max(movement+.000001,(end-start)/2)

def ribbon(points):
    # Every point on every segment is contained in the two-triangle strip.
    n=len(points)
    verts=np.concatenate([points+[0,0,.0001],points-[0,0,.0001]])
    faces=np.array([(i,i+1,n+i) for i in range(n-1)]+[(i+1,n+i+1,n+i) for i in range(n-1)])
    return model(verts,faces)

def bounds(p):
    return np.array([p.min(axis=0),p.max(axis=0)])

def boxgap(a,b):
    return np.linalg.norm(np.maximum(0,np.maximum(a[0]-b[1],b[0]-a[1])))

def check(cache,steps):
    wires=new_leads()
    overlay=load(HERE/"overlay.json")
    installed=read_shapes(cache)
    for name in overlay["remove"]:
        del installed[name]
    for row in overlay["add"]:
        p=HERE/row["brep"]
        assert digest(p)==row["sha256"]
        installed[row["name"]]=cq.Shape.importBrep(str(p))
    # A broad-phase 3-D volume enclosing the entire moving W4 with > 2 mm allowance.
    domain=np.array([[0,-9,2],[43,34,24]])
    fixed={}
    old=WIRES.with_name("harness-r0005")
    sources={k:cache/(k+".brep") for k in installed}
    sources.update({r["name"]:old/r["brep"] for r in load(old/"installed.json")["add"]})
    sources.update({r["name"]:HERE/r["brep"] for r in overlay["add"]})
    tess=cache.parent/"r0013-mesh-025-010"
    tess.mkdir(exist_ok=True)
    installed["cellDrawing"]=maximum_drawing_pack()
    for key,shape in installed.items():
        if key.startswith(("wh","A3-J1-C")) or key in ("A3-J1-plug","A3-J1-TPA"):
            continue
        b=shape.BoundingBox()
        ab=np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])
        if boxgap(ab,domain)>2:continue
        identity=digest(sources[key]) if key!="cellDrawing" else "drawing-35p3-62p3-5p3-at-m10p4-m0p65-3p6"
        meshfile=tess/(identity+".npz")
        if meshfile.exists():
            with np.load(meshfile) as cached:
                vertices,faces=cached["vertices"],cached["faces"]
        else:
            vertices,faces=tri(shape)
            np.savez_compressed(meshfile,vertices=vertices,faces=faces)
        fixed[key]=(ab,model(vertices,faces))
    print("Prepared",len(fixed),"stationary meshes",flush=True)
    routes=load(WIRES/"routing.json")
    nets=list(wires.NET_PIN)
    worst_fixed=(math.inf,)
    worst_pair=(math.inf,)
    max_movement=0
    max_chord=0
    for i in range(steps):
        a,b=wires.STROKE*i/steps,wires.STROKE*(i+1)/steps
        moving={}
        for net in nets:
            x,_,z=routes[net]["tap_center_mm"]
            poles,movement=pole_motion(wires,net,x,z,a,b)
            max_movement=max(max_movement,movement)
            count=97
            degree=len(poles)-1
            chord=degree*(degree-1)*np.linalg.norm(np.diff(poles,n=2,axis=0),axis=1).max()/(8*(count-1)**2)
            max_chord=max(max_chord,chord)
            pts=wires.bernstein(degree,np.linspace(0,1,count))@poles
            barrel=np.array([pts[0,0],-5.35+(a+b)/2,10.36])
            pts=np.concatenate([[barrel],pts])
            assert np.all(pts.min(axis=0)>domain[0]+1) and np.all(pts.max(axis=0)<domain[1]-1)
            budget=wires.JACKET_OD/2+movement+chord+.000002
            assert budget<1, "widen broad phase or refine intervals"
            shape=ribbon(pts)
            ab=bounds(pts)
            moving[net]=(shape,budget)
            nearest=math.inf
            for bb,k in sorted((boxgap(ab,otherbox),k) for k,(otherbox,_) in fixed.items() if not k.startswith("tee-"+net+"-")):
                if bb>nearest+.001:break
                gap=meshgap(shape,fixed[k][1])
                nearest=min(nearest,gap)
                worst_fixed=min(worst_fixed,(gap-budget,net,k,a,b))
        for n,n2 in itertools.combinations(nets,2):
            m1,b1=moving[n];m2,b2=moving[n2]
            worst_pair=min(worst_pair,(meshgap(m1,m2)-b1-b2,n,n2,a,b))
    def result(w):
        return dict(lower_bound_mm=round(w[0]-.000005,5),pair=w[1:3],travel_interval_mm=w[3:])
    report={"intervals":steps,"stroke_mm":wires.STROKE,"actual_installed_revision":HERE.name,
        "form_sha256":digest(WIRES/"loop-forms.json"),"overlay_sha256":digest(HERE/"overlay.json"),
        "stationary_mesh_members":sorted(fixed),"jacket_od_mm":wires.JACKET_OD,
        "max_centerline_motion_from_midpoint_mm":round(max_movement,7),"max_chord_error_mm":round(max_chord,7),
        "flex_to_seated_mesh":result(worst_fixed),"flex_to_flex":result(worst_pair),
        "scope":"Nominal wire jacket bounded by a circular envelope around the exact variable-length-parameter guide. Static obstacles use CAD tessellations at 0.025 mm requested deflection. Supplier socket contacts/TPA, its housing, short stripped conductors, and each lead's own bonded tee are intentional motion interfaces and excluded. No physical dress, tolerance or fatigue allowance included."}
    save(HERE/"QA/interval-clearance.json",report)
    print(report["flex_to_seated_mesh"],report["flex_to_flex"],flush=True)
    if min(worst_pair[0],worst_fixed[0])<=0:
        raise SystemExit("The continuous nominal clearance bound has not passed.")

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cache",type=Path)
    cli.add_argument("--intervals",type=int,default=264)
    args=cli.parse_args()
    check(args.cache,args.intervals)
