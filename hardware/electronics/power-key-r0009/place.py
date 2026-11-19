"""Recover the manufactured four-hole carrier from the project Gerber drill program."""
from pathlib import Path
import re,zipfile
import cadquery as cq
HERE=Path(__file__).resolve().parent
source=HERE.parent/'Rev-F-power-key-carrier-Gerber.zip'
with zipfile.ZipFile(source) as z:
    drill=z.read('power-key-PTH.drl').decode()
radius=float(re.search(r'T01C([\d.]+)',drill).group(1))/2
centers=[tuple(map(float,row)) for row in re.findall(r'X([\d.]+)Y([\d.]+)',drill)]
assert len(centers)==4
board=cq.Solid.makeBox(11.,1.,10.,cq.Vector(-41.5,27.65,7.5))
holes=[cq.Solid.makeCylinder(radius,1.4,cq.Vector(-41.5+x,27.45,7.5+z),cq.Vector(0,1,0)) for x,z in centers]
board.cut(*holes).clean().exportBrep(str(HERE/'Key PCB.brep'))
