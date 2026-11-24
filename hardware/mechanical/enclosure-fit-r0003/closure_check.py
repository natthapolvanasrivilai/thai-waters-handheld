"""Check closure travel, display clearance and rear screw access in installed coordinates."""
from pathlib import Path
import sys,json
import cadquery as cq
from mount import HERE,BASE,geometry,b,near,cyl
from closure import features,CENTRES
from service import swept
def run(cache):
    _,shell,_,_,_=geometry()
    ref=json.loads((HERE.parent/'TW-A-0001-R0017/installed-step.json').read_bytes())['components']
    def member(n):return cq.Shape.importBrep(str(cache/(n+'.brep')))
    _,_,pads,bores=features()
    bezel=member('Bezel').fuse(*pads).cut(*bores).clean()
    fast=cq.importers.importStep(str(BASE.parents[1]/'components/standard-fasteners/6mm.step')).val()
    added=cq.Compound.makeCompound(pads)
    screw=[fast.translate((x,y,28.30)) for x,y in CENTRES]
    def conflicts(shapes,items):
        hits={}
        for n,t in items:
            for s in shapes:
                if near(b(s),b(t),.001):
                    vol=s.intersect(t).Volume()
                    if vol>.0001:hits[n]=round(max(hits.get(n,0),vol),5)
        return hits
    items=[(n,member(n)) for n,rec in ref.items() if n!='Bezel' and n!='Housing' and near(b(added),rec['bounds_mm'],4)]
    out={'pad_centres_mm':CENTRES,'head_recess_mm':round(30-b(screw[0])[-1],4),'screw_tip_relief_mm':.75,'tapped_engagement_mm':3.85,'seat_web_mm':1.75,
         'bezel_final_vs_shell_mm3':round(bezel.intersect(shell).Volume(),6),
         'bezel_final_vs_retained':conflicts([bezel],items),
         'new_pads_through_12mm_closure':conflicts(swept(added,(0,0,12)),[('housing',shell),*items]),
         'screw_vs_bezel_or_retained':conflicts(screw,[('bezel',bezel),*items]),
         'screen_to_new_pads_mm':round(added.distance(member('A1-touch')),4),
         'h1_head_access':{}}
    for i in range(1,5):
        bb=b(member('H1-'+str(i))); x=(bb[0]+bb[1])/2; y=(bb[2]+bb[3])/2
        tool=cyl(x,y,-6,2.02,15.4)
        out['h1_head_access'][str(i)]={'x':x,'y':y,'housing_overlap_mm3':round(shell.intersect(tool).Volume(),5),'grip_overlap_mm3':round(tool.intersect(member('Removable rod grip')).Volume(),5)}
    for n,g in [('housing',shell),('bezel',bezel)]:cq.exporters.export(g,str(HERE/(n+'.step')))
    (HERE/'closure-check.json').write_text(json.dumps(out,indent=2)+'\n')
    assert out['bezel_final_vs_shell_mm3']<.0001 and not out['bezel_final_vs_retained']
    assert not out['new_pads_through_12mm_closure'] and not out['screw_vs_bezel_or_retained']
    assert all(max(v['housing_overlap_mm3'],v['grip_overlap_mm3'])<.0001 for v in out['h1_head_access'].values())
    print(out)
if __name__=='__main__':run(Path(sys.argv[1]))
