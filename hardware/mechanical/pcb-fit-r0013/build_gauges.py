"""Build millimetre fit gauges from the digest-checked, installed R0013 STEP.

Usage: python build_gauges.py /path/to/roundtrip.step [--out DIRECTORY]
Requires CadQuery 2.8, manifold3d, NumPy and trimesh.
"""
import argparse
import hashlib
import itertools
import json
import math
import tempfile
from pathlib import Path

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
C = mf.CrossSection
M = mf.Manifold
# Local X, Y and Z expressed as signed installed axes, then installed origin.
POSE = {
    "A1-display": ((1,-2,-3),(-46.22,30.50,28.50)),
    "A2-sensor": ((2,3,1),(39.48,-12.70,5.91)),
    "A3-haptic": ((1,2,3),(10.80,-16.80,4.60)),
    "A4-integration": ((1,-2,-3),(13,1,18.535)),
    "A5-power": ((1,-2,-3),(13,19,17.84)),
    "KEY-switch": ((1,-3,2),(-41.50,27.65,17.50)),
    "USB-PCB1": ((2,-3,-1),(-41.50,-2.40,14.70)),
    "USB-PCB2": ((1,2,3),(-22.60,17.00,17.60)),
}
NOTES = {
    "A1-display": "R6 glass seated face; flush optical window; LCD, backing and PCB outline; four smooth blind screw guides, three button projections, J7/J8/J9, USB-C shell and separate component-height lands. Solid connector bodies and filled internal/underside spaces. Small passives, flex detail, contacts and insert threads omitted.",
    "A2-sensor": "Four nominal locating holes and six wiring holes, rounded board, central IC, opposite STEMMA QT sockets and individual package lands. Socket openings, leads and sub-nozzle vias omitted. Align the wiring-hole row toward the case floor, components and IC facing toward reel magnet and carrier lands.",
    "A3-haptic": "R0002 substrate outline and two motor holes; J1 represented by project-authored outer molded-body bounding block to its maximum height with support to the board. No CviLux mesh, mating cavity, plug, lock, contacts, or projecting pin tails. Native installed pins reach 0.4675 mm below the PCB back.",
    "A4-integration": "Soldered component bodies are individual height blocks. Back copper is flattened to its maximum outward face. No mounting holes; bonded standoffs are separate. Vias, wires and solder omitted.",
    "A5-power": "R0006 populated layout with individual component-height blocks. Back copper flattened to its maximum outward face. Available 0.70 mm wire holes preserved. Bonded standoffs are separate. Wires, solder and sub-nozzle vias omitted.",
    "KEY-switch": "PCB, switch housing with terminal-side ears and fixed round plunger at its unpressed height. No movable contact or projecting rear leads. Four trimmed terminals extend 0.8 mm below the real PCB; check that space separately.",
    "USB-PCB1": "Separate indicator PCB with solid LED outline and installed height. No wires, solder, or optical behavior.",
    "USB-PCB2": "Separate series resistor PCB with its solid resistor outline and installed height. No wires, adhesive, or solder.",
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest() if hasattr(hashlib,"file_digest") else hashlib.sha256(stream.read()).hexdigest()


def rounded(values):
    return np.round(values,5).tolist()


def bounds(shape):
    b=shape.BoundingBox()
    return np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])


def transform(axes,origin):
    rotation=np.zeros((3,3))
    for i,axis in enumerate(axes):
        rotation[abs(axis)-1,i]=np.sign(axis)
    return np.column_stack((rotation,origin))


def mesh_solid(shape):
    vertices,triangles=shape.tessellate(.01,.10)
    mesh=trimesh.Trimesh([v.toTuple() for v in vertices],triangles,process=True)
    return M(mf.Mesh(np.ascontiguousarray(mesh.vertices,np.float32),np.ascontiguousarray(mesh.faces,np.uint32)))


def rect(lo,hi):
    lo,hi=np.array(lo),np.array(hi)
    return M.cube(hi-lo).translate(lo)


def disc(x,y,z,diameter,h):
    return M.cylinder(h,diameter/2,diameter/2,96).translate((x,y,z))


