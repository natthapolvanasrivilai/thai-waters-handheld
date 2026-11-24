"""Installed R0004 geometry. Coordinates are millimetres in the registered A1 frame."""
from pathlib import Path
import sys
import cadquery as cq
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'enclosure-fit-r0003'
sys.path.insert(0,str(OLD))
from mount import geometry,box,cyl
from closure import features
CENTRES=[(51.,-24.),(51.,24.)]

def build(cache, export=True, operations=None):
    parent,_,shelf,posts,cut=geometry()
    shell=parent
    def alter(sign,*tools):
        nonlocal shell
        if operations is not None:
            operations.extend((sign,s) for s in tools)
        shell=shell.fuse(*tools) if sign==1 else shell.cut(*tools)
    alter(-1,cut)
    alter(1,*posts)
    alter(-1,features()[1][-1])
    bezel=cq.Shape.importBrep(str(cache/'Bezel.brep'))
    for x,y in CENTRES:
        alter(1,cyl(x,y,2.10,3.45,23.65))
        alter(-1,cyl(x,y,-4,2.28,26.60),cyl(x,y,22.59,1.20,3.35))
        bezel=bezel.fuse(cyl(x,y,25.92,2.56,1.90)).cut(cyl(x,y,25.88,.80,3.12))
    for y in (-18.,18.):
        pts=[(-46.75,27.82),(-46.75,24.92),(-47.70,24.92),(-48.21,25.24),(-48.21,25.92),(-47.76,25.92),(-47.76,27.82)]
        wire=cq.Wire.makePolygon([cq.Vector(x,y-2.15,z) for x,z in pts],close=True)
        bezel=bezel.fuse(cq.Solid.extrudeLinear(wire,[],cq.Vector(0,4.30,0)))
        alter(1,box(-49.25,y-3.5,24.25,-46.50,y+3.5,27.79))
        alter(-1,box(-48.48,y-2.50,24.66,-46.22,y+2.50,26.14),
                        box(-48.00,y-2.50,26.13,-46.22,y+2.50,27.85))
    # Restore the exterior skin across the three legacy holes and engraved legends.
    # The inner channel is stepped to stop the diffuser's wider retaining flange.
    alter(1,box(-50.,-9.6,11.79,-46.99,9.60,14.52))
    alter(-1,box(-50.5,-1.25,12.10,-43.99,1.25,14.10),
                    box(-44.45,-2.00,11.30,-42.40,2.00,14.12))
    optic=box(-49.95,-1.05,12.30,-43.05,1.05,13.90).fuse(box(-44.20,-1.75,11.52,-43.65,1.75,13.90)).clean()
    shelf=shelf.fuse(box(-43.45,-1.85,11.43,-42.35,1.85,12.10))
    board=cq.Shape.importBrep(str(cache/'USB-PCB1.brep'))
    bb=board.BoundingBox()
    led=box(bb.xmin-.70,-.8,12.30,bb.xmin,.8,13.90)
    parts={'housing':shell.clean(),'bezel':bezel.clean(),'shelf':shelf.clean(),'diffuser':optic,'rgb-gauge':board.fuse(led).clean()}
    for name,part in parts.items():
        assert part.isValid() and len(part.Solids())==1,name
        if export:cq.exporters.export(part,str(HERE/(name+'.step')))
    return parts

if __name__=='__main__':build(Path(sys.argv[1]))
