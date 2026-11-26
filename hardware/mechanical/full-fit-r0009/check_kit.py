"""Compare shipped resources with the design masters and audit full/independent native slices."""
import csv,json,sys
from pathlib import Path
from zipfile import ZipFile
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from shapely.geometry import Point
from complete_project import HERE,PREV,BOARD,OUT,kit,T,E,step_mesh,sha
import verify
from check_faces import load_print,face_audit
from channels import footprints
verify.OUT=OUT
verify.HERE=HERE

def project_check():
    with ZipFile(OUT) as z,ZipFile(next(PREV.glob('*.3mf'))) as old,ZipFile(next(BOARD.glob('*.3mf'))) as gauge:
        resource='3D/Objects/gauge_108.model'
        assert z.read(resource)==gauge.read(resource)
        assert set(z.namelist())==set(old.namelist())
        assert {k for k in z.namelist() if z.read(k)!=old.read(k)}=={kit.CFG,resource,'3D/Objects/object_1.model'}
        mods=lambda a:[E.tostring(node) for node in E.fromstring(a.read('3D/Objects/object_1.model')).iter(kit.CORE+'object') if node.get('id')!='1']
        assert mods(z)==mods(old)
        c=E.fromstring(z.read(kit.CFG));inventory=[]
        for i,p in enumerate(c.findall('plate'),1):
            for it in p.findall('model_instance'):
                def val(o,k):return o.find(f"metadata[@key='{k}']").get('value')
                oid=val(it,'object_id');obj=c.find(f"object[@id='{oid}']")
                inventory.append(dict(plate=i,instance=val(it,'identify_id'),part=val(obj,'name'),filament_slot=val(obj,'extruder')))
    expected=json.loads((HERE.with_name('enclosure-print-r0004')/'assignments.json').read_bytes())
    assert len(inventory)==len(expected)==27
    assert {(r['plate'],r['instance'],int(r['filament_slot'])) for r in inventory}=={(r['plate'],r['instance'],r['slot']) for r in expected}
    shell=load_print(OUT);ref=step_mesh(BOARD/'housing.step');ref.apply_transform(T)
    assert np.array_equal(shell.faces,ref.faces) and np.max(abs(shell.vertices-ref.vertices))<1e-8
    audit=face_audit(shell)
    assert audit['watertight'] and audit['consistent_winding'] and audit['nonmanifold_edges']==0
    assert all(s['reversed_triangles']==0 and abs(s['overlapping_area_mm2'])<1e-7 for s in audit['usb_sides'])
    with (HERE/'inventory.csv').open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(inventory[0]),lineterminator='\n');writer.writeheader();writer.writerows(inventory)
    return dict(housing_step_sha256=sha(BOARD/'housing.step'),gauge_step_sha256=sha(BOARD/'pcb-gauge.step'),board_gauge_resource_matches=True,unchanged_other_object_resources=25,exact_housing_triangles=len(ref.faces),housing=audit)

def gauge_pilots(folder):
    # Use the native on-plate bounding box; align the CAD centre to that box.
    # The X1C profile offsets G-code Y by -2 mm.
    with ZipFile(folder/'sliced.3mf') as z:
        plate=json.loads(z.read('Metadata/plate_7.json'))
        bb,=[r['bbox'] for r in plate['bbox_objects'] if r['name']=='Rectangular control PCB - component-height gauge']
    g=folder/'plate_7.gcode'
    assert '; extruder_offset = 0x2' in g.read_text()
    x0,y0=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2-2
    assert abs(bb[2]-bb[0]-32.4)<.01 and abs(bb[3]-bb[1]-35.8)<.01
    for x,y in [(36,-14.4),(10.5,3.9)]:
        zone=Point(x0+x-22.7,y0+1.1-y)
        layers=footprints(g,zone.buffer(2.5),.19,.81,object_id='1704')
        for z in (.2,.4,.6,.8):
            polymer=layers[z]['model']
            assert zone.buffer(.85).intersection(polymer).area<.001 and zone.buffer(2.5).intersection(polymer).area>2,(x,y,z)
    return 'Both 1.70 mm pilot cores clear through all four substrate layers'

def run(root):
    comparison=project_check()
    assert verify.native_read(root/'final0')['status']=='pass'
    with ProcessPoolExecutor(3) as pool:
        plates=list(pool.map(verify.plate,[(root,n) for n in range(1,9)]))
    assert sum(len(p['parts']) for p in plates)==27
    pilots={k:gauge_pilots(root/k) for k in ('final7','final0')}
    print('All 27 objects verified',flush=True)
    (HERE/'slice-review.json').write_text(json.dumps(dict(sha256=sha(OUT),comparison=comparison,gauge_pilots=pilots,plates=plates),indent=2)+'\n')
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
