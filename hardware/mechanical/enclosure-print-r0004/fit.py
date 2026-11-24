"""Report installed collisions, closure access and the aperture section of the USB wall."""
from pathlib import Path
import json,sys
import cadquery as cq
from interfaces import HERE,CENTRES,box,cyl
from mount import b,near
from project import manifold,mesh
def check(cache):
    part=lambda n:cq.importers.importStep(str(HERE/(n+'.step'))).val()
    stock=lambda n:cq.Shape.importBrep(str(cache/(n+'.brep')))
    shell,bezel,shelf,lens,lamp=map(part,['housing','bezel','shelf','diffuser','rgb-gauge'])
    hits={}
    def pair(k,a,b):
        v=a.intersect(b).Volume()
        if v>.0001:hits[k]=round(v,5)
    for n,q in [('bezel',bezel),('shelf',shelf),('lens',lens),('lamp',lamp)]:pair(n+' vs housing',q,shell)
    for n,q,t in [('lens vs lamp',lens,lamp),('lens vs shelf',lens,shelf),('lamp vs shelf',lamp,shelf)]:pair(n,q,t)
    for n in ['A1-touch','A1-mounts','A1-backing','A1-carrier','A1-population','A1-usb','Removable rod grip']:
        q=stock(n)
        pair('bezel vs '+n,bezel,q)
        for x,y in CENTRES:
            pair('post vs '+n,cyl(x,y,2.10,3.45,23.65),q)
            pair('driver vs '+n,cyl(x,y,-17,2.02,39.60),q)
    fit={}
    for i,shape in enumerate([shell]):
        # A pierced rectangular skin gives just one closed loop in this section.
        rot=manifold(mesh(shape)).rotate((0,-90,0))
        for x in (-49.99,-49.75,-49.3):
            loops=[p for p in rot.slice(x).to_polygons() if min(p[:,0])>-15 and max(p[:,0])<-11 and min(p[:,1])>-10 and max(p[:,1])<10]
            fit[str(x)]=[[(p[:,k].min(),p[:,k].max()) for k in (0,1)] for p in loops]
            assert len(loops)==1,fit
    report=dict(intersections_mm3=hits,apertures_by_x_mm=fit,lens_to_emitter_mm=lens.distance(lamp),glass_to_bezel_mm=bezel.distance(stock('A1-touch')),rear_fastener_count=2,blind_pilot_top_skin_mm=1.,rear_screw_engagement_mm=2.68,scope='Installed CAD and rear axial driver envelopes. Physical fit, light output and retention await the first article.')
    print(json.dumps(report,indent=2),flush=True)
    (HERE/'fit.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not hits,hits
if __name__=='__main__':check(Path(sys.argv[1]))
