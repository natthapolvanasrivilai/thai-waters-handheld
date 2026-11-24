"""Verify geometry identity, real native extrusion and isolated-plate replay."""
from pathlib import Path
import csv,json,re,sys,hashlib
from zipfile import ZipFile
from xml.etree import ElementTree as E
from project import HERE,BASE,SOURCE,OUT,MODEL_SETTINGS,PROJECT_SETTINGS,PLATE,PROFILE
sys.path.insert(0,str(HERE.parents[2]/'tools'))
sys.path.insert(0,str(HERE.parent/'pocket-reel-r19b-removal-trial'))
from verify_model_extrusion import audit
from path_evidence import inspect

def sha(data):return hashlib.sha256(data).hexdigest()
def read(root):return audit(root/'sliced.3mf',root/'result.json',None,None)
def geometry():
    with ZipFile(OUT) as z, ZipFile(SOURCE) as src:
        parts=[k for k in src.namelist() if k.startswith('3D/')]
        from support import HOUSING
        assert all(src.read(k)==z.read(k) for k in parts if k!=HOUSING)
        original,revised=[E.fromstring(a.read(HOUSING)) for a in (src,z)]
        assert E.tostring(original.find(".//{*}object[@id='1']"))==E.tostring(revised.find(".//{*}object[@id='1']"))
        # Only the nonprinting support blocker is allowed to differ in this resource.
        for node in (original,revised):
            res=node.find('{*}resources')
            res.remove(res.find("{*}object[@id='301']"))
        assert E.tostring(original)==E.tostring(revised)
        assert set(z.namelist())==set(src.namelist())
        p=json.loads(z.read(PROJECT_SETTINGS))
        assert p['printer_settings_id']=='Bambu Lab X1 Carbon 0.4 nozzle'
        assert p['filament_settings_id']==[PROFILE]*6 and p['curr_bed_type']==PLATE
        cfg=E.fromstring(z.read(MODEL_SETTINGS))
        assert all(node.find("metadata[@key='bed_type']").get('value')==PLATE for node in cfg.findall('plate'))
        return len(parts),p['filament_colour']

def motion_digest(gcode):
    # Compare the actual moves, including feeds, extrusion, retractions and arcs.
    with gcode.open('rb') as f:
        return sha(b''.join(line.split(b';',1)[0].strip()+b'\n' for line in f if line.startswith((b'G0 ',b'G1 ',b'G2 ',b'G3 '))))

