"""Rev F top-edge power subassembly; units are millimetres, display toward +Z."""
from pathlib import Path
import base64
import json
import sys
import zlib
from functools import lru_cache
import cadquery as cq
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
INPUT=HERE.parent/"rev-E/scripts/inputs"
V=cq.Vector
X=-36.0
Z=12.5
def box(x,y,z,w,d,h):
    return cq.Solid.makeBox(w,d,h,V(x,y,z))
def rel(x,y,z,w,d,h):
    return box(X+x,y,Z+z,w,d,h)
def cyl(x,y,z,r,h,d=(0,0,1)):
    return cq.Solid.makeCylinder(r,h,V(x,y,z),V(*d))
def yc(x,y,z,r,h):
    return cyl(X+x,y,Z+z,r,h,(0,1,0))
def join(*shapes):
    result=shapes[0]
    for shape in shapes[1:]:
        result=result.fuse(shape)
    return result.clean()
def cut(shape,*tools):
    for tool in tools:shape=shape.cut(tool)
    return shape.clean()

def power_parts(housing):
    # The counterbore captures the cap. Inner vertical relief lets the actuator
    # pass during a straight drop-in of the switch board before main-board fit.
    opening=yc(0,25,0,3.00,12)
    counterbore=yc(0,25,0,4.15,8.55)
    plunger_path=rel(-2.05,29,0,4.10,4.04,17.0)
    frame=cut(housing,opening,counterbore,plunger_path)
    rails=[]
    for side in [-1,1]:
        lo,hi=sorted([side*4.40,side*6.75])
        rail=rel(lo,26.45,-5.65,hi-lo,6.35,10.8)
        rail=cut(rail,rel(-5.70,27.65,-5,11.40,1.28,15))
        rails.append(rail)
    boss=cyl(X+7.7,29.65,Z-3.0,2.5,8.15)
    boss=join(boss,rel(6.2,29.5,-3.0,3.0,3.3,8.15))
    boss=cut(boss,cyl(X+7.7,29.65,Z+.3,0.80,5.2),rel(-5.70,27.65,-5,11.40,1.28,15))
    frame=join(frame,*rails,boss)
    # Positive-Y is toward the fingertip. Print the flange flat, face upward.
    cap=join(yc(0,33,0,3.85,.54),yc(0,33.42,0,2.75,.90))
    cap=cq.Workplane(obj=cap).edges(">Y").fillet(.28).val()
    ring=cut(yc(0,34.02,0,1.65,.5),yc(0,33.99,0,1.21,.6),rel(-.53,33.97,.35,1.06,.70,1.60))
    cap=cut(cap,ring,rel(-.22,34.02,.46,.44,.5,1.52))
    # A crossbar on the rail tops closes the removable board slots.
    keeper=rel(-6.65,26.85,5.15,16.8,5.0,1.5)
    keeper=cq.Workplane(obj=keeper).edges("|Z").fillet(.65).val()
    keeper=cut(keeper,cyl(X+7.7,29.65,Z+5.0,1.1,2))
    # The removable keeper carries the two travel stops. This leaves a clear
    # path to fit the wider flange from inside before retaining the switch.
    for side in [-1,1]:
        lo,hi=sorted([side*3.29,side*4.32])
        keeper=join(keeper,rel(lo,30.25,-.82,hi-lo,1.55,6.30),
                    rel(lo,30.25,-.82,hi-lo,2.05,1.64))
    # M2x6 screw bound: conservative smooth major diameter and head envelope;
    # the nominal thread engagement intersects the printed pilot by design.
    screw=join(cyl(X+7.7,29.65,Z+.65,1,6),
              cyl(X+7.7,29.65,Z+6.65,2.0,1.6))
    pcb=rel(-5.5,27.65,-5,11,1,10)
    holes=[];tails=[]
    for dx in [-3.25,3.25]:
        for dz in [-2.25,2.25]:
            holes.append(yc(dx,27.5,dz,.55,1.3))
            tails.append(yc(dx,26.85,dz,.43,1.80))
    pcb=cut(pcb,*holes)
    # Approximate supplier case / actuator separately so the press path is
    # evaluated without treating intended actuator motion as a collision.
    body=rel(-3.05,28.65,-3.05,6.10,3.35,6.10)
    plunger=yc(0,32,0,1.75,.95)
    return frame,cap,keeper,pcb,body,plunger,cq.Compound.makeCompound(tails),screw

@lru_cache(maxsize=8192)
def bb(s):
    b=s.BoundingBox();return (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)
def near(a,b):
    return all(a[i]<b[i+1]-.00001 and b[i]<a[i+1]-.00001 for i in (0,2,4))
def stl(s,name,orient=None):
    if orient:s=s.rotate((0,0,0),orient[0],orient[1])
    b=bb(s);s=s.translate((-(b[0]+b[1])/2,-(b[2]+b[3])/2,-b[4]))
    path=HERE/"Print"/(name+".stl")
    cq.exporters.export(s,str(path),tolerance=.025,angularTolerance=.10)
    mesh=trimesh.load_mesh(str(path))
    assert mesh.is_volume and mesh.is_watertight and len(mesh.split())==1,name
def viewer(s,n):
    verts,faces=s.tessellate(.04,.12)
    def enc(v):return base64.b64encode(zlib.compress(v.tobytes(),9)).decode()
    return {"n":n,"p":enc(np.rint(np.asarray([p.toTuple() for p in verts])*100).astype("<i2")),
            "t":enc(np.asarray(faces,dtype="<u4"))}

