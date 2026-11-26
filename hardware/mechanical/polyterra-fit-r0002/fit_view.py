"""Compare the new backing with the installed grip and update the offline assembly."""
from pathlib import Path
import base64,io,re,json,sys
import cadquery as cq
import trimesh
from receiver import HERE,backing
def run(cache):
    parent=HERE.parent/'enclosure-print-r0004'
    old=cq.importers.importStep(str(parent/'housing.step')).val()
    new=cq.importers.importStep(str(HERE/'housing.step')).val()
    ramp=backing();grip=cq.Shape.importBrep(str(cache/'Removable rod grip.brep'))
    gap=grip.BoundingBox().xmin-ramp.BoundingBox().xmax
    assert gap>2 and new.isValid() and len(new.Solids())==1
    removed=old.cut(new).Volume();assert abs(removed)<.001
    excess=new.cut(old).Volume();assert abs(excess-ramp.cut(old).Volume())<.01
    (HERE/'mount-check.json').write_text(json.dumps(dict(added_mm3=round(excess,3),removed_mm3=round(removed,4),lower_bound_to_sliding_grip_mm=round(gap,3),motion='Any translation along the receiver Y axis',solids=len(new.Solids())),indent=2))
    html=(parent/'Enclosure-fit-guide.html').read_text(encoding='utf8')
    b64=re.search(r'Z2xURg[A-Za-z0-9+/=]+',html).group()
    scene=trimesh.load(io.BytesIO(base64.b64decode(b64)),file_type='glb',force='scene')
    name=scene.graph.get('Housing')[1];v,f=new.tessellate(.04,.16)
    mesh=trimesh.Trimesh([p.toTuple() for p in v],f);color=scene.geometry[name].visual.main_color
    mesh.visual=trimesh.visual.ColorVisuals(mesh,face_colors=color)
    scene.geometry[name]=mesh
    output=base64.b64encode(scene.export(file_type='glb')).decode()
    html=html.replace(b64,output).replace('R0004','R0006')
    (HERE/'Enclosure-fit-guide.html').write_bytes(('\n'.join(line.rstrip() for line in html.splitlines()).rstrip()+'\n').encode())
if __name__=='__main__':run(Path(sys.argv[1]))
