"""Build the Rev F inspection assembly from the released STEP in assembly coordinates (mm)."""
from pathlib import Path
import argparse,base64,csv,gzip,hashlib,json,math,shutil,sys
import xml.etree.ElementTree as ET
from functools import lru_cache
import cadquery as cq
import numpy as np

HERE=Path(__file__).resolve().parent
REV=HERE.parent
REPO=HERE.parents[3]
P=argparse.ArgumentParser()
P.add_argument('--work',type=Path,required=True,help='Scratch directory for exact STEP/BREP caches and view meshes')
P.add_argument('--full-step',action='store_true',help='Write dressed full-product STEP archive to scratch directory')
P.add_argument('--check',action='store_true',help='Run exact shape intersections on added components')
args=P.parse_args()
TMP=args.work.resolve();TMP.mkdir(parents=True,exist_ok=True)
model=REV/'Rev-F-top-power.step.gz'
model_hash=hashlib.sha256(model.read_bytes()).hexdigest()
cache=TMP/('solids-'+model_hash[:12]);cache.mkdir(exist_ok=True)
if not (cache/'names.json').exists():
    step=TMP/'assembled.step'
    with gzip.open(model,'rb') as src,step.open('wb') as dst:shutil.copyfileobj(src,dst)
    tree=cq.Assembly.load(str(step))
    members={}
    for idx,node in enumerate(tree.children):
        shape=node.obj.moved(node.loc)
        filename=f'{idx:02}.brep';shape.exportBrep(str(cache/filename));members[node.name]=filename
    (cache/'names.json').write_text(json.dumps(members),encoding='utf8')
members=json.loads((cache/'names.json').read_text())
base={n:cq.Shape.importBrep(str(cache/f)) for n,f in members.items()}
basis='Released STEP';vendor='Supplier geometry';env='Nominal envelope';proto='Proposed routing';control='Drawing-based proxy';eagle='Supplier PCB layout'
groups=['Enclosure','Controller','Reel & encoder','Power key','Battery & audio','Haptics','Rod handle','Wiring']
rows={}; shapes={}
def add(key,name,ref,group,kind,shape,delta,stage,note,color,source='',opt='',extra=False):
    ss=shape.Solids()
    bb=shape.BoundingBox()
    bounds=[round(getattr(bb,k),3) for k in ('xmin','xmax','ymin','ymax','zmin','zmax')]
    rows[key]=dict(id=key,name=name,ref=ref,group=group,kind=kind,delta=delta,stage=stage,note=note,color=color,
                   source=source or ('Rev-F-top-power.step.gz' if not extra else 'build_review.py'),option=opt,
                   added=extra,solids=len(ss),bounds_mm=bounds)
    shapes[key]=shape
def map_base(key,n,ref,gr,kind,d,s,note,col,opt=''):
    add(key,n,ref,gr,kind,base[key],d,s,note,col,opt=opt)
def comp(shapes):return cq.Compound.makeCompound(list(shapes))
def box(x,y,z,w,l,h):return cq.Solid.makeBox(w,l,h,cq.Vector(x,y,z))
def cylinder(x,y,z,r,l,d=(0,0,1)):return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(*d))
def tube(a,b,r):
    v=cq.Vector(*b)-cq.Vector(*a);return cq.Solid.makeCylinder(r,v.Length,cq.Vector(*a),v.normalized())
def line(points,r):
    # Rounded corners represent wire occupancy. Each individual route has one connected solid.
    parts=[tube(a,b,r) for a,b in zip(points,points[1:])]
    parts.extend(cq.Solid.makeSphere(r,cq.Vector(*p),angleDegrees1=-90,angleDegrees2=90) for p in points[1:-1])
    return parts[0].fuse(*parts[1:]).clean() if len(parts)>1 else parts[0]
