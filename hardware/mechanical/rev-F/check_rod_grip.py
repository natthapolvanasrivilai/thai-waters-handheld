"""Rigid mount verification. Inputs are the bare Rev F power housing and cap BREPs.

Run python check_rod_grip.py BARE_F_HOUSING.brep CAP.brep after rod_grip.py.
"""
import json
import sys
import cadquery as cq
import trimesh
from rod_grip import ROOT, X, Y, RETRACT, add_mount, saddle, mount_parts, cyl

def box(x,y,z,w,d,h):return cq.Solid.makeBox(w,d,h,cq.Vector(x,y,z))
def overlap(a,b):return max(0.,a.intersect(b).Volume())
def record(d,key,a,b):
    size=overlap(a,b)
    assert size<.002,(key,size)
    d[key]={"volume_mm3":round(size,5),"gap_mm":round(a.distance(b),4)}

bare=cq.Shape.importBrep(sys.argv[1])
power=cq.Shape.importBrep(sys.argv[2])
case=add_mount(bare); handle=saddle(); parts=mount_parts()
old=cq.importers.importStep(str(ROOT.parent/"rev-E/scripts/inputs/Pocket.step")).val().Solids()
screw=parts["Grip lock screw"]; keeper=parts["Grip screw keeper"]
nut=parts["Receiver nut"]; nutcap=parts["Receiver nut keeper"]
assert case.isValid() and handle.isValid() and len(handle.Solids())==1
result={"units":"mm, mm3","single_watertight_STLs":[],"fit":{},"motion":{}}
for filename in ["rod-grip.stl","grip-screw-keeper.stl","receiver-nut-keeper.stl"]:
    mesh=trimesh.load_mesh(str(ROOT/"Print"/filename))
    assert mesh.is_watertight and mesh.is_volume and len(mesh.split())==1,filename
    result["single_watertight_STLs"].append(filename)
for name,other in {"receiver":case,"bezel":old[1],"PWR key":power,
        "active LCD keep-out":box(-38.4,-26.1,28.5,76.8,52.2,12),
        "USB cable":box(-70,-8,15.5,26,16,10),"lower service tools":box(-30,-49,17.5,26,21,6),
        "switch finger approach":box(-42,33,6.5,12,25,12),
        "fold and rotary reel motion envelope":box(39,-20,-5,55,40,41)}.items():
    record(result["fit"],"grip to "+name,handle,other)
static=cq.Compound.makeCompound([case,nut,nutcap])
for name,other in [("screw to case",case),("screw to steel nut thread minimum cylinder",nut),
                   ("screw to grip",handle),("screw to grip keeper",keeper),
                   ("screw to nut keeper",nutcap)]:
    record(result["fit"],name,screw,other)
for name,component in [("nut",nut),("inner keeper",nutcap),("handle keeper",keeper)]:
    record(result["fit"],name+" to molded pocket",component,handle if name=="handle keeper" else case)

# Exact hard-body checks of the material ADDED to the case, including the local
# nut boss, against both the fixed optional haptic envelopes and original cell.
additional=case.cut(bare)
for name,other in {"cell":old[9],"speaker":old[10],
        "haptic driver allowance":box(10.10,-18.90,3,17.8,25.8,4.6),
        "motor allowance":cq.Solid.makeCylinder(5.5,4,cq.Vector(19,19,3))}.items():
    record(result["fit"],"new housing material to "+name,additional,other)
floor=box(X-11,-16,.80,22,12,1.70)
assert floor.cut(case).Volume()<.002
unlocked=screw.translate((0,0,-RETRACT))
for dz in [i*RETRACT/20 for i in range(21)]:
    moved=screw.translate((0,0,-dz))
    for against in [case,handle,keeper,nutcap]:
        assert overlap(moved,against)<.002,("unlock stroke",dz)
moving=cq.Compound.makeCompound([handle,keeper,unlocked])
for dy in range(-43,1):
    assert overlap(moving.translate((0,dy,0)),static)<.002,("slide path",dy)
result["motion"]={"unlock_stroke_mm":RETRACT,"unlock_samples":21,"slide_stroke_mm":43,
                  "slide_samples":44,"max_intersection_tolerance_mm3":.002}
# A single longitudinal pull or vertical lift must interfere with a solid stop.
locked_shank=screw.translate((0,-1.,0))
pull=overlap(locked_shank,case)
lift=overlap(handle.translate((0,0,-1.2)),case)
stop=overlap(handle.translate((0,.5,0)),case)
keeper_capture=overlap(unlocked.translate((0,0,-.75)),keeper)
assert min(pull,lift,stop,keeper_capture)>.02,(pull,lift,stop,keeper_capture)
result["positive_retention_mm3"]={"locked_screw_after_1mm_backslide":round(pull,3),
    "undercut_rails_after_1_2mm_rear_lift":round(lift,3),"blind_stop_after_0_5mm_overshoot":round(stop,3),
    "keeper_after_extra_0_75mm_retraction":round(keeper_capture,3)}
# Constrain the handle freely on a seated plane, then test realistic lateral
# location offsets. Screw shank remains in its bore at ±0.18 mm (each side).
for dx in (-.18,.18):
    translated=cq.Compound.makeCompound([handle,keeper,screw]).translate((dx,-.10,0))
    record(result["fit"],f"mating shift x={dx},y=-0.10",translated,case)
result["geometry"]={"key_engagement":35,"head_width":24.98,"neck_width":19.04,
    "nominal_neck_side_gap":.38,"nominal_flank_horizontal_gap":.378,
    "nominal_flank_normal_gap":.295,"running_full_lateral_play_nominal":.756,
    "rear_floor_under_channel":1.70,"rail_roof_gap":.29,"detached_shoe_height":3.2,
    "nominal_nut_thread_engagement":2.4,"nominal_locked_tip_past_nut":.35,
    "screw_tip_withdrawn_z":-.40,"screw_tip_locked_z":4.90}
result["volume_mm3"]={name:round(obj.Volume(),2) for name,obj in {"grip":handle,**parts}.items()}
for state,dy,dz in [("seated",0.,0.),("removal",-49.,-RETRACT)]:
    assembly=cq.Assembly(name="Rev_F_rod_handle_"+state)
    fixed={"Receiver housing":case,"Bezel":old[1],"PWR":power,"Nut":nut,"Nut keeper":nutcap}
    for i,n in enumerate(["Rotor","Reel stem","Reel knob","Collar","Hinge","Retainer"],2):fixed[n]=old[i]
    for n,s in fixed.items():assembly.add(s,name=n,color=cq.Color(.49,.59,.53))
    for n,s,offset in [("Rod handle",handle,0),("Captive screw",screw,dz),("Retaining cap",keeper,0)]:
        assembly.add(s.translate((0,dy,offset)),name=n,color=cq.Color(.27,.36,.30))
    assembly.export(str(ROOT/"CAD"/("rod-grip-"+state+".step")))
(ROOT/"rod-grip-checks.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
