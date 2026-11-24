"""Check the low horizontal rod handle where its first ledge begins above support."""
from pathlib import Path
import sys,json
from shapely.geometry import box
from interfaces import HERE
sys.path.insert(0,str(HERE.parent/'TW-A-0001-R0014/Printing'))
from rail_paths import footprints
def check(g):
    row=next(r for r in json.loads((HERE/'verified-plates.json').read_bytes())['objects'] if r['plate']==3)
    where=row['unbacked_starts']; result=[]
    for island in where:
        z=island['z'];rect=box(*island['bbox'])
        layers=footprints(g,rect,z-.8,z,object_id='396')
        island_shape=layers[z]['model']
        support=[(h,group['support']) for h,group in layers.items() if h<z and 'support' in group and group['support'].intersection(island_shape).area>.001]
        if support:
            h,base=max(support,key=lambda item:item[0])
            fraction=base.intersection(island_shape).area/island_shape.area
            result.append(dict(z_mm=z,support_path_z_mm=h,model_area_mm2=island_shape.area,support_overlap_fraction=fraction))
    assert len(result)==len(where) and all(round(r['z_mm']-r['support_path_z_mm'],3)<=.4 and r['support_overlap_fraction']>.3 for r in result),result
    print(result,flush=True)
    (HERE/'handle-support.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':check(Path(sys.argv[1]))