map_base('Housing','Receiver housing','P1','Enclosure',basis,[0,0,-28],1,'Printed Rev F body including dovetail shoe, power-key rails and battery fences.','#91a994')
map_base('Bezel','Display bezel','P1','Enclosure',basis,[0,0,113],6,'Printed front frame. Glass clearance at the rim is only 0.25 mm nominal.','#293f39')
for key,name,ref,d,col in [('Rotor','Reel rotor','P1',[65,0,0],'#52796c'),('Stem','Folding crank arm','P1',[91,0,0],'#b68f57'),('Grip','Reel knob','P1',[90,-19,0],'#d0a065'),('Collar','Axle collar','P1',[38,0,0],'#497965')]:
    map_base(key,name,ref,'Reel & encoder',basis,d,2,'Right-edge reel. Shown folded in the released assembly.',col)
reel=base['Reel hardware'].Solids()
for i,(n,ref,d,c) in enumerate([('Hinge screw','H2',[90,0,18],'#9ca7a4'),('Knob retainer','H4',[91,-32,0],'#87928d'),('Diametric magnet','MG1',[52,0,0],'#77969b')]):
    add('reel'+str(i),n,ref,'Reel & encoder',basis,reel[i],d,2,'Released nominal screw or magnet envelope, without a thread or pole marking.',c)
for key,name,ref,kind,d,col in [('Key cap','Top power cap','P1',basis,[0,32,0],'#d1a267'),('Retainer','Key-carrier retainer','P1',basis,[-18,28,19],'#698b78'),('Key PCB','Power-key PCB','PCB1',basis,[-16,18,8],'#367665'),('Switch case','Momentary switch','SW1',env,[-16,18,8],'#3f4748'),('Switch plunger','Switch actuator','SW1',env,[-16,18,8],'#c49455'),('Trimmed terminals','Switch solder tails','SW1',env,[-16,18,8],'#b1a27b'),('Keeper screw','Carrier screw','H6',env,[-18,28,35],'#838e92')]:
    map_base(key,name,ref,'Power key',kind,d,3,'Captured key and carrier. Physical free travel, insulation and trimmed leads require inspection.',col)
for key,name,ref,d,c,opt in [('Removable rod grip','Detachable rod handle','G1',[0,-48,-12],'#536e5e','rod'),('Grip lock screw','Captive M3 × 10','H7',[0,-48,-34],'#9ba9ac','rod'),('Grip screw keeper','Screw keeper','G1',[0,-48,-42],'#71917c','rod'),('Receiver nut','Trapped M3 nut','H8',[0,0,-16],'#8b999d',''),('Receiver nut keeper','Nut keeper','P1',[0,0,-8],'#668a71','')]:
    map_base(key,name,ref,'Rod handle',basis,d,7 if opt else 1,'Rear rail carries bending load. Screw threads and printed skin finish are idealized.',c,opt)
A=base['Waveshare'].Solids();E=base['AS5600'].Solids()
assert len(A)==546 and len(E)==25
a1={0:('touch','Capacitive display stack','#253a39'),5:('carrier','Main controller PCB','#2a7561'),525:('J8','Expansion header J8','#393e3b'),527:('usb','USB-C socket','#a4ada7'),528:('k3','Onboard PWR switch K3','#5e6b6d'),529:('reset','Onboard RESET','#6f7977'),530:('boot','Onboard BOOT','#6f7977'),535:('J7','Battery socket J7','#c8c0a3'),536:('J9','Speaker socket J9','#d0c9ad'),545:('backing','Display backing','#879896')}
for i in [1,2,3,4]:a1[i]=('mounts','Board fixings','#bdaf86')
def source_board(ss,idx,ref,gr,delta,stage):
    bins={}
    for i,solid in enumerate(ss):
        key,name,color=idx.get(i,('population',ref+' populated components','#7e8d88'))
        bins.setdefault((key,name,color),[]).append(solid)
    for (key,name,col),pieces in bins.items():
        add(ref+'-'+key,name,ref,gr,vendor,comp(pieces),delta,stage,
            'Exact placed supplier solids grouped for inspection. The populated board is purchased as one assembly.',col)
