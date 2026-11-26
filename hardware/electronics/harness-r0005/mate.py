"""Installed CviLux W4 parts and a fixed-length, fixed-tap service-loop construction."""
from pathlib import Path
import math
import json
import numpy as np
from scipy.optimize import brentq

import cadquery as cq
from OCP.GCPnts import GCPnts_AbscissaPoint
from geometry import box, cylinder, sweep, V

HERE = Path(__file__).resolve().parent
SRC = HERE / "source-cad"
NET_PIN = {"VCC": 1, "SCL": 3, "SDA": 4, "GND": 5}
TAP_Y = {"VCC": 18.0, "SCL": 19.65, "SDA": 21.3, "GND": 22.95}
PIVOT = (20.96,-6.55,13.56)
RELEASE_DEG = -13.0
STROKE = 8.25
JACKET_OD = 1.42   # Upper crimp drawing diameter, CIEP06SA.
COLOR = {"VCC":"#cf7651","GND":"#545a62","SDA":"#849ec0","SCL":"#9aaa72"}

def source(name):
    return cq.importers.importStep(str(SRC / (name+".step"))).val()

def pin_x(pin):
    return 15.96 + (pin-1)*2.5

def endpoints(net, tx, z, travel=0):
    x = pin_x(NET_PIN[net])
    return np.array([x,-1.4+travel,10.36]), np.array([tx,TAP_Y[net],z+2.0])

FORM = json.loads((HERE/'loop-forms.json').read_text())
NODES, WEIGHTS = np.polynomial.legendre.leggauss(64)
NODES = .5*(1+NODES)
WEIGHTS = .5*WEIGHTS

def curve(net,a,b,travel,t,bow=0,derivative=False):
    # Cubic endpoint tangents connect the barrel and the formed tap.
    # Two quartic/quintic offsets shape the free span without moving its ends.
    cx,cz,sx,sz,dynamic,ky,kz=FORM[net]
    t=np.asarray(t).reshape(-1,1)
    s=1-t
    c=a+[0,ky,0]
    e=b+[0,-.70*kz,kz]
    belly=16*t*t*s*s
    shift=np.array([cx+dynamic*travel,0,cz+bow])
    twist=np.array([sx,0,sz])
    if derivative:
        db=32*t*s*(1-2*t)
        return 3*(s*s*(c-a)+2*s*t*(e-c)+t*t*(b-e))+db*shift+(db*(2*t-1)+2*belly)*twist
    return s**3*a+3*s*s*t*c+3*s*t*t*e+t**3*b+belly*shift+belly*(2*t-1)*twist

def length(net,a,b,travel,bow):
    speed=np.linalg.norm(curve(net,a,b,travel,NODES,bow,derivative=True),axis=1)
    return WEIGHTS@speed

def guide(net,tx,z,travel,count=49):
    a0,b=endpoints(net,tx,z)
    a,_=endpoints(net,tx,z,travel)
    target=length(net,a0,b,0,0)
    bow=0 if travel==0 else brentq(lambda v:length(net,a,b,travel,v)-target,0,30)
    return curve(net,a,b,travel,np.linspace(0,1,count),bow).tolist()

def loop_edge(net,tx,z,travel):
    # The guide is degree five. Recover its six Bernstein poles directly.
    # Interpolating stations with an unconstrained B-spline can overshoot.
    t=np.linspace(0,1,6)
    bernstein=np.stack([math.comb(5,i)*(1-t)**(5-i)*t**i for i in range(6)],axis=1)
    poles=np.linalg.solve(bernstein,guide(net,tx,z,travel,6))
    return cq.Edge.makeBezier([V(*p) for p in poles])

def arc_length(edge):
    return GCPnts_AbscissaPoint.Length_s(edge._geomAdaptor(),1e-8)

def jacket(net, tx, z, travel=0):
    edge=loop_edge(net,tx,z,travel)
    tip=edge.startPoint()
    start=V(tip.x,-5.35+travel,tip.z)
    path=cq.Wire.assembleEdges([cq.Edge.makeLine(start,tip),edge])
    return sweep(path,JACKET_OD/2), 3.95+arc_length(edge)

def split_latch(plug):
    # Exact supplier BRep split through the parallel flexure neck, above body.
    cut=box(16.7,-12.6,13.592,8.5,10.0,3.6)
    return plug.cut(cut),plug.intersect(cut)

def actuate(shape,ratio):
    return shape.rotate(PIVOT,(PIVOT[0]+1,*PIVOT[1:]),RELEASE_DEG*ratio)

