"""Form stock 100 mm battery leads and custom W2 using controlled Rev G wire primitives."""
import importlib.util,json,math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parent
S=ROOT.parents[1]/'mechanical/rev-G/geometry.py'
spec=importlib.util.spec_from_file_location('battery_wire_reference',S)
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
OUT=ROOT/'placed'; OUT.mkdir(exist_ok=True)
rows={}
def factory(variant,i):
    exit_x=ref.CX+((-2,2) if variant=='alt' else (-1.45,1.45))[i]
    exit_y=ref.CY+{'alt':33.,'drawing':31.15,'catalog':31.}[variant]
    exit_z=ref.Z+{'alt':5.5,'drawing':2.65,'catalog':2.5}[variant]
    high=11.55+i*2.15
    turn_z=11.55+.15*i
    dz=(turn_z-exit_z)/2
    dx=(1 if i else -1)*math.sqrt(ref.EDGE**2-dz**2)
    a=(exit_x,exit_y,exit_z);m=(exit_x+dx,exit_y+ref.EDGE,exit_z+dz);b=(exit_x+2*dx,exit_y,turn_z)
    ex,ey,ez=17.975,-24+2*i,10.50
    def path(bow):
        pts=[b,(b[0],exit_y-3,turn_z),(b[0],exit_y-9,high),(b[0],14-i*3,high),(b[0]-bow,6-i*3,high),(b[0]-bow,-10+i*4,high),(ex-5.2,ey,ez),(ex,ey,ez)]
        return [ref.arc(a,m,b),*ref.rounded(pts,3.0)]
    target=97. if variant=='alt' else 100.
    low,high_bow=0.,22.
    for _ in range(25):
        trial=(low+high_bow)/2
        if sum(e.Length() for e in path(trial))>target:high_bow=trial
        else:low=trial
    edges=path((low+high_bow)/2);shape,length=ref.sweep(edges,.70)
    assert abs(length-target)<.02,(variant,i,length,target)
    return shape,{'external_length_mm':round(length,4),'factory_stub_mm':100-target,'nominal_od_mm':1.4,'turnaround_radius_mm':ref.EDGE,'minimum_bend_mm':3.0,'path_mm':[tuple(round(v,3) for v in cq.Wire.assembleEdges(edges).positionAt(k/100).toTuple()) for k in range(101)]}
for variant in ('catalog','drawing','alt'):
    for i in (0,1):
        shape,row=factory(variant,i)
        key=variant+'Tail'+str(i);rows[key]=row;shape.exportBrep(str(OUT/(key+'.brep')))
for i in (0,1):
    x,y,z=29.6,-24+2*i,10.54
    wire_x=-25.878+i*1.25
    points=[(x,y,z),((32.2,31.1)[i],y,z),((32.2,31.1)[i],-14.8-1.45*i,14.35+.18*i),(-24.4-1.75*i,-14.8-1.45*i,14.35+.18*i),(-26.4-i*1.65,-7.5+i*2,12.4+i*1.15),(-27.25+1.70*i,7.0,14.0+i*1.5),(wire_x,13.1,19.05),(wire_x,19.75,19.05)]
    edges=ref.rounded(points,1.45)
    shape,length=ref.sweep(edges,.45)
    key='batt'+str(i);shape.exportBrep(str(OUT/(key+'.brep')))
    rows[key]={'corners_mm':points,'insulated_route_mm':round(length,4),'nominal_od_mm':.90,'bend_radius_mm':1.45,'J7_pos_conditional':('VBAT','GND')[i]}
    copper=cq.Solid.makeCylinder(.16,1.80,cq.Vector(27.8,y,z),cq.Vector(1,0,0))
    copper.exportBrep(str(OUT/('PH-TAIL'+str(i+1)+'.brep')))
    # Local sleeve around the exposed lap solder joint on each header post.
    axis=cq.Vector(1,0,0);a=cq.Vector(26.45,y,10.28)
    sleeve=cq.Solid.makeCylinder(.79,3.80,a,axis).cut(cq.Solid.makeCylinder(.64,4.0,a-axis*.10,axis))
    sleeve.exportBrep(str(OUT/('PH-INS'+str(i+1)+'.brep')))
(OUT/'battery-wires.json').write_text(json.dumps(rows,indent=2)+'\n')

