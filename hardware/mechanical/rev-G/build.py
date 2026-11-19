"""Build and check the Rev G fit print against the tagged Rev F dressed assembly."""
from pathlib import Path
import argparse,gzip,hashlib,itertools,json,shutil,sys
import cadquery as cq
from geometry import key_keeper,bridge,bridge_screw,CX,CY,Z,PLUG,box,housing,factory_lead,adapter_lead
HERE=Path(__file__).resolve().parent
REF=HERE.parent/'rev-F/review'
sys.path.insert(0,str(REF))
from check_review import bounds,candidate,mating,THRESHOLD
p=argparse.ArgumentParser()
p.add_argument('--exports',required=True,type=Path)
p.add_argument('--work',required=True,type=Path)
p.add_argument('--quick',action='store_true',help='Only check changed components and output the diagnostic ledger')
args=p.parse_args()
OUT=args.exports.resolve();WORK=args.work.resolve();WORK.mkdir(exist_ok=True,parents=True)
def obj(file):return json.loads(file.read_text(encoding='utf-8-sig'))
def write(file,data):file.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
archive=OUT/'Riffle-Rev-F-dressed-assembly.step.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='5e88fcf92ef88b7c2efd1952591d11554c6245bb30c0e6097e9b7ea227e93ee2'
cache=WORK/'solids'
if len(list(cache.glob('*.brep')))!=76:
    cache.mkdir(exist_ok=True)
    with gzip.open(archive,'rb') as f,(WORK/'baseline.step').open('wb') as g:shutil.copyfileobj(f,g)
    for node in cq.Assembly.load(str(WORK/'baseline.step')).children:
        node.obj.moved(node.loc).exportBrep(str(cache/(node.name+'.brep')))
rows={r['id']:r for r in obj(REF/'parts.json')}
shapes={f.stem:cq.Shape.importBrep(str(f)) for f in cache.glob('*.brep')}
assert len(shapes)==76
old=shapes['Housing']
shapes['Housing']=housing(old)
shapes['Retainer']=key_keeper(shapes['Retainer'])
shapes['Keeper screw']=shapes['Keeper screw'].translate((-14.9,-.95,0))
assert shapes['Housing'].isValid() and len(shapes['Housing'].Solids())==1
shapes['cellAlt']=cq.importers.importStep(str(REF/'inputs/Adafruit-258.step')).val().translate((CX,CY,Z))
shapes['cellDrawing']=box(CX-35.3/2,CY-62.3/2,Z,35.3,62.3,5.3)
shapes['Cell']=shapes['Cell'].translate((CX+11.5,CY,0))
x,y,z=PLUG
shapes['packplug']=box(x,y,z,5.5,4,3.2)
shapes['ph']=box(x+5.5,y,z,7.8,4,3.2)
for k,part,ref,shape in [('bridge','Lift-out wire bridge','P2',bridge()),('tieS1','Bridge screw, left','H9',bridge_screw(-31.85)),('tieS2','Bridge screw, right','H9',bridge_screw(11.1))]:
    shapes[k]=shape
    rows[k]=dict(rows['ph'],id=k,name=part,ref=ref,stage=4,source='rev-G/geometry.py',color='#8ba69b' if k=='bridge' else '#a5aaa6',
                 note='Lift out before installing or removing the inert gauge. Use two M2 × 4 fasteners in the outboard blind pilots. Insulating tape loops go through the four slots.')
routes={}; variant_keys={}
for variant,cell in [('catalog','Cell'),('alt','cellAlt'),('drawing','cellDrawing')]:
    keys={cell}
    for i in range(2):
        key='pack'+str(i) if variant=='catalog' else variant+'Tail'+str(i)
        shapes[key],routes[key]=factory_lead(variant,i);keys.add(key)
        rows[key]=dict(rows['pack'+str(i)],id=key,batteryVariant=variant,source='rev-G/geometry.py',note='100 mm total factory lead including modeled supplier stub where applicable. Clearance and bend limits require an inert harness trial.')
    variant_keys[variant]=keys
for i in range(2):
    shapes['batt'+str(i)],shapes['shrink'+str(i)],routes['batt'+str(i)]=adapter_lead(i)