source_board(A,a1,'A1','Controller',[0,0,77],5)
source_board(E,{0:('pcb','Magnetic encoder PCB','#326952'),6:('sockets','STEMMA QT sockets','#cec49b'),7:('sockets','STEMMA QT sockets','#cec49b'),16:('chip','AS5600 angle sensor','#424b46')},'A2','Reel & encoder',[28,0,24],2)
map_base('Cell','Design cell envelope','B1','Battery & audio',env,[-41,6,25],4,'62 × 34 × 5 mm allowance from the product page. Inspect incoming cell and the clearance to its lead exit.','#8da4ad')
map_base('Speaker','Kit speaker envelope','SP1','Battery & audio',env,[-48,-20,10],4,'15 × 30 × 7 mm design allowance. Source STEP for the current kit speaker is unavailable.','#767282')
B=cq.importers.importStep(str(HERE/'inputs/Adafruit-258.step')).val().translate((-11.5,0,3.6))
add('cellAlt','Alternate supplier cell CAD','B1','Battery & audio',vendor,B,[-41,6,25],4,'Compare to the catalog envelope. This model has a 37 × 60 mm body, 6 mm at the protection board and 63 mm with lead stubs. Confirm latest production lot.','#c8774e','Adafruit-258.step','alt',True)
# Maximum as-delivered pack body from section 11 of the product-linked PKCELL drawing.
maxpack=box(-11.5-35.3/2,-62.3/2,3.6,35.3,62.3,5.3)
add('cellDrawing','PKCELL drawing maximum','B1','Battery & audio',control,maxpack,[-41,6,25],4,
    '35.3 × 62.3 × 5.3 mm maximum body from QA.S.0228 edition A. Add lead dressing and supplier life-cycle allowance.',
    '#bf9959','PKCELL QA.S.0228 edition A, p. 5','drawing',True)
def extra(key,n,ref,gr,kind,shape,d,s,note,col,opt='',source=''):
    add(key,n,ref,gr,kind,shape,d,s,note,col,source,opt,True)
for i,(x,y) in enumerate([(-36,-24.25),(-36,24.25),(36,-24.25),(36,24.25)]):
    h=cylinder(x,y,9.4,2.2,1.6).fuse(cylinder(x,y,11,1,8))
    extra('H1-'+str(i+1),'Main-board screw '+str(i+1),'H1','Controller',control,h,[0,0,-47],6,'M2 × 8 reference at the Rev E tool-gauge datum. Thread and drive are idealized.','#a4abaa',source='rev-E/scripts/gauges.py')
for i,z in enumerate([12.2,17.1]):
    s=cylinder(53.6,7.8,z,2.1,.3).cut(cylinder(53.6,7.8,z-.1,1.04,.6))
    extra('H3-'+str(i+1),'Hinge shim '+str(i+1),'H3','Reel & encoder',control,s,[91,0,(-1 if not i else 1)*10],2,'Nominal 0.30 mm nylon shim on the hinge axis.','#e0d7b9',source='rev-E/scripts/gauges.py')
# H4 includes a simplified retainer head. Repartition its first 0.4 mm of bearing face
# into a separate washer so the assembled envelope is preserved, with no double occupation.
washer=cylinder(53.6,-8.65,14.8,2.7,.4,(0,1,0)).cut(cylinder(53.6,-8.75,14.8,1.05,.6,(0,1,0)))
extra('H5','Knob thrust washer','H5','Reel & encoder',control,washer,[91,-25,0],2,'Nominal washer under the screw head. The shoulder stack and end float require a real hardware section.','#c1b8a4')
shapes['reel1']=shapes['reel1'].cut(washer).clean()
# Component placement comes from the current STEMMA QT Eagle board, rotated +90 degrees into the cell-side bay.
root=ET.parse(HERE/'inputs/Adafruit-2305-QT.brd')
elems={e.get('name'):e for e in root.iter('element')}
def mapxy(x,y):return 27.89-float(y),-18.7+float(x)
def pos(e):return mapxy(e.get('x'),e.get('y'))
pcb=cq.Workplane('XY').box(17.78,25.4,1.57).edges('|Z').fillet(2.54).val().translate((19,-6,3.785))
def hole(s,x,y,r):return s.cut(cylinder(x,y,2.8,r,2.1))
for k in ['U$1','U$17','U$19','U$21']:pcb=hole(pcb,*pos(elems[k]),1.25)
pin_offsets={p.get('name'):float(p.get('x')) for p in root.findall(".//package[@name='1X05_ROUND_76']/pad")}
hp={};outpins={}
for sig in root.iter('signal'):
    for c in sig.findall('contactref'):
        el=c.get('element')
        if el=='JP2':
            name=sig.get('name'); pin=elems[el];hp[name]=mapxy(float(pin.get('x'))+pin_offsets[c.get('pad')],pin.get('y'))
            pcb=hole(pcb,*hp[name],.5)
        if el in ('JP1','JP3'):outpins[sig.get('name')]=pos(elems[el]);pcb=hole(pcb,*pos(elems[el]),.5)