if __name__=="__main__":
    import tempfile,shutil
    from importlib.util import spec_from_file_location,module_from_spec
    # Run the original Rev E generator with its cache in a scratch directory.
    with tempfile.TemporaryDirectory() as scratch:
        src=Path(scratch)
        shutil.copyfile(INPUT.parent/"geometry.py",src/"geometry.py")
        points=src/"inputs";points.mkdir()
        for name in ["Waveshare.stp","AS5600.step","Pocket.step"]:shutil.copyfile(INPUT/name,points/name)
        spec=spec_from_file_location("rev_e_source",src/"geometry.py")
        baseline=module_from_spec(spec);spec.loader.exec_module(baseline)
        A,D,E,H=baseline.A,baseline.D,baseline.E,baseline.H
    F,cap,keeper,pcb,body,plunger,leads,screw=power_parts(H)
    from rod_grip import add_mount,saddle,mount_parts
    F=add_mount(F)
    fixed=([("Main board "+str(i),s) for i,s in enumerate(A)]+
           [("Encoder "+str(i),s) for i,s in enumerate(E)]+
           [(baseline.labels[i],D[i]) for i in range(1,11)])
    mech={"Housing":F,"Key cap":cap,"Retainer":keeper,"Key PCB":pcb,
          "Switch case":body,"Switch plunger":plunger,"Trimmed terminals":leads,"Keeper screw":screw}
    checks={}
    def clearance(name,s,others):
        b=bb(s);hits=[]
        for k,o in others:
            if near(b,bb(o)):
                volume=s.intersect(o).Volume()
                if volume>.002:hits.append((k,round(volume,4)))
        checks[name]=hits
    clearance("Added housing vs seated registered parts",F.cut(H),fixed)
    lock=mount_parts()
    for n,s in lock.items():clearance(n+" vs registered parts",s,fixed)
    for n,s in list(mech.items())[1:]:clearance(n+" vs registered parts",s,fixed)
    for n,s in list(mech.items())[1:]:
        others=[(m,o) for m,o in mech.items() if m!=n and {m,n}!={"Housing","Keeper screw"}]
        clearance(n+" against new assembly",s,others)
    for stroke in np.linspace(0,.70,15):
        clearance("Cap stroke "+str(round(stroke,3)),cap.translate((0,-stroke,0)),
                  [(m,o) for m,o in mech.items() if m not in ["Key cap","Switch plunger"]])
    # Installed end of board insertion; mounting a key PCB precedes the main
    # board, cap already in place and screw and keeper still removed.
    key=cq.Compound.makeCompound([pcb,body,plunger,leads])
    for step in np.arange(0,23,.5):
        clearance("Key PCB drop "+str(step),key.translate((0,0,step)),[("Housing",F),("Cap",cap)])
        clearance("Cap loading drop "+str(step),cap.translate((0,-2.5,step)),[("Housing",F)])
        clearance("Retainer loading drop "+str(step),keeper.translate((0,0,step)),
                  [("Housing",F),("Cap",cap),("Key",key)])
    for dy in np.linspace(-2.5,0,11):
        clearance("Cap insertion "+str(dy),cap.translate((0,dy,0)),[("Housing",F)])
    switch_items=[("Added housing",F.cut(H)),*list(mech.items())[1:]]
    for i,s in enumerate(A):
        bounds=list(bb(s));bounds[5]+=16
        candidates=[(n,o) for n,o in switch_items if near(bounds,bb(o))]
        for dz in np.arange(0,16.1,.5) if candidates else []:
            clearance(f"Main board solid {i} closure {dz}",s.translate((0,0,dz)),candidates)
    hits={k:v for k,v in checks.items() if v}
    print("FAILURES",hits,flush=True)
    assert not hits,hits
    (HERE/"Print").mkdir(exist_ok=True)
    stl(F,"housing-top-power");stl(cap,"power-cap",((1,0,0),90));stl(keeper,"key-board-retainer",((1,0,0),180))
    ass=cq.Assembly(name="Rev_F_handheld_and_rod_grip")
    for n,s in mech.items():ass.add(s,name=n,color=cq.Color("#BF8756" if n=="Key cap" else "#85998F"))
    for n,s in [("Bezel",D[1]),("Rotor",D[2]),("Stem",D[3]),("Grip",D[4]),("Collar",D[5]),
                ("Reel hardware",cq.Compound.makeCompound(D[6:9])),("Cell",D[9]),("Speaker",D[10]),
                ("Waveshare",cq.Compound.makeCompound(A)),("AS5600",cq.Compound.makeCompound(E)),
                ("Removable rod grip",saddle()),*lock.items()]:ass.add(s,name=n)
    import gzip
    with tempfile.TemporaryDirectory() as temp:
        dest=Path(temp)/"assembly.step";ass.export(str(dest))
        with open(dest,"rb") as src,gzip.open(HERE/"Rev-F-top-power.step.gz","wb") as fp:shutil.copyfileobj(src,fp)
    (HERE/"checks.json").write_text(json.dumps({"threshold_mm3":.002,"static_and_sampled_checks":checks,
       "cap_rest_center":[X,34.32,Z],"cap_max_travel_mm":.7,"switch_to_cap_nominal_gap_mm":.05},indent=2)+"\n")
    if len(sys.argv)>1:
        Path(sys.argv[1]).write_text(json.dumps([viewer(F,"Revised housing"),viewer(cap,"Top power cap")],separators=(",",":")))