def branch(add,routes,nets):
    board=cq.importers.importStep(str(HERE.parent/'pcb-haptic-cie-r0001/A3-substrate.step')).val()
    board=board.rotate((0,0,0),(0,0,1),90).translate((-37.95,-135.15,4.60))
    add('drvBoard',board,'A3 2.50 mm revision substrate','Installed KiCad A3-substrate.step with the CviLux J1 footprint. Bare substrate STEP is 1.51 mm thick.','#2c7350')
    header=source('CIEP05P1HK0-NH').translate((22.713653857,-10.6093745,1.66))
    add('A3-J1-header',header,'CviLux right-angle header','CIEP05P1HK0-NH manufacturer solid, both molded lock bosses and five integral-model pins.','#83b7ad')
    plug=source('CIEP05SL000').rotate((0,0,0),(1,0,0),180).translate((20.96,-7.65,10.535))
    add('A3-J1-plug',plug,'CviLux five-way latch housing','CIEP05SL000 unmodified manufacturer solid. Supplied blind pin pockets and flat catch underside limit seating validation.','#f1daae')
    # Register both outer side-lock slots on the actual two molded ears.
    # Left/right ears occupy z=11.985..12.735; slot spans 1.000 mm.
    # Its closed Y-end is 0.10 mm inboard of the ear retention face.
    tpa=source('CIEP05C0010').rotate((0,0,0),(0,0,1),180).translate((20.96,-1.425,12.385))
    add('A3-J1-TPA',tpa,'CviLux terminal position assurance','CIEP05C0010 supplier solid. Both outer slots registered to molded side ears; internal tooth pockets are absent from the supplier plug solid. Lock depth requires supplier or physical confirmation.','#545c68')
    spacer=box(13.62,-15.8,6.11,14.68,2.10,1.4)
    for pin in range(1,6):
        x=pin_x(pin)
        spacer=spacer.cut(cylinder((x,-14.9,6),(x,-14.9,7.65),.68))
    add('A3-J1-spacer',spacer,'1.40 mm header support','Unclad insulating drilled shim under the rear header feet. Verify shroud support contact and final solder-tail protrusion.','#aa9665')
    # Keep exact stamped mating portion of the detached 8 mm terminal; close
    # only the two open wings using concentric formed-barrel envelope studies.
    front=source('CIEPT021PP0-open').intersect(box(-2,-1,-4.8,4,5,4.81))
    for net,pin,_,_,z,_,tx in nets:
        x=pin_x(pin)
        spring=front.rotate((0,0,0),(1,0,0),90).translate((x,-11.75,9.65))
        barrel=cylinder((x,-6.95,10.36),(x,-5.35,10.36),.46).cut(cylinder((x,-7,10.36),(x,-5.3,10.36),.204))
        sleeve=cylinder((x,-5.35,10.36),(x,-3.75,10.36),.91).cut(cylinder((x,-5.37,10.36),(x,-3.73,10.36),JACKET_OD/2))
        contact=cq.Compound.makeCompound([spring,barrel,sleeve])
        add(f'A3-J1-C{pin}',contact,f'Cavity {pin} {net} terminal','CIEPT021PP0 stamped socket nose retained. Two annular closed-wing envelopes are illustrative, pending crimp microsection and measurement.','#bf9364')
        add('wh'+net+'-Cu',cylinder((x,-6.95,10.36),(x,-5.35,10.36),.203),'W4 '+net+' conductor','26 AWG nominal copper conductor in the modeled front crimp.','#c58456')
        lead,ln=jacket(net,tx,z)
        add('wh'+net,lead,'W4 '+net+' service loop','Fixed-length bending branch. Crimp end follows plug, other end remains bonded to stationary W1 tap.',COLOR[net])
        y=TAP_Y[net]
        shoulder=V(tx,y,z+2)
        center=V(tx,y,z)
        drop=cq.Edge.makeBezier([shoulder,shoulder+V(0,.35,-.5),center+V(0,.2,.5),center])
        copper=cylinder((tx-1.4,y,z),(tx+1.4,y,z),.127).fuse(sweep(drop,.203))
        rings=[cq.Wire.makeCircle(.71-.36*t,drop.positionAt(t),drop.tangentAt(t)) for t in np.linspace(0,1,6)]
        taper=cq.Solid.makeLoft(rings)
        seal=cylinder((tx-1.4,y,z),(tx+1.4,y,z),.45).fuse(taper).cut(copper)
        for suffix,shape,col in [('-Cu',copper,'#b67b52'),('-seal',seal,'#4f6666')]:
            add('tee-'+net+suffix,shape,'W1 '+net+' fixed tap'+suffix,'Stationary dressed tee. W4 jacket ends at the overcoat shoulder.',col)
        routes[net]=dict(pin=pin,tap_center_mm=[tx,y,z],full_jacket_length_mm=round(ln,4),jacket_od_mm=JACKET_OD,
                         crimp_end_mm=[x,-5.35,10.36],free_branch_start_mm=[x,-1.4,10.36],fixed_branch_end_mm=[tx,y,z+2.0])
