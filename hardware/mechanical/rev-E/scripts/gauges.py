from geometry import *
import json,csv
def shift(s,dx=0,dy=0,dz=0):return s.translate((dx,dy,dz))
def cz(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(0,0,1))
def tube(p,q,r):
 v=cq.Vector(*q)-cq.Vector(*p);return cq.Solid.makeCylinder(r,v.Length,cq.Vector(*p),v.normalized())
def assembly(seq):
 return [(name,s,bb(s)) for name,s in seq]
parts=assembly([(labels[i],H if i==0 else D[i]) for i in range(11)]+[(f'A1.{i:03d}',s) for i,s in enumerate(A)]+[(f'A2.{i:02d}',s) for i,s in enumerate(E)])
result=[]
def chk(test,pose,name,s,fixed):
 sb=bb(s);hits=[];cnt=0
 for n,t,tb in fixed:
  if possible(sb,tb):
   v=s.intersect(t).Volume();cnt+=1
   if v>.002:hits.append((n,round(v,5)))
 result.append((test,pose,name,len(fixed),cnt,json.dumps(hits)))
# Check 4 board screws and tool access. Thread inserts intentionally engaged; omit only those four mating holes.
for x in [-36,36]:
 for y in [-24.25,24.25]:
  name=f'H1 ({x}, {y})'
  h=cz(x,y,9.4,2.2,1.6).fuse(cz(x,y,11,1,8))
  chk('Screw installed',0,name,h,[p for p in parts if p[0] not in [f'A1.{i:03d}' for i in range(1,5)]])
  chk('Rear driver axial corridor',0,name,cz(x,y,-8,1.8,17.4),parts)
# Two hinge shims around pivot Z. Face is at Z=14.8 +/- 2.3.
for z in [12.2,17.1]:
 q=cz(53.6,7.8,z,2.1,.3).cut(cz(53.6,7.8,z-.1,1.04,.6))
 chk('Hinge shim nominal',z,'H3 OD 4.2 x 0.30',q,parts)
# Geometric gauges only. A received plug and completed harness still need to be measured.
usb=box(-63,-6,16.45,17,12,6.5).fuse(box(-46,-4.1,18.35,6,8.2,2.7))
chk('USB cable approach',0,'12 x 6.5 overmold / 6 metal projection',usb,[parts[0],parts[1]])
# Solder pads face the floor. Keep the four loose ends and the bundle in the lower half of the bay.
# Corridor envelopes deliberately stop short of mated parts; these are reservations, not supplier harness CAD.
for name,s in [
 ('A2 solder and fanout zone',box(32,-7.4,6.5,7.47,12.35,4)),
 ('W1 bundle along right bay',tube((30,0,9),(30,20,12),1.6)),
 ('W1 toward header',tube((30,20,12),(18,21.7,12.5),1.6)),
 ('J8 right-angle plug envelope',box(10,19.9,11.5,10.4,6,4.39)),
 ('Battery adapter splice zone',box(-18,-15,9.3,20,6,4.5)),
 ('Speaker lead corridor',tube((-37,12,11.3),(-32,21,14.5),1.2))]:
  chk('Wiring space reservations',0,name,s,parts)
# Tolerance sensitivities. These are chosen relative errors, not supplier tolerance specifications.
for d in [.20,.40,.50]:
 chk('PCB datum closes in X',d,'A2 PCB translated toward A1',shift(E[0],dx=-d),parts[11:11+546])
for d in [.15,.25,.30]:
 chk('Display height closes in Z',d,'Display stack toward bezel',shift(A[0],dz=d),[parts[1]])
for d in [.25,.40,.50]:
 chk('Cell shifts laterally',d,'Bare cell toward right fence',shift(D[9],dx=d),[parts[0]])
# Entry of the sensor board before moving along X onto its pins.
for h in np.arange(0,24.01,1.):
 for i,s in enumerate(E):chk('A2 lower into empty bay',h,f'A2.{i:02d}',shift(s,-8,0,h),[parts[0],*parts[2:9]])
for h in np.arange(0,16.01,.5):
 for i in [2,3,4,6,7,8]:chk('Fit rotor before collar',h,labels[i],shift(D[i],dx=h),[parts[0]])
for h in np.arange(0,9.01,.5):
 chk('Slide collar onto shaft',h,'Collar',shift(D[5],dx=-h),[parts[0],parts[2],parts[8]])
with (ROOT/'gauges.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(('test','pose_mm','part','obstacles','narrow_phase','hits_and_mm3'));w.writerows(result)
print([r for r in result if r[-1]!='[]'][:25],flush=True)
