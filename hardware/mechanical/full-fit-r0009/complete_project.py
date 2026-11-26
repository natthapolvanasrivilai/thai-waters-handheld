"""Assemble the complete fit kit around the R0002 board and its housing STEP."""
from pathlib import Path
from zipfile import ZipFile
import sys
from lxml import etree as E
HERE=Path(__file__).resolve().parent
PREV=HERE.with_name('step-fit-r0008')
BOARD=HERE.parents[1]/'electronics/case-board-r0002'
OUT=HERE/'Thai-Waters-R0009-Complete-Fit-PolyTerra-SuperTack-X1C.3mf'
sys.path.insert(0,str(PREV))
from housing_project import step_mesh,T,kit,sha

def build():
    parent=next(PREV.glob('*.3mf'))
    assert sha(parent)=='e4f92173cecc0126a2544f294427c334e959c349c17462bc7713ccd17fb04372'
    with ZipFile(parent) as z: files={k:z.read(k) for k in z.namelist()}
    shell='3D/Objects/object_1.model'
    model=E.fromstring(files[shell])
    mesh=model.find(f".//{kit.CORE}object[@id='1']/{kit.CORE}mesh")
    solid=step_mesh(BOARD/'housing.step')
    solid.apply_transform(T)
    for node in mesh:node.clear()
    for v in solid.vertices:
        E.SubElement(mesh[0],kit.CORE+'vertex',**dict(zip('xyz',(f'{p:.9f}' for p in v))))
    for face in solid.faces:
        E.SubElement(mesh[1],kit.CORE+'triangle',**dict(zip(('v1','v2','v3'),map(str,face))))
    files[shell]=kit.encode(model)
    cfg=E.fromstring(files[kit.CFG])
    obj=cfg.find("object[@id='2']")
    obj.find("metadata[@face_count]").set('face_count',str(len(solid.faces)))
    obj.find("part[@id='1']/mesh_stat").set('face_count',str(len(solid.faces)))
    kit.meta(obj,'name','Housing - rectangular PCB mount and single status light')
    resource='3D/Objects/gauge_108.model'
    with ZipFile(next(BOARD.glob('*.3mf'))) as z:
        files[resource]=z.read(resource)
        single=E.fromstring(z.read(kit.CFG)).find("object[@id='108']")
    cfg.replace(cfg.find("object[@id='108']"),single)
    files[kit.CFG]=kit.encode(cfg)
    kit.write(files,OUT)

if __name__=='__main__':build()
