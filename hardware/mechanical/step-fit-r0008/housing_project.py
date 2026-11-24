"""Build a STEP master and tessellate that exact file for the R0008 print housing."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import sys

import cadquery as cq
import numpy as np
import trimesh
from lxml import etree as E

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / 'polyterra-fit-r0003'
PRE_OPTICAL_STEP = HERE.parent / 'polyterra-fit-r0002/housing.step'
MASTER = HERE / 'housing.step'
OUT = HERE / 'Thai-Waters-R0008-STEP-PolyTerra-SuperTack-X1C.3mf'
sys.path.insert(0, str(PREVIOUS))
from print_project import kit, local_tools

# Installed STEP coordinates to the centered object coordinates of the 45Â° fixture.
# The plate instance supplies the final translation onto the X1C bed.
T = np.eye(4)
c = np.sqrt(.5)
T[:3] = [[c, 0, -c, 7.532339939609294], [0, 1, 0, -2.575151443],
         [c, 0, c, -13.317583435839849]]

def sha(path):
    return sha256(path.read_bytes()).hexdigest()

def make_master():
    assert sha(PRE_OPTICAL_STEP) == '5003e8d4856b37eca4e8a7eeb9755a99fbed5c8df4b1f93f31e87e7fdb0d4a3b'
    solid = cq.importers.importStep(str(PRE_OPTICAL_STEP)).val()
    for cut_region, retained_wall, closed_channel in local_tools():
        solid = solid.cut(cut_region).fuse(retained_wall, closed_channel).clean()
    assert solid.isValid() and len(solid.Solids()) == len(solid.Shells()) == 1
    cq.exporters.export(solid, str(MASTER))

def step_mesh():
    solid = cq.importers.importStep(str(MASTER)).val()
    assert solid.isValid() and len(solid.Solids()) == len(solid.Shells()) == 1
    points, faces = solid.tessellate(.008, .07)
    # OCCT emits face-local vertices. Index common boundary coordinates once,
    # preserving every triangle exactly as triangulated from its STEP face.
    xyz = np.round([p.toTuple() for p in points], 8)
    unique, lookup = np.unique(xyz, axis=0, return_inverse=True)
    mesh = trimesh.Trimesh(unique, lookup[np.asarray(faces)], process=False)
    assert mesh.is_volume and mesh.body_count == 1 and mesh.area_faces.min() > 0
    return mesh

def export_print():
    stock_project = next(PREVIOUS.glob('*.3mf'))
    assert sha(stock_project) == 'af101f1ec1f81f23bee58a0d469af3a5d41a488d3e9a7782450a4e4231b9b896'
    with ZipFile(stock_project) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    path = '3D/Objects/object_1.model'
    root = E.fromstring(files[path])
    part = root.find(f".//{kit.CORE}object[@id='1']/{kit.CORE}mesh")
    mesh = step_mesh()
    mesh.apply_transform(T)
    for node in part:
        node.clear()
    for point in mesh.vertices:
        E.SubElement(part[0], kit.CORE+'vertex', **dict(zip('xyz', (f'{v:.9f}' for v in point))))
    for face in mesh.faces:
        E.SubElement(part[1], kit.CORE+'triangle', **dict(zip(('v1','v2','v3'), map(str,face))))
    cfg = E.fromstring(files[kit.CFG])
    obj = cfg.find("object[@id='2']")
    kit.meta(obj, 'tree_support_branch_angle', 35)
    kit.meta(obj, 'support_object_xy_distance', .23)
    obj.find("part[@id='1']/mesh_stat").set('face_count', str(len(mesh.faces)))
    obj.find('metadata[@face_count]').set('face_count', str(len(mesh.faces)))
    files[path] = kit.encode(root)
    files[kit.CFG] = kit.encode(cfg)
    kit.write(files, OUT)

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild-master',action='store_true',help='reconstruct the R0008 STEP from the pre-optical STEP')
    if parser.parse_args().rebuild_master:
        make_master()
    export_print()
