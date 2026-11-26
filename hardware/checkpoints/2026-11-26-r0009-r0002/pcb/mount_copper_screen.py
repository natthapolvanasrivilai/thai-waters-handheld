"""Static, conservative nominal copper-to-NPTH and outline screen, not native DRC."""
import hashlib, json, math
from layout import HERE, items, one, parse
from collections import defaultdict

def xy(a): return tuple(map(float,a[1:3]))
def dist(a,b): return math.dist(a,b)
def seg(p,a,b):
    d=tuple(y-x for x,y in zip(a,b))
    l=sum(x*x for x in d)
    t=min(1,max(0,sum((p[i]-a[i])*d[i] for i in range(2))/l)) if l else 0
    return dist(p,tuple(a[i]+t*d[i] for i in range(2)))
def rot(p,d):
    c,s=math.cos(math.radians(d)),math.sin(math.radians(d))
    return (c*p[0]+s*p[1],-s*p[0]+c*p[1])
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def outline_gap(p):
    # Analytic signed distance to rounded rectangle, positive inside.
    cx,cy=109.7,115.1
    r=1.5
    x,y=abs(p[0]-cx)-(16.2-r),abs(p[1]-cy)-(17.9-r)
    return r-math.hypot(max(0,x),max(0,y))-min(0,max(x,y))

def read_board(path, control=False):
    b=parse(path)
    assert len(items(b,'gr_line'))==4 and len(items(b,'gr_arc'))==4
    pts=[xy(one(g,k)) for t in ('gr_line','gr_arc') for g in items(b,t) for k in ('start','end')]
    assert tuple(min(a[i] for a in pts) for i in range(2)) == (93.5,97.2)
    assert tuple(max(a[i] for a in pts) for i in range(2)) == (125.9,133.0)
    assert all(abs(outline_gap(p))<1e-5 for p in pts)
    assert not items(b,'zone') and not items(b,'arc')
    holes=[(xy(one(g,'center')),dist(xy(one(g,'center')),xy(one(g,'end')))) for g in items(b,'gr_circle')]
    assert len(holes)==2 and all(abs(r-1.15)<1e-8 for _,r in holes)
    copper=[]
    for t in items(b,'segment'):
        a,z=xy(one(t,'start')),xy(one(t,'end')); r=float(one(t,'width')[1])/2
        tag=f'track {one(t,"net")[1]} {a} → {z}'
        copper.append((tag,[one(t,'layer')[1]],min(outline_gap(a),outline_gap(z))-r,
                       lambda p,a=a,z=z,r=r:seg(p,a,z)-r))
    for v in items(b,'via'):
        a=xy(one(v,'at'));r=float(one(v,'size')[1])/2
        copper.append((f'via {one(v,"net")[1]} {a}',one(v,'layers')[1:],outline_gap(a)-r,
                       lambda p,a=a,r=r:dist(a,p)-r))
    for f in items(b,'footprint'):
        fpos=one(f,'at'); origin=xy(fpos); angle=float(fpos[3]) if len(fpos)>3 else 0
        ref=next(p[2].strip('"') for p in items(f,'property') if p[1]=='"Reference"')
        for p in items(f,'pad'):
            assert p[3]=='roundrect'
            loc=one(p,'at'); center=add(origin,rot(xy(loc),angle)); pa=float(loc[3]) if len(loc)>3 else 0
            sx,sy=xy(one(p,'size')); x,y=sx/2,sy/2
            rr=float(one(p,'roundrect_rratio')[1])*min(sx,sy)
            assert 0<=rr<=min(x,y)
            corners=[add(center,rot((u*w,v*h),pa)) for u,v in ((1,1),(1,-1),(-1,1),(-1,-1)) for w,h in [(x-rr,y-rr)]]
            def point_to_pad(q,center=center,pa=pa,x=x,y=y,rr=rr):
                u,v=rot((q[0]-center[0],q[1]-center[1]),-pa)
                U,V=abs(u)-(x-rr),abs(v)-(y-rr)
                return math.hypot(max(0,U),max(0,V))+min(0,max(U,V))-rr
            layer=one(p,'layers')[1:]
            copper.append((f'pad {ref}.{p[1].strip(chr(34))}',layer,min(map(outline_gap,corners))-rr,point_to_pad))
    assert len(copper)==426
    if control:
        c=holes[0][0]
        copper.append(('injected overlap',['"F.Cu"'],outline_gap(c)-.2,lambda q:dist(q,c)-.2))
    out={'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'copper_features':len(copper),'edge_gap_mm':{},'mount_holes':[]}
    for layer in ['"F.Cu"','"B.Cu"']:
        group=[c for c in copper if layer in c[1] or '"*.Cu"' in c[1]]
        row=min(group,key=lambda c:c[2])
        out['edge_gap_mm'][layer.strip('"')]=dict(gap=round(row[2],6),feature=row[0])
    for pos,r in holes:
        entry=dict(xy_mm=pos,radius_mm=r,layers={})
        for layer in ['"F.Cu"','"B.Cu"']:
            group=[c for c in copper if layer in c[1] or '"*.Cu"' in c[1]]
            row=min(group,key=lambda c:c[3](pos))
            radial=row[3](pos)
            entry['layers'][layer.strip('"')]=dict(nearest_copper_radial_mm=round(radial,6),bore_to_copper_mm=round(radial-r,6),feature=row[0])
        out['mount_holes'].append(entry)
    return out

if __name__=='__main__':
    src=HERE/'case-board.kicad_pcb'
    a=read_board(src)
    assert all(v['gap']>0 for v in a['edge_gap_mm'].values())
    assert all(v['bore_to_copper_mm']>0 for h in a['mount_holes'] for v in h['layers'].values())
    bad=read_board(src,True)
    assert bad['mount_holes'][0]['layers']['F.Cu']['bore_to_copper_mm']<0
    print(json.dumps(a,indent=2))
