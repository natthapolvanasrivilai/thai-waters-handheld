"""Compare the dressed loom to the assembled part solids and the actual terminal poses."""
import argparse
import itertools
import json
from pathlib import Path
import sys
import cadquery as cq

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent))
from package import get_model

def box(s):
    b=s.BoundingBox()
    return [(getattr(b,k+"min"),getattr(b,k+"max")) for k in "xyz"]

def near(a,b,margin=0):
    return all(max(x[0],y[0]) <= min(x[1],y[1])+margin for x,y in zip(a,b))

def run(reference):
    _,rows,paths=get_model()
    shapes={}
    for key,row in rows.items():
        if not row["productEligible"]: continue
        file=paths.get(key, reference / (key+".brep"))
        if key=="cellAlt":
            sys.path.insert(0,str(here.parents[1]/"rev-G"))
            from geometry import CX,CY,Z
            s=cq.importers.importStep(str(here.parents[1]/"rev-F/review/inputs/Adafruit-258.step")).val().translate((CX,CY,Z))
        else:
            s=cq.Shape.importBrep(str(file))
        shapes[key]=(s,box(s))
    wires={k for k in shapes if k.startswith(("w1","wh","wm","w3","USB-W","termination-","tee-","PH-","altTail","spk","batt","shrink"))}
    hits=[]
    pieces={k:[(p,box(p)) for p in s.Solids()] for k,(s,_) in shapes.items()}
    for a,b in itertools.combinations(shapes,2):
        if a not in wires and b not in wires:continue
        sa,ba=shapes[a];sb,bb=shapes[b]
        if not near(ba,bb):continue
        v=sum(p.Volume() for x,bx in pieces[a] for y,by in pieces[b] if near(bx,by) for p in x.intersect(y).Solids())
        if v>.00005:hits.append(dict(a=a,b=b,volume_mm3=round(v,6)))
    def gap(a,b):return round(shapes[a][0].distance(shapes[b][0]),5)
    clearances={k+":"+q:gap(k,q) for k in ["batt0","batt1"] for q in ["Housing","bridge","cellAlt","spk0","spk1"]}
    clearances["batt0:batt1"]=gap("batt0","batt1")
    assert min(clearances.values())>0,clearances
    ends=json.loads((here.parents[2]/'electronics/harness-r0003/placed/conductor-ends.json').read_text())
    terminations={}
    for e in ends:
        key='termination-'+e['id']; target=e['contact'] if e['contact']!='W1-P' else 'J8plug'
        wire={'W2-1':'batt0','W2-2':'batt1','W5-1':'spk0','W5-2':'spk1'}.get(e['id'],'w1'+e['id'][3:])
        terminations[e['id']]=dict(wire=wire,target=target,insulation_to_copper_mm=gap(key,wire),copper_to_terminal_mm=gap(key,target))
    interfaces=set()
    def mate(a,b):
        interfaces.add(frozenset([a,b]))
    for i in range(2):
        w='w3'+str(i)
        for end in ('Trimmed terminals','A1-k3'):mate(w,end)
        mate('motor','wm'+str(i))
        mate('ph','batt'+str(i))
        mate('ph','PH-TAIL'+str(i+1))
        mate('batt'+str(i),'PH-INS'+str(i+1))
    for net in ('VCC','GND','SDA','SCL'):
        for end in ('Cu','seal'):mate('wh'+net,'tee-'+net+'-'+end)
    for wire in ['wh'+n for n in ('GND','VCC','SCL','SDA','Trig')]:
        mate('drvParts',wire+'-Cu')
    for key in wires:
        if key.endswith('-Cu'):mate(key,key[:-3])
    for key,row in terminations.items():
        copper='termination-'+key
        mate(copper,row['target']);mate(copper,row['wire'])
        if key.startswith(('W2','W5')):
            mate(copper,'j7plug' if key.startswith('W2') else 'j9plug')
        assert row['insulation_to_copper_mm']<=0.001 and row['copper_to_terminal_mm']<=0.001,row
    unexpected=[h for h in hits if frozenset([h['a'],h['b']]) not in interfaces]
    assert not unexpected,unexpected
    result=dict(unexpected_intersections=unexpected,installed_parts=len(shapes),routed_parts=sorted(wires),nominal_gaps_mm=clearances,terminations=terminations,intersections=hits)
    (here/'dressed-harness.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Checked',len(wires),'routing parts against',len(shapes),'installed parts.',clearances,terminations,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True)
    run(p.parse_args().reference)
