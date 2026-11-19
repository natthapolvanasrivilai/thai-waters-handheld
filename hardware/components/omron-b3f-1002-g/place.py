"""Place the KiCad B3F-100x exterior on the R0009 key carrier; units are millimetres."""
from pathlib import Path
import cadquery as cq

HERE=Path(__file__).resolve().parent
def placed():
    original=cq.importers.importStep(str(HERE/'B3F-100x.step')).val()
    # Source pin one is the local origin. Center the body on the existing button.
    body=original.translate((-3.25,2.25,0))
    # Trim through-hole leads to 0.80 mm below the 1.00 mm PCB.
    def piece(bottom,top):
        tool=cq.Solid.makeBox(24,24,top-bottom,cq.Vector(-12,-12,bottom))
        return body.intersect(tool).rotate((0,0,0),(1,0,0),-90).translate((-36,28.65,12.50))
    return {'Trimmed terminals':piece(-1.8,0),'Switch case':piece(0,3.35),'Switch plunger':piece(3.35,4.31)}

if __name__=='__main__':
    for key,shape in placed().items():
        assert shape.isValid() and shape.Volume()>0
        cq.exporters.export(shape,str(HERE/(key+'.brep')),exportType='BREP')
