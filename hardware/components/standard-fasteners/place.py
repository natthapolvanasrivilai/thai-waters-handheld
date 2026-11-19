"""Install catalogue-standard fasteners on the R0009 datums (all dimensions in mm).
Requires cq_warehouse a57bb7a24762d367d66369f280a24c38a64e73dd and CadQuery.
"""
import json
from pathlib import Path
import cadquery as cq
from cq_warehouse.fastener import PanHeadScrew,HexNut

HERE=Path(__file__).resolve().parent
def pose():
    screws={n:cq.Shape.cast(PanHeadScrew(size='M2-0.4',length=n,fastener_type='iso14583',simple=False).wrapped) for n in (4,6,8)}
    nut=cq.Shape.cast(HexNut(size='M3-0.5',fastener_type='iso4032',simple=False).wrapped)
    for size,source in [(str(n)+'mm',s) for n,s in screws.items()]+[('nut',nut)]:
        cq.exporters.export(source,str(HERE/(size+'.step')))
    installed={}
    for i,(x,y) in enumerate([(-36,-24.25),(-36,24.25),(36,-24.25),(36,24.25)],1):
        installed['H1-'+str(i)]=screws[8].rotate((0,0,0),(1,0,0),180).translate((x,y,11))
    installed['Keeper screw']=screws[6].translate((-43.2,28.7,19.15))
    for index,x in enumerate((-31.85,11.1),1):
        installed['tieS'+str(index)]=screws[4].translate((x,18.5,10.75)).rotate((-31.85,18.5,0),(-31.85,18.5,1),-7.4)
    # Flats of the 5.5 AF nut run parallel to X across the Y-width of the trap.
    if nut.BoundingBox().xlen < nut.BoundingBox().ylen:nut=nut.rotate((0,0,0),(0,0,1),90)
    installed['Receiver nut']=nut.translate((17,-24.5,2.15))
    folder=HERE/'placed';folder.mkdir(exist_ok=True)
    for name,part in installed.items():
        assert part.isValid(),name
        part.exportBrep(str(folder/(name+'.brep')))
        b=part.BoundingBox()
        print(name,[round(v,3) for v in (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)],len(part.Faces()))
if __name__=='__main__':pose()
