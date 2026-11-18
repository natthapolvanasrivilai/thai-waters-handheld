from geometry import *
import itertools,json
def trigext(a,b):
 # extrema of a*cos(t) + b*sin(t) on [0,pi/2].
 theta=math.atan2(b,a); angles=[0,math.pi/2]+[s for s in [theta,theta+math.pi,theta-math.pi] if 0<s<math.pi/2]
 return [a*math.cos(t)+b*math.sin(t) for t in angles]
def enclosing(s,hinged):
 b=bb(s); xx=[];yy=[]
 for x,y in itertools.product(b[:2],b[2:4]):
  dx=x-53.6;dy=y-7.8
  xx += [53.6+t for t in trigext(dx,-dy)] if hinged else [x]
  yy += [7.8+t for t in trigext(dy,dx)] if hinged else [y]
 r=math.hypot(max(map(abs,yy)),max(abs(b[4]-14.8),abs(b[5]-14.8)))
 return min(xx)-.0001,max(xx)+.0001,r+.0001
def env(x,u,r):return cx(x,0,14.8,r,u-x)
# Tight engineering envelopes of all rotor tiers; verify containment on the actual STEP.
tiers=[(43.5999,49.0001,4.5501),(49-.0001,57.5001,13.0501)]
envelopes=[('Rotor tiers',env(*tiers[0]).fuse(env(*tiers[1])))]
for i in [3,4,6,7]:
 envelopes.append((labels[i],env(*enclosing(D[i],i in [3,4,7]))))
for i,r in [(5,6.6001),(8,3.0001)]:
 b=bb(D[i]);envelopes.append((labels[i],env(b[0]-.0001,b[1]+.0001,r)))
fixed=[('Housing',H),('Bezel',D[1]),('Cell',D[9]),('Speaker',D[10])]+[(f'A2.{i:02d}',s) for i,s in enumerate(E)]+[(f'A1.{i:03d}',s) for i,s in enumerate(A)]
fi=[(n,s,bb(s)) for n,s in fixed];out=[]
for n,s in envelopes:
 i=2 if n=='Rotor tiers' else labels.index(n)
 excess=D[i].cut(s).Volume();hits=[]
 for m,t,b in fi:
  if possible(bb(s),b):
   v=s.intersect(t).Volume()
   if v>.002:hits.append((m,v))
 out.append(dict(moving=n,verified_original_outside_mm3=excess,obstacles=len(fi),envelope_hits=hits))
(ROOT/'continuous.json').write_text(json.dumps(out,indent=2));print(out)

