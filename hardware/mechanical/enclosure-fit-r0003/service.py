"""Test removable-shelf installation, driver access and installed hardware."""
import sys,json
from pathlib import Path
import cadquery as cq
import numpy as np
from mount import HERE,BASE,PINS,geometry,b,box,cyl,near
from gauges import pcb,other
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec

def swept(shape,vec):
    # Sweeping every boundary face includes material between both end poses,
    # including straight sweeps of curved faces. Keep each volume separate.
    v=gp_Vec(*vec)
    pieces=[shape,shape.translate(vec)]
    for face in shape.Faces():
        q=cq.Shape.cast(BRepPrimAPI_MakePrism(face.wrapped,v).Shape())
        if abs(q.Volume())>1e-6:
            for s in q.Solids():
                if s.Volume()<0:s=cq.Shape.cast(s.wrapped.Reversed())
                if s.Volume()>1e-6:pieces.append(s)
    return pieces

def run(cache):
    ref=json.loads((HERE.parent/'TW-A-0001-R0017/installed-step.json').read_bytes())['components']
    shell0,shell,sled,posts,cut=geometry()
    fast=cq.importers.importStep(str(BASE.parents[1]/'components/standard-fasteners/6mm.step')).val()
    dg,_=pcb();dg=dg.rotate((0,0,0),(1,0,0),180).translate((13,-14,18.5))
    spk,motor,_=other(cache)
    screw=[fast.translate((x,y,12)) for x,y in PINS[1:]]
    driver=[cyl(x,y,13.4,2,24) for x,y in PINS[1:]]
    ref={k:v for k,v in ref.items() if k not in {'Housing','Rotor','A4-integration','A4-spacers','A4-bond','A5-power','A5-spacers','A5-bond'}}
    loaded={}
    def member(k):
        if k not in loaded:loaded[k]=cq.Shape.importBrep(str(cache/(k+'.brep')))
        return loaded[k]
    def checks(moving,pairs):
        res={}
        for k,t in pairs:
            for m in moving:
                if not near(b(m),b(t),.002):continue
                v=m.intersect(t).Volume()
                if v>.0001:res[k]=max(float(v),res.get(k,0.))
        return res
    def peers(moving,skip=()):
        bs=[b(m) for m in moving]
        return [(k,member(k)) for k,v in ref.items() if k not in skip and any(near(a,v['bounds_mm']) for a in bs)]
    def overlaps(shapes,skip=()):
        return checks(shapes,peers(shapes,skip))
    r={}
    r['sled_installed']=overlaps([sled])
    r['new_posts_installed']=overlaps(posts)
    r['screws_installed']=overlaps(screw)
    r['anti_rotation_cheek_gap_mm']=.25
    r['screw_centres_mm']=PINS[1:]
    r['physical_pilot_engagement_mm']=4.4
    r['screw_shell_common_mm3']=[s.intersect(shell).Volume() for s in screw]
    r['screw_hits_sled_mm3']=[s.intersect(sled).Volume() for s in screw]
    # These are installed in the otherwise empty rear half with speaker seated;
    # fit bridge, battery, display and loom after the shelf screws.
    present=[('housing',shell),('speaker gauge',spk)]
    present += [(n,member(n)) for n in ref if n.startswith('speaker') or n in ('Speaker','spk0','spk1')]
    for label,parts in [('drop',swept(sled.translate((14,0,0)),(0,0,24))),
                        ('slide',swept(sled,(14,0,0))),('driver',driver)]:
        r[label+'_throughout']=checks(parts,present)
    r['installed_cable_gap_mm']=sled.distance(member('w30'))
    r['speaker_gauge_vs_shell_mm3']=spk.intersect(shell).Volume()
    r['motor_gauge_vs_shell_mm3']=motor.intersect(shell).Volume()
    r['speaker_vs_shelf_mm']=spk.distance(sled)
    r['motor_vs_new_parts_mm']=min(motor.distance(s) for s in [sled,*posts])
    r['pcb_gauge_vs_new_parts_mm']=min(dg.distance(s) for s in [sled,*posts])
    r['pcb_gauge_vs_enclosure_mm3']=dg.intersect(shell).Volume()
    r['pcb_gauge_vs_retained']=overlaps([dg],skip=[k for k in ref if k.startswith('A5-W')])
    r['pilot_floor_mm']=5.0-2.5
    r['screw_tip_relief_mm']=12-6-5.0
    (HERE/'service-check.json').write_text(json.dumps(r,indent=2)+'\n')
    for key in ('sled_installed','new_posts_installed','screws_installed','drop_throughout','slide_throughout','driver_throughout','pcb_gauge_vs_retained'):
        assert not r[key], (key,r[key])
    for key in ('speaker_gauge_vs_shell_mm3','motor_gauge_vs_shell_mm3','pcb_gauge_vs_enclosure_mm3'):
        assert r[key]<.0001,(key,r[key])
    print(r,flush=True)
if __name__=='__main__':run(Path(sys.argv[1]))
