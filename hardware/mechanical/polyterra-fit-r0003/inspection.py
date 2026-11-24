"""Check the print mesh and installed CAD at the retired collectors and the active interfaces."""
from print_project import HERE, MECH, PARENT, OUT, kit, surface, manifold, OFFSET
import cadquery as cq
import numpy as np
import trimesh
from pathlib import Path
import json,zipfile,sys
from lxml import etree as E

def report(cache, folder=HERE, project=OUT, template_project=kit.OUT):
    cache=Path(cache)
    reference=MECH/'enclosure-print-r0004'
    load=lambda p:cq.importers.importStep(str(p)).val()
    shell=load(folder/'housing.step')
    before=load(PARENT/'housing.step')
    assert shell.isValid() and len(shell.Solids())==1 and len(shell.Shells())==1
    with zipfile.ZipFile(project) as z,zipfile.ZipFile(template_project) as parent:
        files={k:z.read(k) for k in z.namelist()}
        mesh,doc,key=kit.read(files,E.fromstring(files[kit.MODEL]),2)
        assert set(z.namelist())==set(parent.namelist())
        assert {k for k in files if files[k]!=parent.read(k)}=={kit.CFG,key}
        prior_modifiers=E.fromstring(parent.read(key))
        for obj in doc.iter(kit.CORE+'object'):
            if obj.get('id')!='1':
                original=prior_modifiers.find(f".//{kit.CORE}object[@id='{obj.get('id')}']")
                assert E.tostring(obj)==E.tostring(original)
    f=kit.source();raw=kit.read(f,E.fromstring(f[kit.MODEL]),2)[0]
    rot=trimesh.geometry.align_vectors(np.array([-1,0,-1])/np.sqrt(2),[0,0,-1])
    raw.apply_transform(rot);mesh.apply_translation(raw.bounds.mean(0))
    mesh.apply_transform(np.linalg.inv(rot));mesh.apply_translation(-OFFSET)
    mm=manifold(mesh)
    assert len([q for q in mm.decompose() if abs(q.volume())>.001])==1
    from manifold3d import Manifold
    tips={}
    for y in (-9.922,9.881):
        # Both complete terminal faces and the surrounding printed octagons
        # originally extended over this narrow 0.20-mm end station.
        cy=y+(-.17 if y<0 else .17)
        size=[.20,2.25,2.9];lo=[-39.58,cy-1.125,19.117]
        b=cq.Solid.makeBox(*size,cq.Vector(*lo))
        old=before.intersect(b).Volume();new=shell.intersect(b).Volume()
        newmesh=(mm^Manifold.cube(size).translate(lo)).volume()
        assert old>.1 and max(abs(new),abs(newmesh))<.002,(old,new,newmesh)
        tips[str(y)]=dict(old_mm3=round(old,5),new_step_mm3=round(new,5),new_print_mm3=round(newmesh,5))
    apertures={}
    for label,m in [('STEP',manifold(surface(shell))),('3MF',mm)]:
        yz=m.rotate((0,-90,0))
        for x in (-49.99,-49.75,-49.3):
            loops=[p for p in yz.slice(x).to_polygons() if min(p[:,0])>-15 and max(p[:,0])<-11 and min(p[:,1])>-10 and max(p[:,1])<10]
            assert len(loops)==1,(label,x,[(p.min(0).tolist(),p.max(0).tolist()) for p in loops])
            extent=np.ptp(loops[0],axis=0)
            assert np.allclose(extent,[2,2.5],atol=.025),(x,extent)
            apertures[f'{label} at X{x}']=extent.round(3).tolist()
    active={}
    for name in ('shelf','rgb-gauge','diffuser','bezel','usbSurround','A1-usb','Speaker','Removable rod grip'):
        p=reference/(name+'.step')
        solid=load(p) if p.exists() else cq.Shape.importBrep(str(cache/(name+'.brep')))
        was=before.intersect(solid).Volume()
        now=shell.intersect(solid).Volume()
        assert abs(was)<.001 and abs(now)<.001,(name,was,now)
        active[name]=dict(parent_overlap_mm3=round(was,4),current_overlap_mm3=round(now,4))
    add=shell.cut(before);sub=before.cut(shell)
    limit=cq.Solid.makeBox(11,26,12,cq.Vector(-50,-13,11))
    assert add.cut(limit).Volume()<.001 and sub.cut(limit).Volume()<.001
    result=dict(collector_end_witnesses=tips,aperture_height_width_mm=apertures,installed_comparison=active,added_mm3=round(add.Volume(),3),removed_mm3=round(sub.Volume(),3),delta_outside_usb_region_mm3=0)
    (folder/'interface-check.json').write_text(json.dumps(result,indent=2)+'\n')
    sys.path.insert(0,str(reference))
    import light_motion
    light_motion.run(cache,folder/'housing.step',folder/'light-motion.json')
if __name__=='__main__':report(sys.argv[1])