rows['Housing'].update(name='Rev G battery-bay housing',kind='Rev G fit-print CAD',source='rev-G/geometry.py',note='Revised battery fences, mounting lands, lead turnaround and PH adapter saddle.')
rows['Cell']['note']='Catalog envelope on the new datum. Select drawing maximum or supplier STEP to change both pack and leads.'
for key in ['ph','packplug','batt0','batt1','shrink0','shrink1','Cell','cellAlt','cellDrawing']:
    rows[key]['source']='rev-G/geometry.py with '+rows[key]['source']
rows['ph']['note']='W2 adapter half on the outboard saddle with 0.25 mm mounting allowance; mate from the left.'
changed=set().union(*variant_keys.values(),routes,{'ph','packplug','Housing','shrink0','shrink1','Retainer','Keeper screw','bridge','tieS1','tieS2'})
def coll(s,t,bins):
    v=0
    for u,bu in bins[s]:
        for w,bw in bins[t]:
            if candidate(bu,bw):v+=max(0.,u.intersect(w).Volume())
    return v
bb={k:bounds(v) for k,v in shapes.items()}
bins={k:[(s,bounds(s)) for s in v.Solids()] for k,v in shapes.items()}
all_special=set.union(*variant_keys.values())
common=set(shapes)-all_special
volumes={}; report={}
def volume(a,b):
    k=tuple(sorted([a,b]))
    if k not in volumes:volumes[k]=coll(a,b,bins) if candidate(bb[a],bb[b]) else 0.
    return volumes[k]
for variant,keys in variant_keys.items():
    ids=sorted(common|keys);hits=[];total=0;eligible=0
    for a,b in itertools.combinations(ids,2):
        if not (a in changed or b in changed or (not args.quick and (rows[a]['added'] or rows[b]['added']))):continue
        total+=1
        if not candidate(bb[a],bb[b]):continue
        eligible+=1;v=volume(a,b)
        if v<=THRESHOLD:continue
        intended=mating(a,b,rows) or {a,b}=={'Housing','Keeper screw'} or ('Housing' in (a,b) and (a.startswith('tieS') or b.startswith('tieS')))
        if a.startswith(('altTail','drawingTail')) or b.startswith(('altTail','drawingTail')):
            intended=(a=='packplug' or b=='packplug')
        if 'Housing' in (a,b) and not intended:
            # A pre-existing housing interface is accepted only when the same physical
            # volume was present before and the revised housing adds no material there.
            other=b if a=='Housing' else a
            if other not in changed:
                prev=sum(max(0.,old.intersect(s).Volume()) for s,sb in bins[other] if candidate(bb['Housing'],sb))
                if abs(v-prev)<.002:intended=True
        hits.append(dict(first=a,second=b,mm3=round(v,4),status='mating or inherited contact' if intended else 'resolve'))
    report[variant]=dict(pair_tests=total,bbox_candidates=eligible,intersections=hits)
    print(variant,total,[h for h in hits if h['status']=='resolve'],flush=True)
write(WORK/'collisions.json',report)
if args.quick:sys.exit()
if any(h['status']=='resolve' for r in report.values() for h in r['intersections']):raise ValueError('Unresolved interference')
from qualification import run
qualification=run(shapes)
for key in ('Keeper screw','tieS1','tieS2'):
    screw=shapes[key]
    bb_s=bounds(screw)
    # Only shaft penetration below the head in the pilot is an intentional interface.
    shaft_top=17.65 if key=='Keeper screw' else 9.55
    tool=box(bb_s[0]-.1,bb_s[2]-.1,shaft_top+.001,bb_s[1]-bb_s[0]+.2,bb_s[3]-bb_s[2]+.2,9)
    qualification.setdefault('screw_outside_pilot_overlap_mm3',{})[key]=round(max(0.,shapes['Housing'].intersect(screw.intersect(tool)).Volume()),5)
print('Acceptance',qualification,flush=True)
write(WORK/'qualification.json',qualification)
assert all(v<=THRESHOLD for r in qualification['insertion_sweep_overlap_mm3'].values() for v in r.values())
assert all(v<=THRESHOLD for k in ('clearance_box_intersections_mm3','screw_outside_pilot_overlap_mm3') for v in qualification[k].values())
assert min(qualification['wall_section_mm'].values())>=1.45

assert all(max(r['housing_mm3'],r['keeper_mm3'])<=THRESHOLD for r in qualification['key_stroke'])
assert all(max(r['shell_mm3'],r['bridge_mm3'])<=THRESHOLD for r in qualification['rigid_placement_corners'])
from deliver import export
export(HERE,REF,WORK,OUT,rows,shapes,changed,report,qualification,routes)

