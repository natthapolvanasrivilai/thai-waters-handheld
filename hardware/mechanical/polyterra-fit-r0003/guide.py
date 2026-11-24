"""Replace the housing in the offline guide, keeping all installed transforms and controls."""
from pathlib import Path
import io,base64,re
import cadquery as cq
import trimesh
from print_project import HERE,PARENT,surface
def build(folder=HERE, template_dir=PARENT, source_rev='R0006', revision='R0007'):
    template=(template_dir/'Enclosure-fit-guide.html').read_text(encoding='utf8')
    old=re.search(r'Z2xURg[A-Za-z0-9+/=]+',template).group()
    scene=trimesh.load(io.BytesIO(base64.b64decode(old)),file_type='glb',force='scene')
    name=scene.graph.get('Housing')[1]
    mesh=surface(cq.importers.importStep(str(folder/'housing.step')).val())
    mesh.visual=trimesh.visual.ColorVisuals(mesh,face_colors=scene.geometry[name].visual.main_color)
    scene.geometry[name]=mesh
    html=template.replace(old,base64.b64encode(scene.export(file_type='glb')).decode()).replace(source_rev,revision)
    (folder/'Enclosure-fit-guide.html').write_bytes(html.encode())
if __name__=='__main__':build()
