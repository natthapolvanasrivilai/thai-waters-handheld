"""Build a Rev E scale detent test coupon. CAD coordinates in millimetres."""
from pathlib import Path
import json

import cadquery as cq
import numpy as np
import trimesh

OUTPUT = Path(__file__).resolve().parent
COUNT = 12
CREST = 12.75
VALLEY = 12.15
THROW = 7.80
AXLE = 4.55
BORE = 4.85
TIP_R = 1.00
TIP_Y = 12.77
WHEEL_Z = 2.70
WHEEL_H = 4.00


def disk(x, y, z, radius, height):
    return cq.Workplane("XY").center(x, y).circle(radius).extrude(height).translate((0, 0, z))


def block(x0, x1, y0, y1, z0, height):
    return cq.Workplane("XY").box(x1-x0, y1-y0, height, centered=False).translate((x0, y0, z0))


def cam_radius(a):
    half = (CREST - VALLEY) / 2
    return CREST - half - half * np.cos(COUNT * (a - np.pi / 2))


def wheel():
    theta = np.linspace(0, 2*np.pi, 360, endpoint=False)
    radius = cam_radius(theta)
    outline = list(zip(radius*np.cos(theta), radius*np.sin(theta)))
    rim = cq.Workplane("XY").polyline(outline).close().extrude(WHEEL_H)
    handle = disk(THROW, 0, WHEEL_H-.2, 2.75, 8.2).edges(">Z").fillet(.8)
    return rim.union(handle).cut(disk(0, 0, -.1, BORE, WHEEL_H+.2))


def frame(leaf_width):
    # All spring material starts on the print bed. The open quadrant under
    # the leaf has no tray to fuse to it. The central seat sets the cam height.
    spine = block(-20, -16, -6, 16, 0, 6.5).edges("|Z").fillet(.7)
    arm = block(-18, .1, -4.5, 4.5, 0, 2.3)
    hub = disk(0, 0, 0, 6.5, WHEEL_Z)
    post = disk(0, 0, WHEEL_Z-.1, AXLE, WHEEL_H+1.0).edges(">Z").chamfer(.35)
    leaf = block(-17.5, .2, 13.05, 13.05+leaf_width, 0, 6.5)
    follower = disk(0, TIP_Y, 0, TIP_R, 6.5)
    root = disk(-16.7, 13.35+leaf_width/2, 0, leaf_width+1, 6.5)
    return spine.union(arm).union(hub).union(post).union(leaf).union(follower).union(root)


def export_print(part, name):
    path = OUTPUT / (name + ".stl")
    assert part.val().isValid() and len(part.val().Solids()) == 1
    cq.exporters.export(part, str(path), tolerance=.035, angularTolerance=.1)
    mesh = trimesh.load_mesh(str(path))
    assert mesh.is_watertight and mesh.is_volume and len(mesh.split()) == 1
    return [round(float(n), 3) for n in mesh.extents]


def measure():
    # Maximum y of cam boundary enlarged by follower tip radius at x=0.
    # This gives radial follower displacement for a laterally centered wheel.
    radians = np.linspace(0, 2*np.pi, 7200, endpoint=False)
    radius = cam_radius(radians)
    travel = []
    for angle in np.arange(0, 360, .5):
        a = radians + np.deg2rad(angle)
        x, y = radius*np.cos(a), radius*np.sin(a)
        contact = (np.abs(x)<=TIP_R) & (y>0)
        center = np.max(y[contact]+np.sqrt(TIP_R**2-x[contact]**2))
        travel.append(float(center)-TIP_Y)
    values = np.array(travel)
    peaks = np.flatnonzero((values>np.roll(values, 1)) & (values>np.roll(values, -1)))
    assert len(peaks)==COUNT
    assert all(np.diff(np.r_[peaks,peaks[0]+len(values)])==60)
    assert min(travel)>BORE-AXLE
    assert max(travel)<1.05
    return {"sampled_increment_deg":.5, "detents_per_revolution":len(peaks),
            "pitch_deg":360/COUNT, "cam_radius_range_mm":[VALLEY, CREST],
            "axis_to_grip_center_mm":THROW, "nominal_radial_bearing_play_mm":round(BORE-AXLE, 2),
            "required_radial_follower_deflection_at_centered_axle_mm":
                [round(min(travel),3), round(max(travel),3)]}


if __name__=="__main__":
    rotor = wheel()
    dims = {"wheel":export_print(rotor, "wheel")}
    for key, width in (("light",1.2),("firm",1.6)):
        fixture=frame(width)
        dims[key]=export_print(fixture, "frame-"+key)
        # Rigid solids intentionally overlap at the compliant tip only. A
        # radius envelope covering every cam angle checks all other solids.
        rigid = fixture.cut(disk(0,TIP_Y,-.1,TIP_R+.01,6.8))
        annulus = disk(0,0,WHEEL_Z+.001,CREST,WHEEL_H-.002).cut(disk(0,0,WHEEL_Z,BORE,WHEEL_H))
        assert rigid.intersect(annulus).val().Volume()<.001
        if key=="light":
            exploded=cq.Assembly(name="DetentBenchCoupon")
            exploded.add(fixture,name="LightFrame",color=cq.Color(.38,.53,.45))
            exploded.add(rotor.translate((0,0,12)),name="Wheel",color=cq.Color(.82,.56,.33))
            exploded.export(str(OUTPUT/"exploded-light.step"))
    data=measure()
    data["watertight_print_extents_xyz_mm"]=dims
    data["wheel_to_noncompliant_frame_overlap_mm3_limit"]=.001
    (OUTPUT/"checks.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data))
