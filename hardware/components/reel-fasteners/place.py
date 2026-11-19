"""Install dimensionally matched catalogue fasteners, keeping the washer face against the grip axle."""
import json
from pathlib import Path
import cadquery as cq
from cq_warehouse.fastener import PanHeadScrew, PlainWasher
HERE=Path(__file__).resolve().parent
def parts():
    def screw(length):
        return cq.Shape.cast(PanHeadScrew('M2-0.4',length,'iso14583',simple=False).wrapped)
    nylon=cq.importers.importStep(str(HERE/'M2-nylon.step')).val()
    m2x10=screw(10);m2x5=screw(5)
    catalog=cq.Shape.cast(PlainWasher('M2','iso7089').wrapped)
    # Re-sew the catalog cylinder surfaces as a single annulus. The original
    # periodic seam writes an open shell on STEP export with this OCC version.
    radii=sorted({round(e.radius(),5) for e in catalog.Edges() if e.geomType()=="CIRCLE"})
    assert radii==[1.10,2.50]
    steel=cq.Workplane("XY").circle(radii[1]).circle(radii[0]).extrude(catalog.BoundingBox().zlen).val()
    assert steel.isValid() and abs(steel.Volume()-5.54177)<.0001
    for f,s in [('ISO14583-M2x10',m2x10),('ISO14583-M2x5',m2x5),('ISO7089-M2',steel)]:
        cq.exporters.export(s,str(HERE/(f+'.step')))
    return {'reel0':m2x10.translate((53.6,7.8,19.6)),
            'reel1':m2x5.rotate((0,0,0),(1,0,0),90).translate((53.6,-8.60,14.8)),
            'H3-1':nylon.translate((53.6,7.8,12.2)), 'H3-2':nylon.translate((53.6,7.8,17.1)),
            'H5':steel.rotate((0,0,0),(1,0,0),90).translate((53.6,-8.25,14.8))}
if __name__=='__main__':
    out=HERE/'placed';out.mkdir(exist_ok=True)
    cad=HERE.parents[1]/'mechanical/TW-A-0001-R0009/CAD'
    references={p.stem:cq.Shape.importBrep(str(p)) for p in cad.glob('*.brep') if p.stem in ['rotor','folding-stem','grip','housing-battery-bay','bezel','collar']}
    posed=parts();report={}
    for k,s in posed.items():
        s.exportBrep(str(out/(k+'.brep')))
        report[k]={}
        for n,other in (references|posed).items():
            if k==n:continue
            b=s.intersect(other)
            report[k][n]={'overlap_mm3':round(b.Volume(),5),'gap_mm':round(s.distance(other),4)}
    # Partition the two disconnected H2 seat/thread contacts before the common.
    # The kernel can report just the counterbore contact for a whole compound.
    for label,lo,hi in [('H2 below upper ear',9.59,12.),('H2 bearing and head',19.599,22.)]:
        slab=cq.Solid.makeBox(5,5,hi-lo,cq.Vector(51.1,5.3,lo))
        screw_section=posed['reel0'].intersect(slab)
        female=references['rotor'].intersect(slab)
        report[label]=dict(overlap_mm3=round(screw_section.intersect(female).Volume(),5))
    (HERE/'fit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['H2 bearing and head'],report['H2 below upper ear'])
