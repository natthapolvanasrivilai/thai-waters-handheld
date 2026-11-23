"""Install the PCB, supports and dressed W1, W4 and motor leads in R0012."""
from pathlib import Path
import hashlib,json,math
import cadquery as cq
from mate import TAP_Y
from geometry import box,cylinder,polyline,sweep,V

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'harness-r0004'
P=HERE/'placed'
files={}
routes={}
def add(name,shape,label,note,color='#464746',group='Haptics',ref='A3 / W4'):
    assert shape.isValid() and shape.Volume()>0,name
    P.mkdir(exist_ok=True)
    file=P/(name+'.brep')
    shape.exportBrep(str(file))
    files[name]=dict(name=name,brep='placed/'+file.name,label=label,group=group,ref=ref,
            color=color,note=note,sha256=hashlib.sha256(file.read_bytes()).hexdigest())

def pcb():
    source=HERE.parent/'pcb-r0004/harness.step'
    board=cq.importers.importStep(str(source)).val().rotate((0,0,0),(1,0,0),180).translate((13,1,18.5))
    add('A4-integration',board,'A4 populated R0004 integration PCB',
        'Direct rigid placement of the released populated KiCad PCB STEP, including all board copper and library package solids. Component face points toward the floor.','#306c45','Wiring','A4')
    pads=[(14,-11.5),(32,-11),(32,-3)]
    # The pads are placed against solder mask on the electrical back of A4.
    # A 2 mm spacer lifts A4 by 1 mm to clear the pressed connector rocker.
    spacer=cq.Compound.makeCompound([box(x,y,18.75,3,3,2) for x,y in pads])
    tape=cq.Compound.makeCompound([box(x,y,z,3,3,.25) for x,y in pads for z in (18.5,20.75)])
    add('A4-spacers',spacer,'Three A4 insulating spacers','Three 3 x 3 x 2 mm electrically insulating blocks between A4 and A1. Verify 0.50 mm nominal A1 component clearance on the received assembly.','#d0caaa','Wiring','A4')
    add('A4-bond',tape,'Six A4 adhesive bondlines','Two nominal 0.25 mm insulating adhesive bondlines per support. Check assembled thickness, peel, thermal exposure and pad position on the received unit.','#87806c','Wiring','A4')
    power_source=HERE.parent/'pcb-power-r0004/usb-input.step'
    power=cq.importers.importStep(str(power_source)).val().rotate((0,0,0),(1,0,0),180).translate((13,3,17.8))
    add('A5-power',power,'A5 populated USB power-entry PCB','Direct placement of KiCad power daughterboard STEP on the A1 subassembly. The resistor thermal path, six point-to-point wires and controller net isolation need qualification.','#314c6a','Wiring','A5')
    seats=[(16,15.0),(27,12.6),(31,15.8)]
    blocks=cq.Compound.makeCompound([box(x,y,18.05,3,3,2.7) for x,y in seats])
    bond=cq.Compound.makeCompound([box(x,y,z,3,3,.25) for x,y in seats for z in (17.8,20.75)])
    add('A5-spacers',blocks,'Three A5 insulating spacers','3 x 3 x 2.7 mm electrically insulating spacers. Qualify bonded footprint, overhang and vibration.','#c5bfb1','Wiring','A5')
    add('A5-bond',bond,'Six A5 adhesive bondlines','Nominal 0.25 mm insulating adhesive bondlines on both faces of each support. Verify temperature and peel retention.','#81765b','Wiring','A5')
    stock=cq.Shape.importBrep(str(OLD/'placed/drvParts.brep')).Solids()
    removed=[]
    keep=[]
    for s in stock:
        c=s.Center()
        if any(math.hypot(c.x-x,c.y-y)<.005 for x,y in [(24.975,-9.1),(17.35,-4.8)]):removed.append(s)
        else:keep.append(s)
    assert len(removed)==2 and len(keep)==14
    add('drvParts',cq.Compound.makeCompound(keep),'A3 components after R1/R2 removal','Boardoza R1.0 source solids. The two R1/R2 pull-ups removed using the native PCB XY coordinates. Central bus pulls reside on A4.','#3f413e')

def motor():
    for name,stubx,px in [('wm0',19.475,22.7),('wm1',18.507,17.2)]:
        # Both output pads are plated through holes. Enter the bottom of the PCB.
        start=(stubx,9,6.04); end=(px,1.3,4.10)
        a=V(*start);b=V(px,3.8,3.94);c=V(*end)
        bend=cq.Edge.makeBezier([a,a+V(0,-2.8,0),b+V(0,1.35,0),b])
        tip=cq.Edge.makeBezier([b,b+V(0,-.85,0),c+V(0,0,-.53),c])
        path=cq.Wire.assembleEdges([bend,tip])
        add(name,sweep(path,.275),name+' motor lead','Factory motor stub continued underneath A3 to its plated output hole. Insulation remains below the pad.','#9f5048' if name=='wm0' else '#414849')
        add(name+'-Cu',cylinder(end,(px,1.3,6.24),.127),name+' exposed pad end','Bottom entry into the source-board plated through hole. Solder and trim at the component face.','#b7774a')
        routes[name]=dict(start_mm=start,end_mm=end,jacket_length_mm=round(path.Length(),3))

NETS=[('VCC',1,-6.35,19.039,9.1,15.45,22.00),('GND',5,-1.27,16.499,10.16,15.55,30.25),
      ('SDA',4,3.81,13.959,11.22,14.55,28.2),('SCL',3,1.27,11.419,12.28,13.45,26.20)]
def trunks():
    for net,pin,pady,tx,z,lane,teex in NETS:
        tee_y=TAP_Y[net]
        points=[(39.48,pady,8.45),(37.6,pady,8.45),(36.2,pady,z),(31.95,pady,z),
                (31.95,tee_y,z),(teex+1.4,tee_y,z)]
        dest=(tx,14.61,12.23)
        tail=[(teex-1.4,tee_y,z),(teex-2.20,tee_y,z),(teex-2.20,lane,z)]
        if net=='SCL':
            tail += [(20.10,lane,13.65),(13.3,lane,13.65),(tx,13.3,13.65),(tx,14.8,13.15),dest]
        else:
            roll = {'VCC':12.85,'GND':12.9,'SDA':13.0}[net]
            tail += [(tx,lane,z),(tx,roll,z),(tx,roll,12.23),dest]
        s=cq.Compound.makeCompound([polyline(points,.4),polyline(tail,.4)])
        add('w1'+net,s,'W1 '+net+' trunk','Fixed 30 AWG trunk from the reel to J8. Tap on the upper transverse run.','#555957')
        # The tee joint is provided by the branch routing step.
        routes['w1'+net]=dict(points_before_tap_mm=points,points_after_tap_mm=tail,window_mm=2.8)
def main():
    pcb();motor();trunks()
    from mate import branch
    branch(add,routes,NETS)
    original={r['name'] for r in json.loads((OLD/'installed.json').read_text())['add']}
    present=set(files)
    remove=sorted((present & original) | {'A3-mode-strap','A3-mode-strap-Cu'})
    (HERE/'installed.json').write_text(json.dumps(dict(remove=remove,add=list(files.values())),indent=2)+'\n')
    (HERE/'routing.json').write_text(json.dumps(routes,indent=2)+'\n')
if __name__=='__main__':main()

