"""Verify side insertion into the already mounted shelf and illustrate the blocked approach."""
from pathlib import Path
import sys,json
import cadquery as cq
from mount import HERE,BASE,geometry,b,near,box

from closure import features
sys.path.insert(0,str(BASE))
from leads import installed
def run(cache):
    _,shell,sled,posts,_=geometry()
    read=lambda n:cq.Shape.importBrep(str(cache/(n+'.brep')))
    present={'housing':shell,'shelf':sled,**{k:read(k) for k in ['Speaker','speakerGasket','speakerMagnet','speakerTerminal0','speakerTerminal1','spk0','spk1']}}
    def check(pieces,targets):
        hits={}
        for p in pieces:
            for k,q in targets.items():
                if near(b(p),b(q)):
                    v=p.intersect(q).Volume()
                    if v>.0001:hits[k]=round(max(v,hits.get(k,0)),5)
        return hits
    board,led=read('USB-PCB1'),read('USB-D1')
    lamp={'board':board,'LED':led}
    for name in ['USB-W4B','USB-W4B-Cu','USB-W4C','USB-W4C-Cu']:
        # The component-side wire roots travel with the lamp. Enclose their
        # complete registered shape inside an axis-aligned gauge at each leg.
        # Clip the tessellated wire at the cut plane. Enlarge the resulting
        # bounding box by 0.03 mm to cover the 0.01 mm chord tolerance.
        import numpy as np
        v,f=read(name).tessellate(.01,.12)
        v=np.array([p.toTuple() for p in v]);tri=v[np.array(f)]
        points=[v[v[:,0]<=-38]]
        for j,k in ((0,1),(1,2),(2,0)):
            a=tri[:,j];e=tri[:,k];mask=(a[:,0]<-38)!=(e[:,0]<-38)
            a,e=a[mask],e[mask]
            points.append(a+((-38-a[:,0])/(e[:,0]-a[:,0]))[:,None]*(e-a))
        p=np.vstack(points)
        root=box(*(p.min(axis=0)-.03),*(p.max(axis=0)+.03))
        lamp[name+' to X-38']=root
    report={'preloaded_shelf_rejected_at_2mm_inboard_mm3':board.translate((2,0,0)).intersect(shell).Volume(),
            'scope':'Shelf is secured first. Board, emitter and registered roots of both leads checked. Unconnected far ends remain free for dressing. Completed tethered loom, solder fillet allowances and insertion force need a wired sample.'}
    for stage,ofs,vec in [('lower',(0,-15,0),(0,0,24)),('side_entry',(0,0,0),(0,-15,0)),('lower_18',(0,-18,0),(0,0,24)),('side_entry_18',(0,0,0),(0,-18,0)),('lower_21',(0,-21,0),(0,0,24)),('side_entry_21',(0,0,0),(0,-21,0))]:
        report[stage]={}
        for name,q in lamp.items():
            shape=q.translate(ofs)
            bb=b(shape);end=b(shape.translate(vec));ranges=[[min(bb[i],end[i]),max(bb[i+1],end[i+1])] for i in (0,2,4)]
            pieces=[box(*[p[0] for p in ranges],*[p[1] for p in ranges])]
            hits=check(pieces,present)
            if hits:report[stage][name]=hits
    added={**{'post '+str(i):p for i,p in enumerate(posts)}, 'shelf':sled,**{'bezel boss '+str(i):s for i,s in enumerate(features()[0])}}
    print('Side entry',report,flush=True)
    report['revised_leads_vs_new_solids']={k:h for k,q in installed()[0].items() if (h:=check([q],added))}
    (HERE/'lamp-fit.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not report['lower_18'] and not report['side_entry_18'] and not report['revised_leads_vs_new_solids']
    print(report,flush=True)
if __name__=='__main__':run(Path(sys.argv[1]))