extra('drvBoard','Haptic controller PCB','A3','Haptics',eagle,pcb,[8,-30,28],4,'Current QT board outline and holes from the vendor Eagle layout. The vendor STEP describes the smaller legacy board.','#296c5b','haptic','Adafruit-2305-QT.brd')
pcs=[]
for key,wh in {'CONN3':(5.85,4.95,2.96),'CONN4':(5.85,4.95,2.96),'U1':(3.0,4.9,1.1),'C1':(.8,1.6,.8),'C3':(1.25,2,.95),'R3':(3,1.6,.6),'D1':(.8,1.6,.8),'C4':(.8,1.6,.8),'C5':(.8,1.6,.8)}.items():
    x,y=pos(elems[key]);w,h,d=wh;pcs.append(box(x-w/2,y-h/2,4.57,w,h,d))
extra('drvParts','Driver IC, sockets and passives','A3','Haptics',control,comp(pcs),[8,-30,28],4,'Component centers follow Eagle; package bodies are bounding solids. Measure populated board height and wire loop.','#9aa998','haptic','Adafruit-2305-QT.brd')
extra('motor','Coin vibration motor','M1','Haptics',env,cylinder(19,19,3,5,2.7),[5,30,26],4,'Ø10 × 2.7 mm envelope. Leads are separately selectable. Confirm bond transfer and EMI on a live board.','#908992','haptic')
# Plug gauges are simple body rectangles, insertion markers and insulated pigtail leads.
for k,n,r,b,d in [('J8plug','Four-way right-angle J8 plug','W1-P',(10.1,20,12,10.2,5.8,2.8),[0,26,43]),('ph','PH battery adapter mate','W2-A',(-16,-15,9.5,7.8,4.0,3.2),[-35,0,20]),('packplug','Battery factory PH plug','B1',(-8.2,-15,9.5,5.5,4,3.2),[-35,0,20]),('j7plug','Battery board-side plug','W2-B',(-27.4,22.8,15.2,4.6,3.4,2.4),[-18,12,44]),('j9plug','Speaker plug','SP1',(-2.9,-26.7,16.1,4.6,3.4,2.4),[-18,-10,45])]:
    extra(k,n,r,'Wiring',control,box(*b),d,5,'Connector body envelope and proposed insertion pose. Mate, key, contact engagement and polarity require a received sample.','#d7cdb0')
nets={}
def wire(k,n,ref,points,r,col,note,opt=''):
    extra(k,n,ref,'Wiring',proto,line(points,r),[0,0,39],5,note,col,opt)
    nets[k]=dict(points_mm=points,insulation_diameter_mm=2*r,polyline_mm=round(sum(math.dist(a,b) for a,b in zip(points,points[1:])),2))
# A2 header local x become assembly Y, local y = 2.54 above PCB lower edge becomes Z = 8.45.
signals=[('VCC','VIN',-6.35,0,'#cc6048'),('GND','GND',-1.27,1,'#454b4d'),('SDA','SDA',3.81,2,'#4e8eaa'),('SCL','SCL',1.27,3,'#c8a24e')]
for name,label,y,i,color in signals:
    x=30.0;z=9.1+i*1.06;xe=10.99+2.54*i
    wire('w1'+name,'Reel '+label,'W1',[(39.48,y,8.45),(37.6,y,8.45),(36.2,y,z),(x,y,z),(x,18.4,z),(27.7,20,z),(xe,20,z),(xe,21.6,12.05)],.4,color,'A2 JP1 pad to J8 plug. 28 AWG design path; trim and strain-relieve after dry fit.')
