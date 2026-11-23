"""Verify mating geometry, sampled sweep envelope, physical-project inventory, and native slices."""
import argparse
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from lxml import etree as E
from build import (HERE,C,P,MATRIX,SAMPLE_NAMES,TINY,EXCLUDE,SOURCE,block,digest,geometry,
                   meta,read_mesh,save)

def geometric_checks(src):
    assert digest(src)==SOURCE
    with ZipFile(src) as archive:
        top=E.fromstring(archive.read('3D/3dmodel.model'))
        old={}
        for oid in SAMPLE_NAMES:
            comp=top.find(f".//{C}object[@id='{oid}']/{C}components")[0]
            node=E.fromstring(archive.read(comp.get(P+'path').lstrip('/')))
            old[oid]=read_mesh(node.find(C+'resources'),comp.get('objectid'))
    shapes,housing,wheel=geometry(old)
    c=shapes['61']; carrier0=old['61']; added=(c-carrier0).as_original()
    kept=(carrier0-c).volume()
    outside_keys=(added^block((-40,-20,-.1),(40,-9,8))).volume()
    post=(added^block((-40,-20,1.43),(40,20,8))).volume()
    flat=(added^block((-40,-20,-.1),(40,20,.599))).volume()
    stock=carrier0.transform(MATRIX); trial=c.transform(MATRIX)
    cross=[]
    for x in (-25,-20,-15,-12,12,15,20,25):
        a=carrier0.rotate((0,-90,0)).slice(x).area()
        b=c.rotate((0,-90,0)).slice(x).area()
        cross.append(dict(x=x,r19b_mm2=round(a,4),r20_mm2=round(b,4)))
        assert b>a+.6
    assert kept<1e-6 and max(outside_keys,post,flat)<1e-6
    shell_volume=(housing^trial).volume()
    assert shell_volume<.0001 and (added.transform(MATRIX)^housing).volume()<1e-7
    sample=shapes['9']; assert (sample^trial).volume()<1e-7
    # Along the original rotor axis, the entire original encoder socket and stop
    # survive on the negative-X side of -4.75 mm.
    shaft=block((-20,-20,-20),(-4.75,20,20)); a=old['40']^shaft;b=wheel^shaft
    delta=(a-b).volume()+(b-a).volume()
    assert delta<1e-6
    # Compare each circumferential sweep radius at the same axial station.
    # Fixed shaft index and press fit still require measurements on a real encoder.
    before=old['40'].rotate((0,-90,0)); after=wheel.rotate((0,-90,0))
    center=np.array([-1.275,0.])
    worst=-100
    for x in np.linspace(-4.73,3.519,166):
        radii=[]
        for shape in (before,after):
            contours=shape.slice(x).to_polygons()
            radii.append(max(np.linalg.norm(poly-center,axis=1).max() for poly in contours))
        worst=max(worst,radii[1]-radii[0])
    assert worst<.003
    return dict(r19b_sha256=SOURCE,carrier_print_to_installed_mm=MATRIX,carrier_new_material_mm3=round(added.volume(),5),
        carrier_material_removed_mm3=round(kept,8),rib_bounds=added.bounding_box(),new_material_at_floor_keys_mm3=outside_keys,
        new_material_at_posts_or_seats_above_1_43_mm3=post,new_material_below_web_top_mm3=flat,arm_sections=cross,
        housing_intersection_mm3={'R19b_original_carrier':round((housing^stock).volume(),8),'R20_carrier':round(shell_volume,8),
                                  'R20_added_ribs_only':round((housing^added.transform(MATRIX)).volume(),8)},
        nominal_carrier_floor_sample_intersection_mm3=round((sample^trial).volume(),8),encoder_shaft_comparison={'region':'Original rotor X <= -4.75 mm includes blind socket, rear shoulder and original shaft',
             'original_volume_mm3':round(a.volume(),5),'symmetric_difference_mm3':round(delta,8)},
        wheel_volume_mm3={'R19b_folding_rotor':round(old['40'].volume(),3),'R20_inert_thumbwheel':round(wheel.volume(),3)},
        wheel_radius_check={'axial_positions':166,'axial_range_mm':[-4.73,3.519],'maximum_R20_minus_R19b_radius_mm':round(float(worst),8)},
        physical_status='unprinted; clearances are nominal triangulated R19b values; retention, torque, wear and electronics clearance outside the reviewed regions remain open')

def inventory(archive):
    with ZipFile(archive) as z:
        cfg=E.fromstring(z.read('Metadata/model_settings.config'))
        props=__import__('json').loads(z.read('Metadata/project_settings.config'))
        root=E.fromstring(z.read('3D/3dmodel.model'))
        assert set(o.get('objectid') for o in root.find(C+'build'))==set(o.get('id') for o in cfg.findall('object'))
        result={}
        for p in cfg.findall('plate'):
            entries={}
            for i in p.findall('model_instance'):
                oid=meta(i,'object_id');obj=cfg.find(f"object[@id='{oid}']")
                k=meta(i,'identify_id')
                entries[k]=dict(name=meta(obj,'name'),extruder=meta(obj,'extruder'),
                                brim=meta(obj,'brim_type'),support=meta(obj,'enable_support'))
            result[meta(p,'plater_id')]=dict(name=meta(p,'plater_name'),bed=meta(p,'bed_type'),instances=entries)
        return dict(project_sha256=digest(archive),printer=props['printer_settings_id'],process=props['print_settings_id'],
                    materials=props['filament_settings_id'],nozzle_offset=props['extruder_offset'],plates=result)

if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('work',type=Path)
    args=parser.parse_args();qa=HERE/'QA';save(qa/'nominal-fit.json',geometric_checks(args.source))
    old=inventory(args.source)
    full=inventory(HERE/'Print/Pocket-Reel-R20-Unpowered-Fit-X1C.3mf')
    first=inventory(HERE/'Print/Pocket-Reel-R20-First-Article-X1C.3mf')
    assert len(old['plates'])==len(full['plates'])==4 and len(first['plates'])==1
    assert {k for p in full['plates'].values() for k in p['instances']}=={k for p in old['plates'].values() for k in p['instances']}-{'524','508','1150'}
    assert len(first['plates']['1']['instances'])==8 and all(m['support']=='0' and m['brim']=='no_brim' for m in first['plates']['1']['instances'].values())
    runs={}
    for name,project in [('r19baseline',old),('verified',full),('reopen-verified',full),('first-article',first),('first-reopen',first)]:
        folder=args.work/name;native=folder/'result.json'; report=json.loads(native.read_text(encoding='utf8'))
        assert report['return_code']==0
        plates=[]
        for plate in report['sliced_plates']:
            number=plate['id']; expected=project['plates'][str(number)]['instances']
            assert plate['warning_message']=='' and plate['filament_change_times']==0
            assert sorted(r['name'] for r in plate['objects'])==sorted(r['name'] for r in expected.values())
            plates.append(dict(id=number,objects=len(expected),warning=plate['warning_message'],material_changes=0,
                estimate_minutes=round(plate['total_predication']/60,2),estimate_g=round(sum(f['total_used_g'] for f in plate['filaments']),2),
                deposited_gcode_sha256=digest(folder/f'plate_{number}.gcode')))
        assert len(plates)==len(project['plates'])
        runs[name]=dict(input_editable_sha256=project['project_sha256'],output_sliced_3mf_sha256=digest(folder/'sliced.3mf'),
                        native_result_sha256=digest(native),plates=plates)
    save(qa/'native-projects.json',dict(native_version='BambuStudio 02.09.01.70',R19b=old,R20_full=full,R20_first_article=first,runs=runs))
