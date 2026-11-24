"""Build the board mount from the editable R0008 housing and placed PCB solids."""
from pathlib import Path
import sys

from layout import HERE, PARENT, SCREWS, REST
import cadquery as cq
from fit import MOUNTS as OLD_MOUNTS, REST as OLD_REST, support, cyl
ROOT=HERE.parents[2]
BASE=ROOT/'hardware/mechanical/step-fit-r0008/housing.step'
SEAT=17.70
BACK=18.50
FLOOR=2.50

def stock(path):
    return cq.importers.importStep(str(path)).val()

def taper(x,y,stations):
    rings=[cq.Wire.makeCircle(r, cq.Vector(x+dx, y+dy, z), cq.Vector(0,0,1))
           for z,dx,dy,r in stations]
    return cq.Solid.makeLoft(rings,ruled=True).clean()

def mounted():
    pcb=stock(HERE/'case-board.step').rotate((0,0,0),(1,0,0),180).translate((13,-14,BACK))
    screw=stock(ROOT/'hardware/components/standard-fasteners/4mm.step')
    solids={'PCB':pcb}
    for i,(x,y) in enumerate(SCREWS,1):
        if i==1:
            stock_post=cyl(x,y,2.1,2.05,SEAT-2.1)
        else:
            stock_post=taper(x,y,[(2.1,0,2.5,2.05),(7.1,0,2.5,2.05),
                                  (13.2,0,0,1.95),(SEAT,0,0,2.05)])
        post=stock_post.cut(cyl(x,y,13.2,.82,4.6))
        solids[f'boss {i}']=post
        solids[f'screw {i}']=screw.translate((x,y,BACK))
    solids['rest']=taper(*REST,[(2.1,0,0,2.05),(15.5,0,0,1.75),
                               (SEAT,-.55,-2.0,1.65)])
    # Trim the back of the contact land under the straight board edge.
    solids['rest']=solids['rest'].cut(cq.Solid.makeBox(8,6,2,cq.Vector(34,18.95,17.20)))
    return solids

def floor():
    shell=stock(BASE)
    limits=cq.Solid.makeBox(100,100,25,cq.Vector(-50,-50,FLOOR))
    centers=[(x-87,y-114) for x,y in OLD_MOUNTS]+[OLD_REST]
    for i,(x,y) in enumerate(centers,1):
        shell=shell.cut(support(x,y,i).intersect(limits))
    shell=shell.clean()
    assert len(shell.Solids())==1 and shell.isValid()
    return shell

def export():
    parts=mounted()
    housing=floor().fuse(parts['boss 1'],parts['boss 2'],parts['rest']).clean()
    assert housing.isValid() and len(housing.Solids())==1
    cq.exporters.export(housing,str(HERE/'housing.step'))
    assembly=cq.Assembly(name='Case_board_mount')
    assembly.add(housing,name='Housing',color=cq.Color(.48,.60,.51))
    assembly.add(parts['PCB'],name='Control_and_USB_PCB',color=cq.Color(.10,.42,.27))
    for i in range(1,3):
        assembly.add(parts[f'screw {i}'],name=f'M2_screw_{i}',color=cq.Color(.69,.70,.67))
    assembly.export(str(HERE/'case-mount-assembly.step'))

if __name__=='__main__':export()
