"""Produce the native X1C color-separated project from the registered enclosure fit kit."""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import json,sys
import numpy as np
import trimesh
from lxml import etree as E

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'enclosure-fit-r0003'))
from project import read_mesh,replace_mesh,CORE,PROD,MODEL,SETTINGS,encode,value
SOURCE=next((HERE.parent/'enclosure-fit-r0003').glob('*.3mf'))
OUT=HERE/'Thai-Waters-R0004-X1C-Color-Fit.3mf'
COLORS=['#899C89','#303938','#D99A4E','#E6F2F2','#202221','#92979A']
PLATES=[('Sage - housing and lamp shelf',1),('Charcoal - bezel and reel',2),
        ('Sage - rod handle',1),('Clear PETG - single diffuser',4),
        ('Black TPU - mask and cover',5),('Gray - battery gauges',6),
        ('Gray - PCB and component gauges',6),('Amber - controls',3)]
# All placements in local plate coordinates, with room for brim and support.
MOVE={142:(1,43,75),8:(8,105,124),10:(8,128,124),14:(8,151,124),
      36:(6,94,130),38:(6,165,130)}
def meta(node,key,val):
    m=node.find(f"metadata[@key='{key}']")
    if m is None:m=E.SubElement(node,'metadata',key=key)
    m.set('value',str(val))
def palette(p):
    # Native input has three filament profiles and four nozzle/filament variants.
    # Use the installed Generic PETG standard variant for each rigid material.
    for k,v in list(p.items()):
        if not isinstance(v,list):continue
        if len(v)==3:
            p[k]=[v[i] for i in (1,1,1,1,2,1)]
        elif len(v)==4 and k not in ('bed_exclude_area','print_compatible_printers','printable_area','long_retractions_when_ec','retraction_distances_when_ec') and not k.startswith('machine_'):
            p[k]=[v[i] for i in (2,2,2,2,3,2)]
    p.update(filament_colour=COLORS,filament_self_index=list(map(str,range(1,7))),
             flush_volumes_matrix=['0' if i==j else '280' for i in range(6) for j in range(6)],
             flush_volumes_vector=['140']*12,different_settings_to_system=['']*8,
             inherits_group=['']*8,curr_bed_type='Engineering Plate')