for i,(name,color) in enumerate([('VCC','#cb6554'),('GND','#50494a'),('SDA','#4f93a1'),('SCL','#bda354')]):
    dx,dy=hp[name]; x=30.; y=17.; z=9.1+i*1.06
    wire('wh'+name,'Driver '+name,'W1',[(x,y,z),(27.5,15,z),(23.1,7,z),(23.1,dy,z),(dx,dy,z),(dx,dy,4.56)],.34,color,'Optional four-conductor branch on the W1 bus to A3 header pads. Define splice and clamp process.', 'haptic')
for i,(sg,col) in enumerate([('OUT+','#c06754'),('OUT-','#577999')]):
    x,y=outpins[sg];wire('wm'+str(i),'Motor '+sg,'M1',[(x,y,4.57),(x,y,8.1+i*.55),(12.8+i,6.9,8.3+i*.52),(17.3+i*.76,11.9,6.1+i*.5),(17.3+i*.76,14.4,5.05)],.35,col,'Motor leads route to the two driver output pads. Leave motor plate free to bond.','haptic')
for i,(n,c) in enumerate([('BAT+','#c35542'),('GND','#474a49')]):
    d=i*1.62
    # Two full factory leads per PKCELL's product-linked drawing, on separate height layers.
    # The adjustable return leg takes up the remainder of the 100 mm stock length.
    def pack_path(return_x):
        z=10.75+1.65*i
        return [(-12.6+2.1*i,30.55,7.5),(-12.6+2.1*i,30.82,9.4+1.65*i),
                (-12.6+2.1*i,29.3,z),(-1.7,25,z),(-1.7,4,z),(return_x,4,z),
                (return_x,-6.5,z),(-1.3,-6.5,z),(-1.3,-13.15-1.5*i,z),
                (-2.7,-13.15-1.5*i,10.6+1.1*i)]
    import math
    reference_path=pack_path(-19)
    length=sum(math.dist(a,b) for a,b in zip(reference_path,reference_path[1:]))
    packroute=pack_path(-19-(100-length)/2)
    wire('pack'+str(i),'Cell tail '+n,'B1',packroute,.70,c,
         '100 mm SKU drawing lead path, 24 AWG. Assumed 1.4 mm insulated diameter. Verify exit, bend radius, actual wire OD and service loop away from the pouch.')

    wire('batt'+str(i),'Battery adapter '+n,'W2-A / W2-B',[(-16,-13.8+d,10.5+i*1.2),(-20.5,-12+d,11.2+i*1.2),(-27.9,-7.5,12+i*1.2),(-27.9,16,13+i*1.2),(-25.8+d,22.8,15.6+i*1.15)],.45,c,'Two spliced adapter halves. Continuity-test both connector pinouts before installing B1.')
    wire('spk'+str(i),'Speaker '+('+' if not i else '−'),'SP1',[(-34.8+d,-14.7,9.2),(-32+d,-18.1,12.4+i*1.0),(-24,-19.3+d,13+i),(-7.5,-20.4+d,14.2+i),(-1.7+d,-24.6,16.2+i*.9)],.36,['#99718d','#6c6b7a'][i],'Factory speaker pair to J9 amplifier outputs. The terminal positions on the speaker are provisional.')
for i,c in enumerate(['#d9d4bb','#4c5052']):
    d=i*.85
    wire('w3'+str(i),'Power key '+('signal' if not i else 'return'),'W3',[(-39.25+6.5*i,26.85,10.25+4.5*i),(-40.55+8.65*i,25.8,11.6+3.5*i),(-40.55+i*8.9,22.7,13+i*2.5),(-39.7+i*8.1,18.7,13+i*1.8),(-32.8,9.4,12+i*1.6),(-32.8,-13,12+i*1.6),(-28+2*i,-21.3+i*.4,16.2+i*1.1),(-25.5+2.4*i,-23.5,19.1)],.35,c,'SW1 to K3. Endpoints identify the switch region; continuity-locate K3 pads and confirm solder allowance and wire dressing.')
