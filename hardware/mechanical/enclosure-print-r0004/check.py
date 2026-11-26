"""Validate native output for every plate including actual deposited material and footprint."""
from pathlib import Path
from zipfile import ZipFile
import sys,json,hashlib
from lxml import etree as E
from color_project import HERE,OUT,PLATES,COLORS
sys.path.insert(0,str(HERE.parents[2]/'tools'))
sys.path.insert(0,str(HERE.parent/'pocket-reel-r19b-removal-trial'))
from verify_model_extrusion import audit
from path_evidence import inspect
def run(root):
    report=audit(root/'sliced.3mf',root/'result.json',None,None)
    assert report['status']=='pass',report.get('warnings')
    expected=json.loads((HERE/'assignments.json').read_bytes())
    assert len(expected)==len(report['objects'])==27
    with ZipFile(root/'sliced.3mf') as z:
        info=E.fromstring(z.read('Metadata/slice_info.config'))
        assert len(info.findall('plate'))==8
        seq=json.loads(z.read('Metadata/filament_sequence.json'))
    results=[]
    for idx,(name,slot) in enumerate(PLATES,1):
        plate=info.findall('plate')[idx-1]
        f,=plate.findall('filament')
        assert int(f.get('id'))==slot and f.get('color')==COLORS[slot-1] and f.get('type')==('TPU' if slot==5 else 'PETG')
        assert seq[f'plate_{idx}']['sequence']==[slot] and f.get('used_for_object')=='true'
        g=root/f'plate_{idx}.gcode'
        assert ';curr_bed_type='+('Textured PEI Plate' if slot==5 else 'Engineering Plate') in g.read_text(encoding='utf8')
        actual={r['object_id']:r for r in report['objects'] if r['plate']==idx}
        intended={r['instance']:r for r in expected if r['plate']==idx}
        assert actual.keys()==intended.keys()
        paths,_=inspect(g,track_layers=True,focus=set(actual))
        for i,k in actual.items():
            p=paths[i]
            results.append(dict(plate=idx,name=k['name'],height_mm=round(k['mesh_top_mm']-k['mesh_bottom_mm'],3),actual_filament=f.get('type'),actual_colour=f.get('color'),slot=slot,
              first_layer_mm2=p['first_model_contact_mm2'],support_mm3=p['support_mm3'],model_layers=k['model_layers'],unbacked_starts=p['model_component_backing']['fully_unbacked_components']))
        print(idx,[(r['name'],round(r['first_layer_mm2'],1),len(r['unbacked_starts'])) for r in results if r['plate']==idx],flush=True)
    (HERE/'verified-plates.json').write_text(json.dumps({'project_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'objects':results},indent=2)+'\n')
if __name__=='__main__':run(Path(sys.argv[1]))
