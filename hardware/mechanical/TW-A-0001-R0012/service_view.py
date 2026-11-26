"""Package the CviLux motion review as a single offline HTML file."""
import argparse, csv, json, shutil
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
from build import HERE,load,digest
from viewer import mesh
from service_check import HARNESS, read_shapes
from mate import split_latch, guide, STROKE

def outlines(shape):
    sectioner=BRepAlgoAPI_Section(shape.wrapped,gp_Pln(gp_Pnt(24.26,0,0),gp_Dir(1,0,0)),False)
    sectioner.Build()
    section=cq.Shape.cast(sectioner.Shape())
    outlines=[]
    for wire in cq.Wire.combine(section.Edges(),tol=1e-5):
        # Discretize the ordered closed wire, including narrow boss edges.
        pts=wire.positions(np.linspace(0,1,max(48,12*len(wire.Edges()))))
        outlines.append([[round(v.y,3),round(v.z,3)] for v in pts])
    return outlines

def make(cache,bundle,exports, *, revision=HERE,harness=HARNESS,overlay=None,wire_model=None):
    shapes=read_shapes(cache)
    if overlay:
        for name in overlay["remove"]:
            del shapes[name]
        for row in overlay["add"]:
            src=revision/row["brep"]
            assert digest(src)==row["sha256"]
            shapes[row["name"]]=cq.Shape.importBrep(str(src))
    route_guide=wire_model.guide if wire_model else guide
    housing=shapes['A3-J1-plug'];body,latch=split_latch(housing)
    h=shapes['A3-J1-header']
    items={}
    def add(k,s,color,motion='fixed'):
        items[k]=dict(color=color,motion=motion,**mesh(s))
    add('header',h.Solids()[0],'#56a999')
    add('pins',cq.Compound.makeCompound(h.Solids()[1:]),'#c89d62')
    add('housing',body,'#ebd5b0','rigid')
    add('rocker',latch,'#ec985e','rocker')
    add('TPA',shapes['A3-J1-TPA'],'#555f67','rigid')
    for k,s in shapes.items():
        if k.startswith('A3-J1-C') or k.startswith('wh') and k.endswith('-Cu'):add(k,s,'#b78954','rigid')
        elif k.startswith(('w1','tee-','termination-W1')) or k=='J8plug': add(k,s,'#457ea2' if k!='J8plug' else '#7697aa')
        elif overlay and k in {row["name"] for row in overlay["add"]} and k.startswith("A5-") and k not in ("A5-power","A5-bond","A5-spacers"):
            add(k,s,'#796451','context')
        elif k in ['A1-carrier','A1-population','A4-integration','A5-power']:
            add(k,s,'#698e81','display')
        elif k in ['drvBoard','drvParts','A3-J1-spacer','wm0','wm1','motor','bridge','A2-pcb']:
            add(k,s,{'drvBoard':'#577d63','drvParts':'#4b5151','motor':'#939a93','bridge':'#859187','A2-pcb':'#72927e'}.get(k,'#8a8172'),'context')
    routes=load(harness/'routing.json')
    leads={}
    for net in ('VCC','SCL','SDA','GND'):
        x,_,z=routes[net]['tap_center_mm']
        leads[net]=[]
        for frame in range(67):
            d=frame*.125
            points=route_guide(net,x,z,d,97 if overlay else 41)
            points.insert(0,[points[0][0],-5.35+d,10.36])
            leads[net].append(np.round(points,4).tolist())
    data=dict(items=items,leads=leads,stroke=STROKE,section=dict(h=outlines(h.Solids()[0]),p=outlines(body),l=outlines(latch)),
              qa=load((revision if overlay else HARNESS)/'clearance.json'),path=list(csv.DictReader((revision/'QA/service-path.csv').open())))
    assert data['qa']['source_hashes']=={r['name']:r['sha256'] for r in (overlay or load(HARNESS/'installed.json'))['add']}
    template=(HERE/'service-template.html').read_text(encoding='utf8')
    if overlay:
        data['seatedStudy']=True
        certificate=load(harness/"continuous-clearance.json")
        witnesses=load(harness/"clearance.json")["minimum_by_pair_group"]
        connector=load(harness/"connector-clearance.json")
        assert certificate["pass_nominal"] and connector["pass_nominal"]
        data["clearanceGate"]=certificate["continuous_external_and_interlead_clearance_test_mm"]
        data["externalWitness"]=min((witnesses[g] for g in ("display","W1","fixed","lead_to_lead")),key=lambda w:w["native_witness"]["gap_mm"])
        data["terminalGap"]=connector["minimum_exact_straight_stub_to_nonmating_moving_part_mm"]
        template=template.replace(HERE.name,revision.name).replace('R0012 ·',revision.name.rsplit('-',1)[-1]+' ·')
        template=template.replace('type="checkbox"> Display boards seated','type="checkbox" checked> Show seated display boards')
        template=template.replace('Open the isolated unit and lift the A1/A4/A5 display assembly clear. Disconnect J8 and support its plug in the original dressed position.', 'The display stack, J8 and W1 stay at their installed coordinates. Show or hide the translucent boards to inspect the working space.')
        template=template.replace('Brown shows moving W4 to W1.', 'Brown shows the closest moving lead to its seated surroundings or another lead.')
    template=template.replace('<script id="data"></script>','<script type="application/json" id="data">'+json.dumps(data,separators=(',',':'))+'</script>')
    template=template.replace('<script id="app"></script>','<script>'+bundle.read_text(encoding='utf8')+'</script>')
    doc=HERE.parents[2]/'docs/models'/(revision.name+'-connector-motion.html')
    doc.write_text(template,encoding='utf8')
    shutil.copyfile(doc,exports/doc.name)
    print(doc,digest(doc))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['baseline-breps','bundle','exports']:p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();make(a.baseline_breps,a.bundle,a.exports)

