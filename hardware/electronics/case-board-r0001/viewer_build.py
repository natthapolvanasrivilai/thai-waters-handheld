"""Package the case board and its mounting hardware as a local, offline inspection view."""
from pathlib import Path
import base64
import os
import subprocess
import tempfile
import cadquery as cq
import trimesh
from build import HERE,MOUNTS
from fit import ROOT
from leads import installed

def run():
    scene=trimesh.Scene()
    def add(s,name,color):
        vv,ff=s.tessellate(.045,.18)
        mesh=trimesh.Trimesh(vertices=[v.toTuple() for v in vv],faces=ff)
        mesh.visual=trimesh.visual.ColorVisuals(mesh,face_colors=[*color,255])
        scene.add_geometry(mesh,node_name=name,geom_name=name)
    add(cq.importers.importStep(str(HERE/"housing.step")).val(),"Housing",(124,153,136))
    pcb=cq.importers.importStep(str(HERE/"case-board.step")).val().rotate((0,0,0),(1,0,0),180).translate((13,-14,18.5))
    substrate=max(pcb.Solids(),key=lambda s:s.Volume())
    add(substrate,"PCB",(38,105,81))
    for i,s in enumerate(pcb.Solids()):
        if abs(s.Volume()-substrate.Volume())<.00001:continue
        b=s.BoundingBox()
        add(s,"Package_"+str(i),(190,148,79) if b.zlen<.12 else (72,79,80))
    screw=cq.importers.importStep(str(ROOT/"hardware/components/standard-fasteners/4mm.step")).val()
    for i,(x,y) in enumerate(MOUNTS,1):add(screw.translate((x-87,y-114,18.5)),"Screw_"+str(i),(166,174,172))
    for n,s in installed()[0].items():
        add(s,n.replace(" ","_"),(50,55,56) if n.startswith("W3") else (195,95,66))
    binary=base64.b64encode(scene.export(file_type="glb")).decode()
    modules=ROOT/"game/src/node_modules"
    exe=modules/("@esbuild/win32-x64/esbuild.exe" if os.name=="nt" else ".bin/esbuild")
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/"viewer.js"
        subprocess.run([str(exe),str(HERE/"viewer.js"),"--bundle","--minify","--format=iife","--legal-comments=none","--outfile="+str(out)],check=True,env={**os.environ,"NODE_PATH":str(modules)})
        html=(HERE/"viewer-template.html").read_text(encoding="utf8").replace("@@SCENE@@",binary).replace("@@JS@@",out.read_text(encoding="utf8"))
    (HERE/"Case-board-R0001-view.html").write_bytes(html.replace("@@LICENSE@@",(ROOT/"third-party/three-LICENSE.txt").read_text(encoding="utf8")).encode("utf8"))
if __name__=="__main__":run()
