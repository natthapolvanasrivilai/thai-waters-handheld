"""Build backing along the exterior of the receiver. Dimensions are installed mm."""
import cadquery as cq
import manifold3d as mf
from kit import *
OFFSET=np.array([-3.140001297,-2.575000763,3.200001004-15.5000019])
def backing():
    # The shoe slides on the east side. The ramp lives entirely on its west side.
    y=-30.7
    outline=[(-15.35,.06),(-.68,-3.20),(-.68,.06)]
    wire=cq.Wire.makePolygon([cq.Vector(x,y,z) for x,z in outline],close=True)
    return cq.Solid.extrudeLinear(wire,[],(0,37.8,0))
def installed():
    old=cq.importers.importStep(str(HERE.parent/'enclosure-print-r0004/housing.step')).val()
    updated=old.fuse(backing()).clean()
    assert updated.isValid() and len(updated.Solids())==1 and updated.Volume()>old.Volume()
    cq.exporters.export(updated,str(HERE/'housing.step'))
def mesh_add(files,root,cfg):
    mesh,doc,path=read(files,root,2)
    vv,ff=backing().tessellate(.01,.1)
    def solid(m):
        return mf.Manifold(mf.Mesh64(np.array(m.vertices,dtype='float64'),np.array(m.faces,dtype='uint64')))
    add=trimesh.Trimesh([p.toTuple() for p in vv],ff);add.apply_translation(OFFSET)
    union=solid(mesh)+solid(add)
    assert union.status()==mf.Error.NoError and len(union.decompose())==1
    made=union.to_mesh64()
    m=doc.find(f".//{CORE}object[@id='1']/{CORE}mesh")
    for parent in m:parent.clear()
    for p in made.vert_properties:E.SubElement(m[0],CORE+'vertex',**dict(zip('xyz',[f'{v:.9f}' for v in p[:3]])))
    for tri in made.tri_verts:E.SubElement(m[1],CORE+'triangle',**dict(zip(('v1','v2','v3'),map(str,tri))))
    files[path]=encode(doc)
    stat=cfg.find("object[@id='2']/part[@id='1']/mesh_stat")
    if stat is not None:stat.set('face_count',str(len(made.tri_verts)))
if __name__=='__main__':installed()
