"""Build the offline fit guide from the same geometry as the printed parts."""
from pathlib import Path
import sys,os,json,base64,subprocess,tempfile
import trimesh,numpy as np,cadquery as cq
from interfaces import HERE,OLD,CENTRES
from mount import BASE
from gauges import pcb,other

ROOT=HERE.parents[2]
def run(cache,supplier_step):
    scene=trimesh.Scene()
    def add(m,n,color):
        if isinstance(m,cq.Shape):
            v,f=m.tessellate(.04,.16)
            m=trimesh.Trimesh([p.toTuple() for p in v],f)
        m.visual=trimesh.visual.ColorVisuals(m,face_colors=[*color,255])
        scene.add_geometry(m,node_name=n,geom_name=n)
    case=(137,156,137); steel=(183,188,185); gauge=(146,151,154); charcoal=(48,57,56); amber=(217,154,78)
    def installed(name):return cq.importers.importStep(str(HERE/(name+'.step'))).val()
    shell,shelf=installed('housing'),installed('shelf')
    add(installed('diffuser'),'Diffuser',(230,242,242))
    from hashlib import sha256
    assert sha256(supplier_step.read_bytes()).hexdigest()=='a439644d5916a9ef3dd84bde075d1c9ccef111e101809441e252e7454ebc8700'
    carrier=cq.Shape.importBrep(str(cache/'USB-PCB1.brep'))
    add(carrier,'RGBcarrier',(62,108,83))
    emitter=cq.importers.importStep(str(supplier_step)).val().rotate((0,0,0),(0,0,1),90)
    emitter=emitter.translate((carrier.BoundingBox().xmin-.125,0,13.10))
    for i,solid in enumerate(emitter.Solids()):
        add(solid,'LED'+str(i),(220,216,170) if i==0 else ((206,199,178) if i<10 else (228,223,204)))
    add(shell,'Housing',case);add(shelf,'Shelf',case)
    add(cq.importers.importStep(str(HERE/'bezel.step')).val(),'Bezel',charcoal)
    def stock(n):return cq.Shape.importBrep(str(cache/(n+'.brep')))
    sp,m,_=other(cache);add(sp,'Speaker',gauge);add(m,'Motor',gauge)
    fast=cq.importers.importStep(str(ROOT/'hardware/components/standard-fasteners/6mm.step')).val()
    add(fast.translate((-44.6,18,12)),'ShelfScrew',steel)
    for i,(x,y) in enumerate(CENTRES):add(fast.rotate((0,0,0),(1,0,0),180).translate((x,y,22.60)),'Closure'+str(i),steel)
    g,_=pcb();add(g.rotate((0,0,0),(1,0,0),180).translate((13,-14,18.5)),'Combined',(64,125,106))
    fit=HERE.parent/'pcb-fit-r0013'
    for n,rec in json.loads((fit/'geometry.json').read_bytes())['parts'].items():
        if n.startswith('USB') or n in ('A4-integration','A5-power'):continue
        mesh=trimesh.load_mesh(fit/rec['file'])
        mat=np.eye(4);mat[:3,:]=rec['print_to_installed_3x4'];mesh.apply_transform(mat)
        add(mesh,n.split('-')[0] if not n.startswith('USB') else n.replace('-',''),gauge)
    for n in ('A3-J1-plug','cellAlt','bridge','Key cap','Retainer','Removable rod grip','Collar','Stem','Grip','serviceCover'):
        add(stock(n),n.replace(' ','').replace('-',''),(amber if n in ('Key cap','Stem','Grip') else (charcoal if n in ('Collar','Retainer','bridge') else ((32,34,33) if n=='serviceCover' else (gauge if n in ('cellAlt','A3-J1-plug') else case)))))
    add(cq.importers.importStep(str(HERE.parent/'reel-dfm-r0001/rotor.step')).val(),'Rotor',charcoal)
    data=base64.b64encode(scene.export(file_type='glb')).decode()
    modules=ROOT/'game/src/node_modules'
    boot=(BASE/'viewer.js').read_text().split('const views=')[0]
    tmpl=(BASE/'viewer-template.html').read_text(encoding='utf8')
    controls='<nav aria-label="Fit sequence">'+''.join(f'<button data-step="{i}">{i+1}. {name}</button>' for i,name in enumerate(['Housing and diffuser','Lower shelf','Slide shelf','Fasten shelf','Lower boards','Power and gauges','Seat display','Secure bezel from rear']))+'</nav>'
    before,rest=tmpl.split('<nav ',1);_,after=rest.split('</nav>',1);tmpl=before+controls+'<button id="inspect-light">Inspect status light</button>'+after
    tmpl=tmpl.replace('Case-mounted PCB','Enclosure fit R0004').replace('Case board R0001','R0004 fit sequence').replace('The design uses a 0.8 mm PCB and two M2 × 4 screws. The power-lead view shows the three located routes. The display, other electronics and service connector are outside this view.','The colored gauges reproduce occupied space. Insert the shelf before the battery bridge, display and wires. Check the actual soldered lamp, connector and wire bundle in a separate unpowered assembly.')
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);(p/'src.js').write_text(boot+(HERE/'views.js').read_text(encoding='utf8'),encoding='utf8')
        exe=modules/('@esbuild/win32-x64/esbuild.exe' if os.name=='nt' else '.bin/esbuild')
        subprocess.run([str(exe),str(p/'src.js'),'--bundle','--minify','--format=iife','--legal-comments=none','--outfile='+str(p/'out.js')],check=True,env={**os.environ,'NODE_PATH':str(modules)})
        (HERE/'Enclosure-fit-guide.html').write_bytes(tmpl.replace('@@SCENE@@',data).replace('@@JS@@',(p/'out.js').read_text()).replace('@@LICENSE@@',(ROOT/'third-party/three-LICENSE.txt').read_text()).encode())
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