def exterior(section):
    # Largest positive contour of a horizontal STEP section. All gauges represent
    # the carrier outline independently of its sub-nozzle vias.
    loops=section.to_polygons()
    polygons=[C([ring],mf.FillRule.EvenOdd) for ring in loops]
    return max(polygons,key=lambda p:p.area())


class Build:
    def __init__(self,name,source):
        self.name=name
        self.source=source
        self.pose=transform(*POSE[name])
        self.axes=self.pose[:,:3]
        self.origin=self.pose[:,3]
        self.add=[]
        self.cut=[]
        self.nodes=set()
        self.features={}
        self.bores=[]

    def node(self,key):
        self.nodes.add(key)
        return self.source[key]

    def local_bounds(self,shape):
        a,b=bounds(shape)
        points=(np.array(list(itertools.product(*zip(a,b))))-self.origin) @ self.axes
        return np.array([points.min(0),points.max(0)])

    def local_manifold(self,shape):
        return mesh_solid(shape).transform(np.column_stack((self.axes.T,-self.axes.T@self.origin)))

    def body_block(self,shape,base,label=None):
        lo,hi=np.round(self.local_bounds(shape),4)
        if hi[2] <= base+.02:
            return
        lo[2]=base
        self.add.append(rect(lo,hi))
        if label:
            self.features[label]=rounded([lo,hi])

    def plate(self,shape,bottom,top,hole_min=.60):
        s=self.local_manifold(shape)
        local=self.local_bounds(shape)
        section=s.slice(np.mean(local[:,2]))
        profile=exterior(section)
        board=profile.extrude(top-bottom).translate((0,0,bottom))
        self.add.append(board)
        self.features["substrate"]=rounded([[*local[0,:2],bottom],[*local[1,:2],top]])
        for loop in section.to_polygons():
            ring=C([loop],mf.FillRule.EvenOdd)
            if ring.area() >= profile.area()-.00001:
                continue
            pts=np.array(loop)
            d=pts.max(0)-pts.min(0)
            if min(d)<hole_min-.01 or abs(d[0]-d[1])>.015:
                continue
            center=(pts.max(0)+pts.min(0))/2
            self.bore(center,bottom,top,float(np.mean(d)))

    def bore(self,center,lower,upper,diameter):
        self.cut.append(disc(*center,lower-.001,diameter,upper-lower+.002))
        self.bores.append(dict(center_print_xy_mm=rounded(center),diameter_mm=round(diameter,3),
                               depth_span_print_z_mm=rounded([lower,upper])))

    def stepped_body(self,shape,base,levels,label):
        # Use a few measured slabs. Fill only the footprint of each slab back to
        # the substrate, keeping a continuous print underneath its outer landmark.
        s=self.local_manifold(shape)
        lo,hi=self.local_bounds(shape)
        if s.status()!=mf.Error.NoError:
            self.body_block(shape,base,label)
            return
        for z0,z1 in zip(levels,levels[1:]):
            if z1<=base+.001:
                continue
            segment=s.trim_by_plane((0,0,1),z0-.0005).trim_by_plane((0,0,-1),-z1-.0005)
            if segment.is_empty():
                continue
            # Project each height band to a planar mechanical silhouette, filling
            # internal cavities. This is a stepped envelope, with no mated internals.
            projected=segment.project()
            for p in projected.decompose():
                if p.area()>.15:
                    if self.name == "A1-display":
                        # Collapse same-height contacts to millimetre-scale lands.
                        # Avoid coincident vendor tessellation edges on the STL.
                        pts=np.concatenate(p.to_polygons())
                        low,high=np.round([pts.min(0),pts.max(0)],3)
                        if min(high-low) >= .40:
                            self.add.append(rect([*low,base],[*high,z1]))
                    else:
                        self.add.append(exterior(p).extrude(z1-base).translate((0,0,base)))
        self.features[label]=rounded([lo,hi])

    def display(self):
        def layer(key,section_z,bottom,top):
            shape=self.node(key)
            s=self.local_manifold(shape)
            profile=exterior(s.slice(section_z))
            self.add.append(profile.extrude(top-bottom).translate((0,0,bottom)))
        # The manufacturer's glass drawing specifies R6. Fill the optical recess
        # for a broad first-layer datum at the nominal highest glass plane.
        glass=C.square((92.44-12,61-12)).translate((6,6)).offset(6,mf.JoinType.Round,2,144)
        self.add.append(glass.extrude(1.10))
        layer("A1-touch",2,1.10,3.40)
        layer("A1-backing",4.60,3.40,5.90)
        self.plate(self.node("A1-carrier"),5.90,7.50,3.1)
        for boss in self.node("A1-mounts").Solids():
            lo,hi=self.local_bounds(boss)
            xy=(lo+hi)[:2]/2
            self.add.append(disc(*xy,7.50,4,4))
            self.bore(xy,6.0,11.50,2.0)
        for key in ("A1-J7","A1-J8","A1-J9","A1-k3","A1-reset","A1-boot"):
            shape=self.node(key)
            lo,hi=self.local_bounds(shape)
            levels=sorted(set([7.5,round((7.5+hi[2])/2,3),round(hi[2],4)]))
            self.stepped_body(shape,7.48,levels,key)
        # USB shell, capsule-section across the short axis. The outboard face is
        # closed to make a mechanical bezel witness without fragile socket walls.
        shape=self.node("A1-usb")
        self.stepped_body(shape,7.45,[7.45,8.0,8.5,9.2,9.8,10.30,10.60,10.7504],"USB-C")
        for idx,shape in enumerate(sorted(self.node("A1-population").Solids(),key=lambda s:-s.Volume())):
            lo,hi=self.local_bounds(shape)
            if shape.Volume()<.30 or min((hi-lo)[:2])<.40:
                continue
            if idx<6:
                top=round(hi[2],4)
                self.stepped_body(shape,7.48,np.linspace(7.48,top,1+max(1,math.ceil((top-7.48)/.7))),f"population-{idx+1}")
            else:
                self.body_block(shape,7.48)

    def sensor(self):
        self.plate(self.node("A2-pcb"),0,1.57,.80)
        for i,socket in enumerate(self.node("A2-sockets").Solids()):
            self.stepped_body(socket,1.56,[1.56,1.88,4.53],f"socket-{i+1}")
        self.body_block(self.node("A2-chip"),1.56,"AS5600-body")
        for part in self.node("A2-population").Solids():
            if part.Volume()>.25:
                self.body_block(part,1.56)

    def haptic(self):
        self.plate(self.node("drvBoard"),0,1.51,.85)
        header=max(self.node("A3-J1-header").Solids(),key=lambda s:s.Volume())
        self.body_block(header,1.50,"J1 outer molded-body envelope")
        for s in self.node("drvParts").Solids():
            if s.Volume()>.5:
                self.body_block(s,1.50)

    def bonded(self):
        key=self.name
        solids=sorted(self.node(key).Solids(),key=lambda s:-s.Volume())
        top=round(self.local_bounds(solids[0])[1,2],4)
        self.plate(solids[0],0,top,.60)
        for s in solids[1:]:
            lo,hi=self.local_bounds(s)
            if hi[2]>top+.20 and min((hi-lo)[:2])>.39:
                self.body_block(s,top-.01)

    def key_switch(self):
        self.plate(self.node("Key PCB"),0,1.00,1.1)
        case=self.node("Switch case")
        self.stepped_body(case,.99,[.99,1.45,2.5,4.35],"switch housing")
        plunger=max(self.node("Switch plunger").Solids(),key=lambda s:s.Volume())
        self.add.append(disc(5.5,5,4.34,3.5,.96))
        self.features["plunger"]=rounded(self.local_bounds(plunger))
        rim=min(self.node("Switch plunger").Solids(),key=lambda s:s.Volume())
        self.stepped_body(rim,4.34,[4.34,4.90],"upper rim lands")

    def indicator(self):
        self.plate(self.node(self.name),0,.60,1.0)
        key="USB-D1" if self.name=="USB-PCB1" else "USB-R1"
        self.body_block(self.node(key),.59,key)

    def run(self):
        if self.name=="A1-display": self.display()
        elif self.name=="A2-sensor": self.sensor()
        elif self.name=="A3-haptic": self.haptic()
        elif self.name in {"A4-integration","A5-power"}: self.bonded()
        elif self.name=="KEY-switch": self.key_switch()
        else: self.indicator()
        gauge=M.batch_boolean(self.add,mf.OpType.Add)
        if self.cut:
            gauge=gauge-M.batch_boolean(self.cut,mf.OpType.Add)
        gauge=gauge.simplify(.00001)
        assert gauge.status()==mf.Error.NoError and len(gauge.decompose())==1,(self.name,gauge.status(),len(gauge.decompose()))
        return gauge