NORMALS={24:[0,1,0],38:[0,1,0],8:[0,-.6696,-.7427],10:[0,0,1]}
def build():
    assert sha256(SOURCE.read_bytes()).hexdigest()=='decb53c415f1a33eafd49635c30acf87784dab57a7778e821f133540cd7c93de'
    with ZipFile(SOURCE) as z:files={k:z.read(k) for k in z.namelist()}
    model,cfg=[E.fromstring(files[k]) for k in (MODEL,SETTINGS)]
    from native_parts import apply
    apply(files,model,cfg,Path(sys.argv[1]))
    p=json.loads(files['Metadata/project_settings.config']);palette(p)
    plates=cfg.findall('plate')
    extra=deepcopy(plates[-1])
    for inst in extra.findall('model_instance'):extra.remove(inst)
    plates[-1].addnext(extra);plates.append(extra)
    for i,(plate,(name,slot)) in enumerate(zip(plates,PLATES),1):
        meta(plate,'plater_id',i);meta(plate,'plater_name',f'{i:02d} {name}')
        meta(plate,'bed_type','Textured PEI Plate' if slot==5 else 'Engineering Plate')
        meta(plate,'filament_maps','1 1 1 1 1 1');meta(plate,'filament_volume_maps','0 0 0 0 0 0')
    items={int(i.get('objectid')):i for i in model.find(CORE+'build')}
    report=[]
    for oid,item in items.items():
        inst=next(i for pp in plates for i in pp.findall('model_instance') if int(value(i,'object_id'))==oid)
        plate=plates.index(inst.getparent())+1
        original=np.array(list(map(float,item.get('transform').split())))
        wp=original[-3:].copy()
        if oid in MOVE:
            plate,x,y=MOVE[oid];plates[plate-1].append(inst)
            wp[:2]=(x+307.2*((plate-1)%3),y-307.2*((plate-1)//3))
        slot=PLATES[plate-1][1];obj=cfg.find(f"object[@id='{oid}']")
        meta(obj,'extruder',slot)
        for part in obj.findall("part[@subtype='normal_part']"):meta(part,'extruder',slot)
        # Bake into the native mesh for stable reopen bounds. Set the source transform
        # consistently so a later split/export retains the same bed-facing surface.
        pose='registered face'
        if oid in NORMALS:
            normal=np.asarray(NORMALS[oid],float)
            normal/=np.linalg.norm(normal)
            rot=trimesh.geometry.align_vectors(normal,[0,0,-1])
            c=model.find(f".//{CORE}object[@id='{oid}']/{CORE}components/{CORE}component")
            fn=c.get(PROD+'path').lstrip('/');doc=E.fromstring(files[fn]);pid=c.get('objectid')
            m=read_mesh(doc,pid);m.apply_transform(rot)
            centre=m.bounds.mean(axis=0);m.apply_translation(-centre);wp[2]=m.extents[2]/2
            replace_mesh(doc,pid,m);files[fn]=encode(doc)
            part=obj.find("part[@subtype='normal_part']")
            # Imported source STL coordinates -> recentered object coordinates.
            oldoff=np.array([float(value(part,'source_offset_'+k)) for k in 'xyz'])
            mat=rot.copy();mat[:3,3]=wp - centre - rot[:3,:3]@oldoff
            meta(part,'matrix',' '.join(f'{n:.10g}' for n in mat.flat))
            pose={24:'Broad side of handle mounting foot down',38:'Broad face of battery pack down',8:'Hinge seating face down',10:'Broad face of knob down'}[oid]
            if oid in (24,8):
                for k,v in dict(enable_support=1,support_type='normal(auto)',support_on_build_plate_only=0,brim_type='outer_only',brim_width=5).items():meta(obj,k,v)
        # Also re-seat previous geometry whose oblique/recessed face changed its
        # mesh height upstream (especially the screw-retained bezel).
        if oid==4:
            c=model.find(f".//{CORE}object[@id='4']/{CORE}components/{CORE}component")
            m=read_mesh(E.fromstring(files[c.get(PROD+'path').lstrip('/')]),c.get('objectid'))
            wp[2]=-m.bounds[0,2]
        item.set('transform','1 0 0 0 1 0 0 0 1 '+' '.join(f'{v:.10g}' for v in wp))
        report.append(dict(plate=plate,part=value(obj,'name'),slot=slot,colour=COLORS[slot-1],instance=value(inst,'identify_id'),pose=pose))
    layers=E.fromstring(files['Metadata/layer_config_ranges.xml'])
    # Old handle-only 33 mm local layer-height override was for a vertical grip.
    for entry in layers.findall("object[@id='12']"):layers.remove(entry)
    cuts=E.fromstring(files['Metadata/cut_information.xml'])
    template=deepcopy(cuts[0])
    assert all(n.find('cut_id').get('connectors_cnt')=='0' for n in cuts)
    for n in list(cuts):cuts.remove(n)
    for i in range(len(report)):
        n=deepcopy(template);n.set('id',str(i+1));cuts.append(n)
    files['Metadata/cut_information.xml']=encode(cuts)
    files.update({MODEL:encode(model),SETTINGS:encode(cfg),'Metadata/layer_config_ranges.xml':encode(layers),
                  'Metadata/project_settings.config':json.dumps(p,ensure_ascii=False,indent=2).encode()})
    with ZipFile(OUT,'w') as z:
        for k,v in sorted(files.items()):z.writestr(ZipInfo(k,(2026,11,24,0,0,0)),v,compress_type=ZIP_DEFLATED)
    (HERE/'assignments.json').write_text(json.dumps(sorted(report,key=lambda r:r['plate']),indent=2)+'\n')
if __name__=='__main__':build()
