"""Check the delivered XML geometry against an independent tessellation of the saved STEP."""
from collections import Counter
from zipfile import ZipFile
import json
import numpy as np
import trimesh
import cadquery as cq
from lxml import etree as E
from shapely.geometry import Polygon
from shapely.ops import unary_union
from housing_project import HERE, OUT, PREVIOUS, PRE_OPTICAL_STEP, MASTER, T, step_mesh, kit, sha

def load_print(path):
    with ZipFile(path) as z:
        xml = E.fromstring(z.read('3D/Objects/object_1.model'))
    shell = xml.find(f".//{kit.CORE}object[@id='1']/{kit.CORE}mesh")
    points = [[float(v.get(k)) for k in 'xyz'] for v in shell[0]]
    faces = [[int(f.get(k)) for k in ('v1','v2','v3')] for f in shell[1]]
    return trimesh.Trimesh(points, faces, process=False)

def face_audit(raw):
    m = raw.copy()
    m.apply_transform(np.linalg.inv(T))
    # Compare connectivity after welding identical seam coordinates in both versions.
    m.merge_vertices(digits_vertex=7)
    counts = np.bincount(m.edges_unique_inverse)
    result = dict(boundary_edges=int(sum(counts==1)), nonmanifold_edges=int(sum(counts>2)),
                  watertight=bool(m.is_watertight), consistent_winding=bool(m.is_winding_consistent))
    sides = []
    for sign in (-1,1):
        xyz=m.triangles
        coplanar = np.all(np.abs(xyz[:,:,1] - sign*8.76)<.0001, axis=1)
        select = coplanar & (m.triangles_center[:,0]>-48) & (m.triangles_center[:,0]<-38)
        projected = [Polygon(p[:,[0,2]]) for p in xyz[select]]
        union = unary_union(projected)
        sides.append(dict(installed_y_mm=sign*8.76,triangles=int(select.sum()),face_area_mm2=round(union.area,6),
                          reversed_triangles=int(sum(select & (sign*m.face_normals[:,1]<0))),
                          overlapping_area_mm2=round(sum(q.area for q in projected)-union.area,8)))
    result['usb_sides']=sides
    return result

def check():
    prior=next(PREVIOUS.glob('*.3mf'))
    before=face_audit(load_print(prior))
    delivered=load_print(OUT)
    after=face_audit(delivered)
    ref=step_mesh()
    ref.apply_transform(T)
    assert np.array_equal(ref.faces, delivered.faces)
    error=np.linalg.norm(ref.vertices-delivered.vertices,axis=1).max()
    assert error<1e-8
    assert sum(s['reversed_triangles'] for s in before['usb_sides'])>0
    assert after['watertight'] and after['consistent_winding']
    assert after['boundary_edges']==after['nonmanifold_edges']==0
    assert all(s['face_area_mm2']>50 and s['reversed_triangles']==0 and s['overlapping_area_mm2']<1e-7 for s in after['usb_sides'])
    shape=cq.importers.importStep(str(MASTER)).val()
    assert shape.isValid() and len(shape.Solids())==len(shape.Shells())==1
    # The earlier STEP defines the intended fit independent of the flawed print export.
    old=cq.importers.importStep(str(PREVIOUS/'housing.step')).val()
    changes=[old.cut(shape).Volume(),shape.cut(old).Volume()]
    assert max(map(abs,changes))<.0001
    with ZipFile(OUT) as a, ZipFile(prior) as b:
        assert set(a.namelist())==set(b.namelist())
        assert {k for k in a.namelist() if a.read(k)!=b.read(k)}=={'3D/Objects/object_1.model',kit.CFG}
        mods=lambda z:[E.tostring(o) for o in E.fromstring(z.read('3D/Objects/object_1.model')).iter(kit.CORE+'object') if o.get('id')!='1']
        assert mods(a)==mods(b)
    result=dict(source_step_sha256=sha(PRE_OPTICAL_STEP),released_step_sha256=sha(MASTER),
                project_sha256=sha(OUT),exact_triangle_indices=True,vertex_registration_error_mm=float(error),
                triangle_count=len(ref.faces),step_surface_types=dict(Counter(f.geomType() for f in shape.Faces())),
                step_difference_from_intended_fit_mm3=changes,previous_print=before,current_print=after)
    (HERE/'face-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':check()