# Shop stock is represented by nominal adhesive placement. These are proposed pad sizes.
pads=[cylinder(19,19,2.5,4.3,.5),box(12,-17,2.5,5,5,.5),box(21,0,2.5,5,5,.5)]
extra('adhH','Haptic mounting pads','SHOP1','Haptics',control,comp(pads),[3,0,9],4,'0.5 mm adhesive allowance. Neither size, grade, adhesion nor transfer is production-qualified.','#beb7a1','haptic')
# Mated header pins and shop consumables. The header's insertion depth is nominal.
pins=comp([box(10.99+i*2.54-.32,21.6-.32,14.75,.64,.64,3.0) for i in range(4)])
extra('hdrPins','J8 male header contacts','W1-P','Wiring',control,pins,[0,26,43],5,'Four nominal 0.64 mm square contacts. Gauge the insertion depth and pin-1 orientation on the actual socket.','#c39c58')
for i in (0,1):
    d=i*1.62
    a=cq.Vector(-16,-13.8+d,10.5+i*1.2);b=cq.Vector(-20.5,-12+d,11.2+i*1.2)
    unit=(b-a).normalized()
    start=a+unit*.3
    sleeve=cq.Solid.makeCylinder(.72,3.75,start,unit).cut(cq.Solid.makeCylinder(.46,3.95,start-unit*.1,unit))
    extra('shrink'+str(i),'Battery splice sleeve '+str(i+1),'SHOP1','Wiring',control,sleeve,[-28,0,30],5,'Nominal shrunk insulation on a battery-adapter splice. Gauge joint diameter, support and isolation.','#70736c')
# Alternate service cable is shown as an unplugged external gauge and excluded from the fitted bill.
usb=box(-63,-6,16.45,17,12,6.5).fuse(box(-46,-4.1,18.35,6,8.2,2.7))
extra('usbGauge','USB data plug gauge','USB1','Wiring',control,usb,[-35,0,0],6,'External fixture modeled for plug approach only. Excluded from closed-unit mass, coverage and interference totals.','#7c8986','usb','rev-E/scripts/gauges.py')
def mesh(s):
    vv,tt=s.tessellate(.07,.20)
    v=np.rint(np.array([p.toTuple() for p in vv])*100).astype('<i2')
    t=np.asarray(tt,dtype='<u4')
    def pack(a):return base64.b64encode(zlib.compress(a.tobytes(),7)).decode('ascii')
    return {'v':pack(v),'t':pack(t)}
import zlib
for k,r in rows.items():
    print('mesh',k,flush=True)
    path=cache/(k+'.mesh.json')
    if r['added'] or k=='reel1' or not path.exists():path.write_text(json.dumps(mesh(shapes[k]),separators=(',',':')),encoding='utf8')
data=[dict(r,**json.loads((cache/(k+'.mesh.json')).read_text())) for k,r in rows.items()]
(TMP/'meshes.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
(HERE/'parts.json').write_text(json.dumps(list(rows.values()),indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(HERE/'routes.json').write_text(json.dumps(nets,indent=2)+'\n',encoding='utf8')
if args.check:
    from check_review import verify
    verify(rows,shapes,HERE,TMP)
# Compact, exact BREP supplement. For CAD use place over the original STEP at shared world origin.
ass=cq.Assembly(name='Rev_F_inspection_additions')
for k,r in rows.items():
    if r['added'] and r['option'] not in ('alt','drawing','usb'):ass.add(shapes[k],name=k,color=cq.Color(r['color']))
step=TMP/'added-hardware.step';ass.export(str(step))
with step.open('rb') as src,gzip.open(HERE/'additional-hardware.step.gz','wb') as dst:shutil.copyfileobj(src,dst)
print('Finished',len(rows),'selectable entries',flush=True)

if args.full_step:
    full=cq.Assembly(name='Thai_Waters_Rev_F_dressed_review')
    for k,r in rows.items():
        if r['option'] not in ('alt','drawing','usb'):full.add(shapes[k],name=k,color=cq.Color(r['color']))
    step=TMP/'full-dressed.step'
    full.export(str(step))
    with step.open('rb') as src,gzip.open(TMP/'Riffle-Rev-F-dressed-assembly.step.gz','wb',compresslevel=6) as dst:shutil.copyfileobj(src,dst)

