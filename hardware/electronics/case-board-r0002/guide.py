"""Build the assembly review from the released enclosure scene and editable candidate solids."""
from pathlib import Path
import base64, io, os, re, tempfile, subprocess
import trimesh
from mount import HERE, ROOT, mounted, stock

def mesh(shape,color):
    v,f=shape.tessellate(.035,.13)
    m=trimesh.Trimesh([p.toTuple() for p in v],f)
    m.visual=trimesh.visual.ColorVisuals(m,face_colors=[*color,255])
    return m

def build():
    base=ROOT/'hardware/mechanical'
    parent=base/'step-fit-r0008/Enclosure-fit-guide.html'
    html=parent.read_text(encoding='utf8')
    token=re.search(r'Z2xURg[A-Za-z0-9+/=]+',html).group()
    scene=trimesh.load(io.BytesIO(base64.b64decode(token)),file_type='glb',force='scene')
    parts=mounted()
    board=parts['PCB'].Solids()
    substrate=max(board,key=lambda s:s.Volume())
    scene.geometry[scene.graph.get('Housing')[1]]=mesh(stock(HERE/'housing.step'),[119,145,129])
    scene.geometry[scene.graph.get('Combined')[1]]=mesh(substrate,[44,106,84])
    for i,s in enumerate(s for s in board if not s.isSame(substrate)):
        col=[184,151,86] if s.BoundingBox().zlen<.12 else [69,73,74]
        n=f'BoardPart{i}'
        scene.add_geometry(mesh(s,col),node_name=n,geom_name=n)
    for i in (1,2):
        n=f'BoardPartScrew{i}'
        scene.add_geometry(mesh(parts[f'screw {i}'],[186,189,181]),node_name=n,geom_name=n)
    html=html.replace(token,base64.b64encode(scene.export(file_type='glb')).decode())
    html=html.replace('Enclosure fit R0008','Case board R0002 · mount review').replace('R0008 fit sequence','R0002 mount review')
    boot=(ROOT/'hardware/electronics/case-board-r0001/viewer.js').read_text().split('const views=')[0]
    stages=(base/'enclosure-print-r0004/views.js').read_text(encoding='utf8')
    stages=stages.replace('[58,-93,130],[5,0,10]','[55,-50,87],[23,1,14]')
    stages=stages.replace('Set the combined board package side down on its three housing supports.',
                          'Lower the rectangular PCB with components facing the case floor. Seat its two inboard screws and check that the far corner rests flat.')
    stages=stages.replace('o.visible=names.has(o.name)',"o.visible=(o.name.startsWith('BoardPart') && names.has('Combined')) || names.has(o.name)")
    html=html.replace('<button id="inspect-light">','<button id="inspect-board">PCB underside</button><button id="inspect-light">')
    inspect="""
  document.getElementById('inspect-board').onclick=()=>{
    show(4);
    gltf.scene.traverse(o=>{if(o.isMesh)o.visible=o.name==='Combined'||(o.name.startsWith('BoardPart')&&!o.name.startsWith('BoardPartScrew'));});
    camera.position.set(45,-30,-54);orbit.target.set(23,1,18);orbit.update();render();
    info.textContent='Component side, facing the case floor. Select Lower boards to return to the installed view.';
  };
"""
    stages=stages.replace("  document.getElementById('inspect-light')",inspect+"  document.getElementById('inspect-light')")
    stages=stages.replace('show(0);','show(4);')
    modules=ROOT/'game/src/node_modules'
    with tempfile.TemporaryDirectory() as folder:
        js=Path(folder)/'src.js';js.write_text(boot+stages,encoding='utf8')
        out=js.with_name('build.js')
        exe=modules/('@esbuild/win32-x64/esbuild.exe' if os.name=='nt' else '.bin/esbuild')
        subprocess.run([str(exe),str(js),'--bundle','--minify','--format=iife','--legal-comments=none','--outfile='+str(out)],check=True,env={**os.environ,'NODE_PATH':str(modules)})
        html,count=re.subn(r'<script>(?=[^<]{0,150}(?:\(\(\)|var ))[\s\S]*?</script>',lambda m:'<script>'+out.read_text(encoding='utf8')+'</script>',html,count=1)
        assert count==1
    (HERE/'Mount-review.html').write_bytes(html.encode())

if __name__=='__main__':build()
