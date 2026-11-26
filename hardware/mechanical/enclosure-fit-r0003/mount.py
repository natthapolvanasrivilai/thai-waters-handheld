"""USB lamp shelf and removable bracket. All coordinates are installed millimetres."""
from pathlib import Path
import cadquery as cq
import json
import math
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/"electronics/case-board-r0001"
V=cq.Vector
def box(x,y,z,X,Y,Z):
    return cq.Solid.makeBox(X-x,Y-y,Z-z,V(x,y,z))
def cyl(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,V(x,y,z))
# Broad pads keep the printed beam flat during removal. Fit the shelf screw before A1.
PINS=((-40.4,18.),(-44.6,18.))
def geometry():
    parent=cq.importers.importStep(str(BASE/"housing.step")).val()
    cut=box(-43.52,-3.04,10.80,-40.18,3.8,14.85)
    shell=parent.cut(cut)
    sled=box(-43.42,-2.85,10.4,-39.4,3.52,11.50)
    sled=sled.fuse(box(-41.26,-2.85,11.49,-39.4,2.9,12.25),
                   box(-43.04,2.42,11.49,-41.43,3.52,13.75),
                   box(-43.42,-2.85,11.49,-42.46,-1.75,12.20),
                   box(-43.42,1.75,11.49,-42.46,2.9,12.20),
                   box(-41.10,-2.85,10.4,-39.16,18.1,12.0),
                   box(-46.55,15.55,10.4,-40.35,20.45,12.0))
    posts=[]
    for x,y in PINS:
        outer=cyl(x,y,2.12,2.45,8.28)
        post=outer.cut(cyl(x,y,5.0,.82,5.7)) if (x,y)==PINS[1] else outer
        posts.append(post)
        sled=sled.fuse(cyl(x,y,10.4,2.45,1.6))
        if (x,y)==PINS[1]: sled=sled.cut(cyl(x,y,10.30,1.15,2.0))
    posts.append(box(-46.55,20.70,2.1,-39.8,22.25,12.2))
    shell=shell.fuse(*posts).clean()
    sled=sled.clean()
    assert shell.isValid() and len(shell.Solids())==1 and sled.isValid() and len(sled.Solids())==1
    from closure import features
    bosses,reliefs,_,_=features()
    shell=shell.fuse(*bosses).cut(*reliefs).clean()
    assert shell.isValid() and len(shell.Solids())==1
    return parent,shell,sled,posts,cut
def b(s):
    q=s.BoundingBox()
    return [getattr(q,k) for k in ("xmin","xmax","ymin","ymax","zmin","zmax")]
def near(a,c,margin=.01):
    return all(a[i]<c[i+1]+margin and c[i]<a[i+1]+margin for i in (0,2,4))
if __name__=="__main__":
    import sys
    cache=Path(sys.argv[1]);parent,shell,sled,posts,cut=geometry()
    for n,s in [('shell',shell),('sled',sled)]:
        s.exportBrep(str(HERE/(n+'.brep')))
    parts=json.loads((HERE.parent/'TW-A-0001-R0017/installed-step.json').read_bytes())['components']
    for k,s in [('sled',sled),('posts',cq.Compound.makeCompound(posts))]:
        for name,info in parts.items():
            if name in ('Housing','A4-bond','A4-spacers','A4-integration','A5-bond','A5-spacers','A5-power'):continue
            if near(b(s),info['bounds_mm'],.6):
                t=cq.Shape.importBrep(str(cache/(name+'.brep')))
                print(k,name,round(s.distance(t),3),round(s.intersect(t).Volume(),3),flush=True)
    print('seated shell intersection',[(b(q),q.Volume()) for q in shell.intersect(sled).Solids()],flush=True)
