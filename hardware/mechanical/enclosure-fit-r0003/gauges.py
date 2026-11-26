"""Make unpowered installation gauges in real board and installed coordinates."""
from pathlib import Path
from hashlib import sha256
import json
import cadquery as cq
from mount import HERE,BASE,V,b,box,cyl
import sys
sys.path.insert(0,str(BASE))
from build import OUTLINE,MOUNTS

def pcb():
    src=BASE/'case-board.step'
    real=cq.importers.importStep(str(src)).val()
    # On KiCad's exported component side +Y is toward the board's low drawing Y.
    poly=[(x-100,100-y) for x,y in OUTLINE]
    board=cq.Workplane('XY',origin=(0,0,-.04)).polyline(poly).close().extrude(.84).val()
    for x,y in MOUNTS:
        board=board.cut(cyl(x-100,100-y,-.1,1.15,1))
    packages=[]
    for s in real.Solids():
        x,X,y,Y,z,Z=b(s)
        if Z>.81:
            # Round the height outward to a printed layer from the bottom datum.
            import math
            top=math.ceil((Z+.04-1e-5)/.2)*.2-.04
            packages.append(box(x,y,.78,X,Y,top))
    assert len(packages)>25
    gauge=board.fuse(*packages).clean()
    # Compare every package to the printable envelope; copper below -.04 is tolerance.
    misses=[s.cut(gauge).Volume() for s in real.Solids() if b(s)[5]>.81]
    assert max(misses)<.001
    return gauge,dict(package_solids=len(packages),max_missing_package_mm3=max(misses),real_bounds=b(real),gauge_bounds=b(gauge),source_sha256=sha256(src.read_bytes()).hexdigest())

def other(cache):
    # Simple original clearance gauges, built from installed component datums.
    # Keep the oval rim, gasket and the soft lead stubs printable as one silhouette.
    def read(n):return cq.Shape.importBrep(str(cache/(n+'.brep')))
    speaker=read('Speaker').fuse(*[read(k) for k in ['speakerCloth','speakerGasket','speakerRim','speakerDiaphragm','speakerMagnet','speakerPoleRing','speakerTerminal0','speakerTerminal1']]).clean()
    # A dry-fit gauge may fill enclosed voids. Populate from the source footprints
    # above their bed projection to prevent floating terminals or diaphragm starts.
    def oval(x,X,y,Y,z,Z):
        return cq.Workplane('XY',origin=((x+X)/2,(y+Y)/2,z)).slot2D(Y-y,X-x,angle=90).extrude(Z-z).val()
    # Use the actual metal frame silhouette through its height. Fill only internal
    # voids bounded by that frame using its exterior cross section.
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    def outline(s,z):
        face=cq.Face.makePlane(150,150,V(0,0,z))
        edges=cq.Shape.cast(BRepAlgoAPI_Section(s.wrapped,face.wrapped).Shape()).Edges()
        wires=cq.Wire.combine(edges)
        return max(wires,key=lambda w:cq.Face.makeFromWires(w).Area())
    frame=read('Speaker')
    outline_wire=outline(frame,6.0).translate((0,0,-1.75))
    body=cq.Solid.extrudeLinear(outline_wire,[],V(0,0,5.1))
    # The magnet and two lead ends are the height controls.
    body=body.fuse(cyl(-40.52,0,8.9,7.60,.85))
    for name in ('speakerTerminal0','speakerTerminal1'):
        x,X,y,Y,z,Z=b(read(name))
        body=body.fuse(box(x-.12,y,4.25,X+.12,Y,Z))
    # Factory motor body and integrated strain relief envelope, wire routing by loose leads.
    m=cyl(19,14,3,5,3.55).fuse(box(17.5,14,3,20.5,24,6.55))
    return body.clean(),m.clean(),dict(speaker_source_bounds=b(speaker),speaker_gauge_bounds=b(body),motor_source_bounds=b(read('motor')),motor_gauge_bounds=b(m))
