"""Check the old and candidate case seats and the actual sliced gauge paths."""
from pathlib import Path
import sys,json,hashlib
from mount import HERE,ROOT,SCREWS,BACK,OLD_MOUNTS,OLD_REST,mounted,support,cq,stock,BASE,cyl
from gauge import OUT
from shapely.geometry import Point
sys.path.insert(0,str(ROOT/'hardware/mechanical/polyterra-fit-r0001'))
from audit import read
from path_evidence import inspect
sys.path.insert(0,str(ROOT/'hardware/mechanical/TW-A-0001-R0014/Printing'))
from rail_paths import footprints
from fit import bounds

def check(folder):
    g=folder/'plate_1.gcode'
    review=read(folder)
    assert review['status']=='pass' and len(review['objects'])==1
    obj=review['objects'][0]
    paths,_=inspect(g,True,focus={obj['object_id']})
    result=paths[obj['object_id']]
    assert result['model_mm3']>0 and result['support_mm3']==0 and not result['model_component_backing']['fully_unbacked_components']
    text=g.read_text()
    assert all(t in text for t in (';curr_bed_type=Supertack Plate','M190 S45','M109 S220','; nozzle_diameter = 0.4'))
    source=stock(HERE/'pcb-gauge.step')
    b=bounds(source);center=[(b[j]+b[j+1])/2 for j in (0,2)]
    assert '; extruder_offset = 0x2' in text
    pilots=[]
    for x,y in SCREWS:
        zone=Point(128+x-13-center[0],126-14-y-center[1])
        layers=footprints(g,zone.buffer(2.5),.19,.81,object_id=obj['object_id'])
        for z in (.2,.4,.6,.8):
            polymer=layers[z]['model']
            assert zone.buffer(.85).intersection(polymer).area<.001 and zone.buffer(2.5).intersection(polymer).area>2,(x,y,z,zone.wkt,zone.buffer(.85).intersection(polymer).area,zone.buffer(2.5).intersection(polymer).area,polymer.bounds,center)
        pilots.append({'installed_xy_mm':[x,y],'open_core_diameter_mm':1.7,'layers_checked':4})
    installed=source.rotate((0,0,0),(1,0,0),180).translate((13,-14,BACK))
    checks={}
    old=[support(kx-87,ky-114,i) for i,(kx,ky) in enumerate(OLD_MOUNTS,1)]+[support(*OLD_REST,3)]
    new=mounted()
    for label,path,seats in [('R0008',BASE,old),('R0002 mount',HERE/'housing.step',[new[k] for k in ('boss 1','boss 2','rest')])]:
        volume=stock(path).intersect(installed).Volume()
        witness=installed.translate((0,0,-.01))
        areas=[round(s.intersect(witness).Volume()/.01,2) for s in seats]
        assert volume<.001 and min(areas)>1,(label,volume,areas)
        checks[label]={'gauge_interference_mm3':round(volume,5),'seat_contact_mm2_10um_witness':areas}
    stats=json.loads((folder/'result.json').read_bytes())['sliced_plates'][0]
    out={'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'native':review,'model_layers':obj['model_layers'],
         'bed_contact_mm2':result['first_model_contact_mm2'],'support_mm3':result['support_mm3'],'main_filament_g':stats['filaments'][0]['main_used_g'],
         'pilot_checks':pilots,'installed_checks':checks}
    (HERE/'gauge-check.json').write_text(json.dumps(out,indent=2)+'\n')
    print(checks)
if __name__=='__main__':check(Path(sys.argv[1]))