def run(root,with_replay):
    geometries,colors=geometry()
    full=root/'plate0';result=read(full)
    assert result['status']=='pass' and len(result['objects'])==27,result['warnings']
    allrows=[];plates=[];support_witness=[];replay_deltas=[]
    assignments=json.loads((BASE/'assignments.json').read_bytes())
    with ZipFile(full/'sliced.3mf') as z:
        info=E.fromstring(z.read('Metadata/slice_info.config'))
        seq=json.loads(z.read('Metadata/filament_sequence.json'))
    for n,p in enumerate(info.findall('plate'),1):
        f,=p.findall('filament')
        slot=[1,2,1,4,5,6,6,3][n-1]
        assert int(f.get('id'))==slot and f.get('type')=='PLA' and f.get('color')==colors[slot-1] and f.get('tray_info_idx')=='GFL01'
        assert seq[f'plate_{n}']['sequence']==[slot]
        g=full/f'plate_{n}.gcode';text=g.read_text(encoding='utf8')
        for line in [';curr_bed_type='+PLATE,'; nozzle_diameter = 0.4','M190 S45','M109 S220','; filament_type = '+';'.join(['PLA']*6)]:
            assert re.search('^'+re.escape(line)+r'(?:\s|;|$)',text,re.M),line
        objs=[r for r in result['objects'] if r['plate']==n]
        ids={r['object_id'] for r in objs}
        assert ids=={r['instance'] for r in assignments if r['plate']==n}
        paths,_=inspect(g,True,focus=ids)
        for r in objs:
            a=paths[r['object_id']]
            assert a['first_model_contact_mm2']>0 and a['model_mm3']>0 and r['model_layers']>1
            unbacked=a['model_component_backing']['fully_unbacked_components']
            for island in unbacked:
                from shapely.geometry import box
                sys.path.insert(0,str(HERE.parent/'TW-A-0001-R0014/Printing'))
                from rail_paths import footprints
                zpos=island['z'];layers=footprints(g,box(*island['bbox']),zpos-.61,zpos,object_id=r['object_id'])
                patch=layers[zpos]['model']
                supports=[(h,grp['support']) for h,grp in layers.items() if h<zpos and 'support' in grp and patch.intersection(grp['support']).area>.001]
                assert supports,(r['name'],island)
                height,base=max(supports,key=lambda pair:pair[0])
                fraction=patch.intersection(base).area/patch.area
                assert zpos-height<=.401 and fraction>.30,(r['name'],island,fraction)
                support_witness.append(dict(part=r['name'],z_mm=zpos,patch_area_mm2=round(patch.area,3),support_at_mm=height,overlap_percent=round(fraction*100,1)))
            allrows.append(dict(plate=n,part=r['name'],layers=r['model_layers'],height_mm=round(r['mesh_top_mm']-r['mesh_bottom_mm'],3),first_layer_mm2=a['first_model_contact_mm2'],model_mm3=a['model_mm3'],support_mm3=a['support_mm3'],supported_starts=len(unbacked)))
        move=motion_digest(g)
        if with_replay:
            repeat=root/f'plate{n}'
            repeat_audit=read(repeat)
            assert repeat_audit['status']=='pass'
            assert sorted((r['object_id'],r['model_layers']) for r in repeat_audit['objects'])==sorted((r['object_id'],r['model_layers']) for r in objs)
            replay_gcode=repeat/f'plate_{n}.gcode'
            repeated_digest=motion_digest(replay_gcode)
            if repeated_digest!=move:
                # Some native support/interface or travel lines vary by slicing context.
                # Require equal layer populations, bed footprints and supported-start
                # locations. Measure support quantity independently of physical-part volume.
                again,_=inspect(replay_gcode,True,focus=ids)
                for k,orig in paths.items():
                    rr=again[k]
                    assert rr['model_component_backing']['fully_unbacked_components']==orig['model_component_backing']['fully_unbacked_components']
                    assert abs(orig['first_model_contact_mm2']-rr['first_model_contact_mm2'])<.05
                    assert abs(orig['model_mm3']-rr['model_mm3'])<=max(.02,.001*orig['model_mm3'])
                    assert bool(orig['support_mm3'])==bool(rr['support_mm3'])
                    replay_deltas.append(dict(plate=n,part=k,whole_job_support_mm3=orig['support_mm3'],plate_job_support_mm3=rr['support_mm3'],model_delta_mm3=round(rr['model_mm3']-orig['model_mm3'],3)))
            else:repeated_digest=move
        else:repeated_digest=None
        plates.append(dict(plate=n,parts=len(objs),model_and_support_g=float(f.get('used_g')),seconds=int(p.find("metadata[@key='prediction']").get('value')),movement_sha256=move,replay_movement_sha256=repeated_digest))
        print(n,len(objs),len(support_witness),flush=True)
    record=dict(project=OUT.name,project_sha256=sha(OUT.read_bytes()),verified_native_geometry_resources=geometries,material=PROFILE,plate=PLATE,nozzle_mm=.4,bed_c=45,nozzle_c=220,independent_replay=with_replay,plates=plates,supported_starts=support_witness,replay_differences=replay_deltas,parts=allrows)
    (HERE/'slice-review.json').write_text(json.dumps(record,indent=2)+'\n')
if __name__=='__main__':run(Path(sys.argv[1]),'--replay' in sys.argv)
