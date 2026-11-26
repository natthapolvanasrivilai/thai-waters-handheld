"""Check final STL datums against the installed ledger and independent sensor artwork."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
MECH = HERE.parent
GLASS = "A1-display"
SENSOR = "A2-sensor"
# Independently selected installed XY/XYZ points on the flat face of each landmark.
# Transformation to the print ray is applied after selecting the reference.
PROBES = {
    GLASS: {"USB shell": (-36.6,0,17.7496), "J7": (-25.25,23.3,17.6),
            "J8": (0,22.9,15.9), "J9": (-.69,-21.8,17.6),
            "SW reset": (-16.50,-25.1,19.20)},
    SENSOR: {"AS5600 package": (42.55,0,14.8), "negative-Y socket": (44.01,-10,14.8),
             "positive-Y socket": (44.01,10,14.8)},
    "A3-haptic": {"J1 housing": (20.96,-10.0,14.36), "U1": (20.95,-3,7.295)},
    "A4-integration": {"tall package": (31.5,-3.7,16.505)},
    "A5-power": {"R0006 tall package": (25,7,15.455)},
    "KEY-switch": {"unpressed plunger": (-36,32.95,12.5)},
    "USB-PCB1": {"indicator": (-42.352,0,13.1)},
    "USB-PCB2": {"resistor": (-21,18,18.65)},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section_solid(mesh):
    return mf.Manifold(mf.Mesh64(np.ascontiguousarray(mesh.vertices),
                                  np.ascontiguousarray(mesh.faces,np.uint64)))


def holes(section):
    result=[]
    for ring in section.to_polygons():
        xy=np.array(ring)
        # The outer loop has positive orientation. Interior contours are clockwise.
        area=np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))/2
        if area<0:
            a,b=xy.min(0),xy.max(0)
            result.append(((a+b)/2,b-a))
    return result


def outer_z(mesh,xy):
    triangles=mesh.triangles
    u=triangles[:,1]-triangles[:,0]
    v=triangles[:,2]-triangles[:,0]
    d=xy-triangles[:,0,:2]
    det=u[:,0]*v[:,1]-u[:,1]*v[:,0]
    use=abs(det)>1e-8
    a=(d[use,0]*v[use,1]-d[use,1]*v[use,0])/det[use]
    b=(u[use,0]*d[use,1]-u[use,1]*d[use,0])/det[use]
    inside=(a>=-1e-6)&(b>=-1e-6)&(a+b<=1.000001)
    z=triangles[use,0,2]+a*u[use,2]+b*v[use,2]
    return max(z[inside])


def measure_bores(mesh,depth,expected,diameter):
    measured=holes(section_solid(mesh).slice(depth))
    found=[]
    for center in expected:
        actual,size=min(measured,key=lambda hole:np.linalg.norm(hole[0]-center))
        center_error=np.linalg.norm(actual-center)
        diameter_error=np.max(abs(size-diameter))
        if max(center_error,diameter_error)>.01:
            raise ValueError(f"Bore mismatch {center} {actual} {size}")
        found.append(dict(center_xy_mm=np.round(actual,5).tolist(),xy_diameter_mm=np.round(size,5).tolist()))
    return found


def sensor_artwork(mesh):
    path=MECH/"rev-E/scripts/inputs/Adafruit-AS5600.brd"
    doc=ET.parse(path)
    package="MOUNTINGHOLE_2.5_PLATED"
    elements=doc.findall(f".//board/elements/element[@package='{package}']")
    locations=[np.array([float(e.get(k)) for k in ("x","y")]) for e in elements]
    diameter=float(doc.find(f".//package[@name='{package}']/pad").get("drill"))
    edges=doc.findall(".//board/plain/wire[@layer='20']")
    ends=np.array([[float(e.get("x1")),float(e.get("y1"))] for e in edges])
    size=np.ptp(ends,axis=0)
    arcs=[e for e in edges if e.get("curve")]
    radii=[abs(float(e.get("x2"))-float(e.get("x1"))) for e in arcs]
    assert len(arcs)==4 and all(e.get("curve")=="90" for e in arcs)
    assert abs(max(radii)-min(radii))<.00001
    r=radii[0]
    target=mf.CrossSection.square(size-2*r).offset(r,mf.JoinType.Round,2,1024).translate((r,r))
    contours=section_solid(mesh).slice(.75).to_polygons()
    outline=max([mf.CrossSection([loop],mf.FillRule.EvenOdd) for loop in contours],key=lambda ring:ring.area())
    area_delta=(target-outline).area()+(outline-target).area()
    if area_delta>.035:
        raise ValueError(f"Sensor outline differs by {area_delta} square millimetres")
    return dict(file=str(path.relative_to(MECH)),sha256=sha(path),artwork_outline_mm=size.tolist(),corner_radius_mm=r,
                four_mounts=measure_bores(mesh,.75,locations,diameter),pitch_mm=np.ptp(locations,axis=0).tolist(),
                outer_outline_symmetric_difference_mm2=round(area_delta,7),
                six_wire_holes=measure_bores(mesh,.75,[(x,2.54) for x in [6.35,8.89,11.43,13.97,16.51,19.05]],1.0))


def main():
    geometry=json.loads((HERE/"geometry.json").read_bytes())
    source=MECH/"TW-A-0001-R0013/installed-step.json"
    reference=json.loads(source.read_bytes())
    assert geometry["source_step_sha256"]==reference["step_sha256"]
    records={}
    for name,row in geometry["parts"].items():
        path=HERE/row["file"]
        assert sha(path)==row["sha256"]
        mesh=trimesh.load_mesh(path)
        pose=np.array(row["print_to_installed_3x4"])
        installed=mesh.copy()
        installed.apply_transform(np.vstack([pose,[0,0,0,1]]))
        bounds=np.array([reference["components"][node]["bounds_mm"] for node in row["source_nodes"]])
        ref=np.array([bounds[:,::2].min(0),bounds[:,1::2].max(0)])
        # The haptic header's solder tails are intentionally truncated at the underside.
        if name=="A3-haptic":
            ref[0,2]=reference["components"]["drvBoard"]["bounds_mm"][4]
        error=np.max(abs(ref-installed.bounds))
        if error>.006:
            raise ValueError(f"{name} extent discrepancy {error} mm")
        probes={}
        for feature,point in PROBES[name].items():
            local=(np.array(point)-pose[:,3])@pose[:,:3]
            z=outer_z(mesh,local[:2])
            if abs(local[2]-z)>.012:
                raise ValueError(f"{name} {feature} at {local}: measured {z}")
            probes[feature]=dict(installed_xyz_mm=list(point),actual_print_z_mm=round(float(z),5),
                                  error_mm=round(float(abs(local[2]-z)),6))
        record=dict(source_reference_min_max_mm=np.round(ref,5).tolist(),
                    stl_registered_min_max_mm=np.round(installed.bounds,5).tolist(),
                    maximum_bound_difference_mm=round(float(error),6),feature_height_probes=probes)
        if name==SENSOR:
            record["sensor_artwork"]=sensor_artwork(mesh)
        if name==GLASS:
            coords=[[(x+46.22),(30.50-y)] for x in [-36,36] for y in [-24.25,24.25]]
            record["four_unthreaded_insert_guides"]=measure_bores(mesh,9.50,coords,2.)
        if name=="A3-haptic":
            record["motor_wire_holes"]=measure_bores(mesh,.75,[(6.4,18.1),(11.9,18.1)],1.)
        records[name]=record
    out=dict(geometry_sha256=sha(HERE/"geometry.json"),installed_ledger_sha256=sha(source),unit="mm",parts=records)
    (HERE/"geometry-checks.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
