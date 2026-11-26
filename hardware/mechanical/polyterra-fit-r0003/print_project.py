"""Remove the two discontinued light pipes from the installed shell and its native print mesh."""
from pathlib import Path
import importlib.util
import sys
import zipfile
import hashlib

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh
from lxml import etree as E

HERE = Path(__file__).resolve().parent
MECH = HERE.parent
PARENT = MECH / 'polyterra-fit-r0002'
sys.path.insert(0, str(PARENT))
import kit
from receiver import OFFSET

OUT = HERE / 'Thai-Waters-R0007-PolyTerra-SuperTack-X1C.3mf'
CAD_SOURCE = MECH / 'TW-A-0001-R0009/build.py'

def local_tools():
    spec = importlib.util.spec_from_file_location('original_usb_well', CAD_SOURCE)
    well = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(well)
    original = dict(well.GUIDES)
    well.GUIDES = {'statusUsbGuide': original['statusUsbGuide']}
    # Evaluate the source of the USB cup itself without the retired sleeves.
    base = cq.Shape.importBrep(str(MECH/'TW-A-0001-R0008/CAD/housing-battery-bay.brep'))
    local = well.box(-50.15,-13,10.8,12,26,13)
    clean = well.housing(base.intersect(local))
    # Retain the current single-window outer skin and the lamp installation path.
    clean = clean.fuse(well.box(-50,-9.6,11.79,3.01,19.2,2.73))
    clean = clean.cut(well.box(-42.56,-17.75,11.38,1.30,20.155,3.47))
    keep = well.box(-47.30,-13,11,8.20,26,12)
    tools=[]
    for name in ('statusChgGuide','statusPwrGuide'):
        start,end,radius=original[name]
        a,b=np.array(start),np.array(end)
        axis=(b-a)/(b[0]-a[0])
        mask=well.bar(tuple(a-axis*.1),tuple(b+axis*.1),radius+1.02).intersect(keep)
        # Fill the isolated segment behind the existing exterior skin without
        # remeshing or cutting the already closed outer surface.
        stub = well.bar(tuple(a), tuple(b), radius+.24).intersect(
            well.box(-49.85,-13,11.79,2.56,26,11.21)).intersect(clean)
        tools.append((mask,clean.intersect(mask).clean(),stub))
    return tools

def surface(shape):
    points,faces=shape.tessellate(.008,.07)
    return trimesh.Trimesh([p.toTuple() for p in points],faces)

def manifold(m):
    out=mf.Manifold(mf.Mesh64(np.ascontiguousarray(m.vertices,dtype=np.float64),
                              np.ascontiguousarray(m.faces,dtype=np.uint64)))
    assert out.status()==mf.Error.NoError
    return out

def build():
    assert hashlib.sha256(kit.OUT.read_bytes()).hexdigest()=='0611121fa0b8f6fecd5c7d5ee8e7166f674548e225ad213d411e9f7dc70b8da1'
    with zipfile.ZipFile(kit.OUT) as z:
        files={k:z.read(k) for k in z.namelist()}
    model=E.fromstring(files[kit.MODEL])
    cfg=E.fromstring(files[kit.CFG])
    stock,doc,path=kit.read(files,model,2)
    old=cq.importers.importStep(str(PARENT/'housing.step')).val()
    shell=old
    donor=manifold(stock)
    baseline=kit.source()
    prior=kit.read(baseline,E.fromstring(baseline[kit.MODEL]),2)[0]
    rot=trimesh.geometry.align_vectors(np.array([-1,0,-1])/np.sqrt(2),[0,0,-1])
    prior.apply_transform(rot)
    placement=rot.copy()
    placement[:3,3]=rot[:3,:3]@OFFSET-prior.bounds.mean(0)
    for mask,retained,stub in local_tools():
        shell=shell.cut(mask).fuse(retained,stub).clean()
        tool=manifold(surface(mask)).transform(placement[:3])
        replacement=manifold(surface(retained)).transform(placement[:3])
        donor=(donor-tool)+replacement+manifold(surface(stub)).transform(placement[:3])
    assert shell.isValid() and len(shell.Solids())==1
    assert donor.status()==mf.Error.NoError
    bodies=sorted(donor.decompose(),key=lambda q:abs(q.volume()),reverse=True)
    assert sum(abs(q.volume()) for q in bodies[1:]) < .002
    data=bodies[0].simplify(.00001).to_mesh64()
    mesh=doc.find(f".//{kit.CORE}object[@id='1']/{kit.CORE}mesh")
    for element in mesh:element.clear()
    for xyz in data.vert_properties:
        E.SubElement(mesh[0],kit.CORE+'vertex',**dict(zip('xyz',(f'{v:.9f}' for v in xyz[:3]))))
    for face in data.tri_verts:
        E.SubElement(mesh[1],kit.CORE+'triangle',**dict(zip(('v1','v2','v3'),map(str,face))))
    obj=cfg.find("object[@id='2']")
    obj.find("part[@id='1']/mesh_stat").set('face_count',str(len(data.tri_verts)))
    obj.find('metadata[@face_count]').set('face_count',str(len(data.tri_verts)))
    files[path]=kit.encode(doc)
    files[kit.CFG]=kit.encode(cfg)
    kit.write(files,OUT)
    cq.exporters.export(shell,str(HERE/'housing.step'))
    return placement

if __name__=='__main__':build()
