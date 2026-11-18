from geometry import *
import csv,json,itertools,sys
from collections import Counter
mode=sys.argv[1]
rows=[];hits=[]
def write(stage,pose,n,m,status,vol=0):
 rows.append((stage,pose,n,m,status,round(vol,5)))
 if vol>.002:hits.append(rows[-1])
def dump():
 with (ROOT/(mode+'.csv')).open('w',newline='') as f:
  w=csv.writer(f);w.writerow(('test','pose','moving','fixed','classification','overlap_mm3'));w.writerows(rows)
 print(mode,len(rows),len(hits),hits[:18],flush=True)
def cacheitem(n,s):return n,s,bb(s)
def pair(stage,pose,a,b):
 n,s,ab=a;m,t,tb=b
 if not possible(ab,tb):return write(stage,pose,n,m,'separate bounds')
 vol=s.intersect(t).Volume()
 return write(stage,pose,n,m,'INTERFERENCE' if vol>.002 else 'within 0.002 mm3',vol)
# Partition the complex housing once to skip empty interior. Individual tiles are exact intersections.
def partition(shape):
 xs=[-51,-47,-39.2,-32.5,32.5,39.2,46.9,60]
 ys=[-35,-27.6,-20.8,20.8,27.6,35]
 zs=[-.5,5,17.0001,28]
 pieces=[]
 for x,u in zip(xs,xs[1:]):
  for y,v in zip(ys,ys[1:]):
   for z,w in zip(zs,zs[1:]):
    obj=shape.intersect(box(x,y,z,u-x,v-y,w-z))
    if obj.Volume()>.000001:pieces.append(cacheitem('Revised housing',obj))
 return pieces
# Fast clearance certificate: one BRep check for a known empty orthogonal region.
empty=(-39.2,39.2,-27.52,27.52,17.00003,61)
void=box(empty[0],empty[2],empty[4],empty[1]-empty[0],empty[3]-empty[2],empty[5]-empty[4])
assert H.intersect(void).Volume()<.000001
def invoid(b):return all(b[i]>=empty[i] and b[i+1]<=empty[i+1] for i in [0,2,4])
printed=[cacheitem(n,H if i==0 else D[i]) for i,n in enumerate(labels)]
waves=[cacheitem(f'A1.{i:03d}',s) for i,s in enumerate(A)]
sensors=[cacheitem(f'A2.{i:02d}',s) for i,s in enumerate(E)]
def matrices():
 for a,b in itertools.combinations(printed,2):pair('Rev E installed',0,a,b)
 for a in sensors:
  pair('Rev D regression',0,a,cacheitem('D housing',D[0]))
 for a in waves+sensors:
  for b in printed:
   if b[0]=='Housing' and invoid(a[2]):write('Rev E installed',0,a[0],b[0],'certified empty region')
   else:pair('Rev E installed',0,a,b)
 for a in waves:
  for b in sensors:pair('Rev E installed',0,a,b)
 dump()
def metric(n,left,right):
 choices=sorted([(boundgap(a[2],b[2]),i,j) for i,a in enumerate(left) for j,b in enumerate(right)])
 best=float('inf')
 for d,i,j in choices:
  if d>=best:break
  dist=left[i][1].distance(right[j][1])
  if dist<best:best=dist;ident=(left[i][0],right[j][0])
 return (n,round(best,4),*ident)
def measurements():
 pairs=[('Controller to sensor',waves,sensors),('Display surface to bezel',[waves[0]],[printed[1]]),('Controller to cell',waves,[printed[9]]),('Controller to speaker',waves,[printed[10]]),('Magnet face to AS5600 body',[printed[8]],[sensors[16]]),('Shaft to sensor assembly',[printed[2]],sensors),('Sockets to revised housing',[sensors[6],sensors[7]],[printed[0]]),('Battery to lateral shell/fences',[printed[9]],[printed[0]]),('Speaker to shell',[printed[10]],[printed[0]]),('Controller substrate to encoder substrate',[waves[5]],[sensors[0]])]
 out=[metric(*p) for p in pairs]
 (ROOT/'clearances.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
def path():
 # For translation certify through the full stroke if the swept AABB misses the obstacle,
 # otherwise use a conservative bounding prism, then exact BRep at the listed sample pitch.
 def stroke(stage,items,against,axis,length,pitch):
  for n,s,bb0 in items:
   swept=list(bb0);swept[2*axis+1]+=length
   for m,t,tb in against:
    if not possible(swept,tb) or (m=='Housing' and invoid(swept)):
     write(stage,'full stroke',n,m,'certified swept bounds');continue
    env=box(swept[0],swept[2],swept[4],swept[1]-swept[0],swept[3]-swept[2],swept[5]-swept[4])
    if env.intersect(t).Volume()<.000001:
     write(stage,'full stroke',n,m,'certified empty swept box');continue
    for k in np.arange(0,length+.0001,pitch):
     move=[0.,0.,0.];move[axis]=float(k)
     shifted=s.translate(tuple(move)) if k else s
     pair(stage,round(k,3),cacheitem(n,shifted),(m,t,tb))
 stroke('A1 insert from display side',waves,[printed[0],*printed[2:],*sensors],2,16,.5)
 # A2 is slipped onto the pins from the vacant controller bay before installing A1.
 flipped=[cacheitem(n,s.mirror('YZ')) for n,s,_ in sensors]
 obs=[cacheitem(n,s.mirror('YZ')) for n,s,_ in [printed[0],*printed[2:9]]]
 stroke('A2 seat from inboard',flipped,obs,0,8,.5)
 stroke('Bezel closure',[printed[1]],[printed[0],*printed[2:],*sensors,*waves],2,5,.5)
 dump()
def motion():
 moving=[2,3,4,5,6,7,8]
 # An enclosing cylinder covers every crank angle, including the hinge screw, collar and magnet.
 # Qualify all three fold parts against stationary carrier in increments; use rotationally invariant envelopes separately.
 for deg in range(0,91,5):
  for i in [3,4,7]:
   a=cacheitem(labels[i],fold(D[i],deg))
   for b in [printed[j] for j in (0,1,2,5,6,8)]+sensors:
    pair('Grip deployment',deg,a,b)
 for angle in range(0,360,10):
  for f in (0,90):
   for i in moving:
    a=cacheitem(labels[i],rot(fold(D[i],f) if i in [3,4,7] else D[i],angle))
    for b in [printed[0],printed[1],*sensors]:pair('Reel turn fold '+str(f),angle,a,b)
 dump()
if mode=='static':matrices()
if mode=='path':path()
if mode=='motion':motion()
if mode=='metric':measurements()
