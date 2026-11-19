"""Place the two supplier assemblies and form six workshop wires in assembly axes (mm)."""
import json
from pathlib import Path
import math
import cadquery as cq

HERE=Path(__file__).resolve().parent
HARD=HERE.parents[1]
OUT=HERE/'placed'
V=cq.Vector
board=cq.importers.importStep(str(HARD/'components/boardoza-drv2605l/DRV2605L.step')).val().translate((-107.35,52.75,4.60))
motor=cq.importers.importStep(str(HARD/'components/sparkfun-rob-08449/8449.STEP')).val().rotate((0,0,0),(0,0,1),90).translate((19,19,3))
parts={'drvBoard':board.Solids()[17],'drvParts':cq.Compound.makeCompound(board.Solids()[:17]),'motor':motor}
# Cut support strips from 3M 4991 gray VHB, 2.3 mm nominal before compression;
# installed top at 4.60 and nominal floor at 2.50. Set final pad thickness by measurement.
parts['adhH']=cq.Compound.makeCompound([cq.Solid.makeBox(3.,12.,2.1,V(x,-12,2.5)) for x in [16.5,24.5]])
reference=json.loads((HARD/'mechanical/rev-F/review/routes.json').read_text())
routes={}
# A3 J1 shipped header: solder onto the side of each pin. Each horizontal
# branch terminates at the metal. Insulation ends 1.2 mm before its terminal.
for net,ypin in {'VCC':-1.08,'GND':-11.24,'SDA':-8.70,'SCL':-6.16}.items():
    k='wh'+net
    z=reference[k]['points_mm'][0][2]
    wy={'VCC':1.2,'GND':3.4,'SDA':5.8,'SCL':7.8}[net]
    tee=[29.,wy,z]
    routes[k]=[tee,[27.5,wy,z],[22.5,7.,z],[19.5,ypin,z],[14.42,ypin,z]]
# The two 0.55 mm vendor leads continue from the actual STEP stub ends and
# are trimmed to the solder pads. A single continuous conductor per motor output.
routes['wm0']=[[19.475,9.,6.04],[19.475,7.0,6.04],[25.0,4.8,7.10],[31.50,2.0,7.80],[32.00,-4.40,7.80],[30.50,-6.70,7.20],[29.10,-7.90,6.75]]
routes['wm1']=[[18.507,9.,6.04],[18.507,6.2,6.04],[21.0,4.25,8.10],[24.3,1.85,8.30],[27.4,-.60,8.00],[29.10,-2.40,7.35]]
def pipe(p,r):
    # Interconnects use a smoothed B-spline from the branch, with linear copper tails.
    pts=[V(*q) for q in p];edge=cq.Edge.makeSpline(pts)
    contour=cq.Wire.makeCircle(r,pts[0],edge.tangentAt(0))
    return cq.Solid.sweep(contour,[],edge,True,False),edge.Length()
def line(a,b,r):
    a,b=V(*a),V(*b);d=b-a
    return cq.Solid.makeCylinder(r,d.Length,a,d.normalized())
record={}
for k,points in routes.items():
    is_motor=k.startswith('wm')
    r=.275 if is_motor else .400
    outer,length=pipe(points,r)
    a=points[-1];b=(a[0],a[1],5.5) if is_motor else (13.18,a[1],a[2])
    parts[k]=outer
    parts[k+'-Cu']=line(a,b,.127)
    record[k]=dict(stock='SparkFun factory lead' if is_motor else 'Adafruit 30AWG silicone 0.8mm nominal OD',
                   od_mm=2*r,points_mm=points,insulated_length_mm=round(length,3),stripped_tail_end_mm=b)
# Boardoza's unused IN/TRIG J1-2 is grounded for its internal ROM mode.
# Solder the local link to the west side of J1-2/J1-5, leaving individual bus leads on the east.
bridge=[(11.6,-3.62,12.95),(10.8,-3.62,12.95),(10.3,-5.4,12.95),(10.3,-9.5,12.95),(10.8,-11.24,12.95),(11.6,-11.24,12.95)]
parts['whTrig'],length=pipe(bridge,.4)
parts['whTrig-Cu']=cq.Compound.makeCompound([line(bridge[0],(12.62,-3.62,12.95),.127),line(bridge[-1],(12.62,-11.24,12.95),.127)])
record['whTrig']=dict(stock='Adafruit 30AWG silicone',od_mm=.8,points_mm=bridge,insulated_length_mm=round(length,3),function='J1-2 unused IN/TRIG to J1-5 GND')
OUT.mkdir(exist_ok=True)
for k,shape in parts.items():shape.exportBrep(str(OUT/(k+'.brep')))
(OUT/'routes.json').write_text(json.dumps(record,indent=2)+'\n')
print('Exported',list(parts))

