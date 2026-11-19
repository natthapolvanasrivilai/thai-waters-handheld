"""Print-only inert clearance gauges. All supplier coordinates and dimensions are in mm."""
from pathlib import Path
import json
import cadquery as cq
import trimesh

HERE=Path(__file__).resolve().parent
OUT=HERE/'gauges';OUT.mkdir(exist_ok=True)
def bore(x):
    return cq.Solid.makeCylinder(.80,6,cq.Vector(x,31.35,2.65),cq.Vector(0,-1,0))
# Unradiused maximum drawing block challenges the entire pocket width and length.
pk=cq.Solid.makeBox(35.3,62.3,5.3,cq.Vector(-17.65,-31.15,0)).cut(bore(-1.45),bore(1.45))
# Fusing the supplier's four original solids retains both rigid lead stubs and the protection cap.
cad=cq.importers.importStep(str(HERE/'inputs/Adafruit-258.step')).val().Solids()
alternate=cad[0].fuse(*cad[1:]).clean()
measures=[]
for name,s in [('PKCELL-max-body-with-wire-sockets',pk),('Adafruit-258-CAD-with-PCM-and-stubs',alternate)]:
    file=OUT/(name+'.stl');cq.exporters.export(s,str(file),tolerance=.025,angularTolerance=.12)
    mesh=trimesh.load_mesh(str(file));assert mesh.is_volume and mesh.is_watertight and len(mesh.split())==1
    dims=[round(float(x),3) for x in mesh.extents]
    measures.append(dict(file=file.name,dimensions_mm=dims,single_watertight_solid=True))
(OUT/'dimensions.json').write_text(json.dumps(measures,indent=2)+'\n',encoding='utf8')
print(measures)
