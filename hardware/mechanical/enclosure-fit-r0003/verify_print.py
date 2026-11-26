"""Audit actual paths on every native instance and reproduce the changed plates."""
import sys,json,hashlib,csv
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'reel-dfm-r0001'))
import paths,thickness
sys.path.insert(0,str(HERE.parents[2]/'tools'))
from verify_model_extrusion import audit
from path_evidence import inspect
def run(root):
    full=root/'all'
    result=audit(full/'sliced.3mf',full/'result.json',None,None)
    assert result['status']=='pass' and len(result['objects'])==30,result
    (HERE/'deposition.json').write_text(json.dumps(result,indent=2)+'\n')
    paths.HERE=HERE;paths.main(full)
    rows=json.loads((HERE/'part-paths.json').read_bytes())
    assert len(rows)==30 and all(not r['model_component_backing']['fully_unbacked_components'] for r in rows)
    replay={}
    for i in (1,2,7):
        d=root/f'reopen{i}'
        repeat=audit(d/'sliced.3mf',d/'result.json',None,None)
        assert repeat['status']=='pass'
        expected=[r for r in result['objects'] if r['plate']==i]
        assert [(r['name'],r['model_layers']) for r in expected]==[(r['name'],r['model_layers']) for r in repeat['objects']]
        ids={r['object_id'] for r in expected}
        check,_=inspect(d/f'plate_{i}.gcode',True,focus=ids)
        for row in expected:
            orig=next(r for r in rows if r['name']==row['name'])
            new=check[row['object_id']]
            assert len(new['model_component_backing']['fully_unbacked_components'])==len(orig['model_component_backing']['fully_unbacked_components'])
            assert abs(new['first_model_contact_mm2']-orig['first_model_contact_mm2'])<.1
        replay[i]=dict(checked=len(ids),native_result_sha256=hashlib.sha256((d/'result.json').read_bytes()).hexdigest())
    (HERE/'reopen.json').write_text(json.dumps(replay,indent=2)+'\n')
    thickness.PROJECT=next(HERE.glob('*.3mf'));thickness.HERE=HERE;thickness.run()
if __name__=='__main__':run(Path(sys.argv[1]))
