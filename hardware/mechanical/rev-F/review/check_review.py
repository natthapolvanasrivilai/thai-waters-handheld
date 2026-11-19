"""Nominal mechanical interference and alternative cell studies. All lengths in mm."""
import csv,json,itertools
import cadquery as cq

THRESHOLD=.002
def bounds(s):
    b=s.BoundingBox();return [getattr(b,x) for x in ('xmin','xmax','ymin','ymax','zmin','zmax')]
def candidate(a,b):return all(a[i]<b[i+1]-.000001 and b[i]<a[i+1]-.000001 for i in (0,2,4))
def intersect(a,b,bb1,bb2):
    if not candidate(bb1,bb2):return 0.
    return max(0.,a.intersect(b).Volume())
MATES={
    'hdrPins':{'A1-J8','J8plug'},'J8plug':{'A1-J8'},'packplug':{'ph'},'j7plug':{'A1-J7'},'j9plug':{'A1-J9'},
    'H5':{'reel1','Grip'},'motor':{'adhH'},'drvBoard':{'adhH','drvParts'},'drvParts':{'adhH'},
}
# Electrical terminal and support interfaces stay in the ledger, flagged for bench confirmation.
def mating(a,b,rows):
    if b in MATES.get(a,set()) or a in MATES.get(b,set()):return True
    if (a.startswith('H1-') and b=='A1-mounts') or (b.startswith('H1-') and a=='A1-mounts'):return True
    for x,y in ((a,b),(b,a)):
        if x.startswith('w1') and y in ('A2-pcb','J8plug'):return True
        if x.startswith('wh') and (y.startswith('w1') and y[2:]==x[2:] or y=='drvBoard'):return True
        if x.startswith('wm') and y in ('motor','drvBoard'):return True
        if x.startswith('w3') and y in ('Trimmed terminals','A1-k3'):return True
        if x.startswith('pack') and y in ('Cell','packplug'):return True
        if x.startswith('batt') and y in ('ph','j7plug'):return True
        if x.startswith('spk') and y in ('Speaker','j9plug'):return True
    return False
def verify(rows,shapes,out,tmp):
    solidbins={k:[(s,bounds(s)) for s in v.Solids()] for k,v in shapes.items()}
    bbox={k:bounds(s) for k,s in shapes.items()}
    tested=0;candidates=0;hits=[]
    for a,b in itertools.combinations(shapes,2):
        if {a,b}.intersection({'cellAlt','cellDrawing','usbGauge'}):continue
        if not (rows[a]['added'] or rows[b]['added']):continue
        tested+=1
        if not candidate(bbox[a],bbox[b]):continue
        volume=0
        for s,sb in solidbins[a]:
            for t,tb in solidbins[b]:
                if not candidate(sb,tb):continue
                candidates+=1;volume+=intersect(s,t,sb,tb)
        if volume>THRESHOLD:
            hits.append(dict(first=a,second=b,overlap_mm3=round(volume,4),
                             status='expected interface; gauge' if mating(a,b,rows) else 'resolve'))
    print('Dressed assembly',tested,candidates,hits,flush=True)
    polys=shapes['cellAlt']; axis=(-11.5,0,3.6)
    # Occupied geometry on the full option configuration. Exclude the nominal pouch and its own leads.
    omitted={'cellAlt','cellDrawing','usbGauge','Cell','pack0','pack1'}
    poses=[(0,0,0),(180,0,0),(0,1.5,0),(180,1.5,0),(0,-1.5,0),(0,1.5,-1.5),(90,0,0),(-90,0,0)]
    results=[]
    for rot,dx,dy in poses:
        moved=polys.rotate(axis,(axis[0],axis[1],axis[2]+1),rot).translate((dx,dy,0))
        bo=bounds(moved);coll=[]
        for k in shapes:
            if k in omitted or not candidate(bbox[k],bo):continue
            vol=sum(intersect(moved,s,bo,sb) for s,sb in solidbins[k])
            if vol>THRESHOLD:coll.append({'part':k,'mm3':round(vol,3)})
        results.append(dict(rotation_deg=rot,dx_mm=dx,dy_mm=dy,intersections=coll))
        print('Cell pose',rot,dx,dy,coll,flush=True)
    # Deliberately exclude flexible leads and SHOP1 pads. Keep these explicit during bench work.
    keepout=cq.Solid.makeBox(38,64,7.3,cq.Vector(-29,-32,3.1))
    kb=bounds(keepout);cutlist=[]
    for k in shapes:
        if k in omitted or rows[k]['kind']=='Proposed routing' or k=='adhH':continue
        v=sum(intersect(keepout,s,kb,sb) for s,sb in solidbins[k])
        if v>THRESHOLD:cutlist.append(dict(part=k,mm3=round(v,3)))
    specs=[]
    for name,width,long,thick in [('minimum',34.7,61.7,4.7),('nominal',35,62,5),('maximum',35.3,62.3,5.3)]:
        s=cq.Solid.makeBox(width,long,thick,cq.Vector(-11.5-width/2,-long/2,3.6))
        b=bounds(s)
        collisions=[{'part':k,'mm3':round(v,3)} for k in shapes if k not in omitted
                    and (v:=sum(intersect(s,t,b,tb) for t,tb in solidbins[k]))>THRESHOLD]
        specs.append(dict(size=name,dimensions_mm=[width,long,thick],intersections=collisions))
    res={'source':'OpenCascade B-Rep Boolean common volume','threshold_mm3':THRESHOLD,'pair_tests':tested,
         'candidate_solid_pairs':candidates,'intersections':hits,'cell_tests':results,'drawing_body_tests':specs,
         'cell_window_study':{'bounds_mm':kb,'affected_rigid_parts':cutlist,
         'status':'Study envelope; wall thickness, restraint, swelling allowance, handling, bending and revised harness remain to be validated.'}}
    (out/'placement-results.json').write_text(json.dumps(res,indent=2)+'\n',encoding='utf8')
    return res