def write_part(build,out):
    gauge=build.run()
    mesh=gauge.to_mesh()
    target=out/"meshes"/(build.name+".stl")
    raw=trimesh.Trimesh(mesh.vert_properties[:,:3],mesh.tri_verts,process=False)
    raw.export(target)
    read=trimesh.load_mesh(target,process=True)
    assert read.is_watertight and read.is_winding_consistent and len(read.split())==1,build.name
    assert np.max(abs(read.bounds[0]))<.025,(build.name,read.bounds)
    for hole in build.bores:
        z0,z1=hole["depth_span_print_z_mm"]
        # Real pin/wire holes have a circular empty section in the bare substrate.
        # A3 header pins occupy five holes above the substrate only.
        xy=hole["center_print_xy_mm"]
        z=(z0+z1)/2
        section=gauge.slice(z)
        check=C.circle(hole["diameter_mm"]/2-.015,96).translate(xy)
        assert (section^check).area()<.00001,(build.name,hole)
    installed=read.copy()
    installed.apply_transform(np.vstack((build.pose,[0,0,0,1])))
    record=dict(file="meshes/"+target.name,sha256=digest(target),quantity=1,
        source_nodes=sorted(build.nodes),print_to_installed_3x4=rounded(build.pose),
        print_min_max_mm=rounded(read.bounds),installed_min_max_mm=rounded(installed.bounds),
        print_xyz_mm=rounded(read.extents),first_layer_datum_area_mm2=round(gauge.slice(.01).area(),3),
        rigid_connected_components=1,watertight=True,triangles=len(read.faces),mesh_volume_mm3=round(read.volume,4),
        bore_geometry=build.bores,feature_bounds_print_min_max_mm=build.features,scope=NOTES[build.name])
    print(build.name,rounded(read.extents),flush=True)
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("step",type=Path)
    p.add_argument("--out",type=Path,default=HERE)
    args=p.parse_args()
    ledger=json.loads((HERE.parent/"TW-A-0001-R0013/installed-step.json").read_text())
    assert digest(args.step)==ledger["step_sha256"],"Wrong master STEP"
    assembly=cq.Assembly.load(str(args.step))
    source={node.name:node.obj.moved(node.loc) for node in assembly.children}
    (args.out/"meshes").mkdir(parents=True,exist_ok=True)
    # Normalize each located STEP child to an independent BRep before meshing.
    # Serializing through OpenCascade removes shared triangulation state and
    # preserves the same primitive order as the original fit-gauge build.
    used={"drvBoard","drvParts","Key PCB","Switch case","Switch plunger","USB-D1","USB-R1",
          "USB-PCB1","USB-PCB2","A3-J1-header","A4-integration","A5-power"}
    used.update(key for key in source if key.startswith(("A1-","A2-")))
    with tempfile.TemporaryDirectory() as folder:
        normalized={}
        for key in sorted(used):
            path=Path(folder)/(key+".brep")
            source[key].exportBrep(str(path))
            normalized[key]=cq.Shape.importBrep(str(path))
        records={name:write_part(Build(name,normalized),args.out) for name in POSE}
    output=dict(assembly="TW-A-0001-R0013",electrical="TW-A-0002-R0006",unit="mm",scale=1,
        source_step_sha256=ledger["step_sha256"],matrix="installed_xyz = matrix @ [print_x,print_y,print_z,1]",
        parts=records)
    (args.out/"geometry.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
