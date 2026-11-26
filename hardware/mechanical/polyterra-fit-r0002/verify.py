"""Audit native multi-plate slice and separate reopens of every plate."""
from kit import *
from shapely.geometry import box,Point,LineString
from shapely.ops import unary_union
sys.path.insert(0,str(BASE))
from audit import read as native_read,motion_digest
from path_evidence import inspect
sys.path.insert(0,str(BASE.parent/'TW-A-0001-R0014/Printing'))
from rail_paths import footprints
from concurrent.futures import ProcessPoolExecutor
def plate(job):
    root,n=job;whole=root/'final0';single=root/f'final{n}'
    objects=native_read(single);assert objects['status']=='pass',objects['warnings']
    objs=objects['objects'];ids={r['object_id'] for r in objs};assign=json.loads((BASE.parent/'enclosure-print-r0004/assignments.json').read_bytes())
    assert ids=={r['instance'] for r in assign if r['plate']==n}
    records=[];single_digest=motion_digest(single/f'plate_{n}.gcode');full_digest=motion_digest(whole/f'plate_{n}.gcode')
    for fol in ([whole,single] if full_digest!=single_digest else [whole]):
        g=fol/f'plate_{n}.gcode'
        t=g.read_text();assert all(s in t for s in (';curr_bed_type=Supertack Plate','M190 S45','M109 S220','; nozzle_diameter = 0.4'))
        path,first=inspect(g,True,focus=ids);rows=[]
        for obj in objs:
            i=obj['object_id'];r=path[i];starts=[]
            for item in r['model_component_backing']['fully_unbacked_components']:
                z=item['z'];p=footprints(g,box(*item['bbox']),z-.405,z,object_id=i)
                patch=p[z]['model'];under=[(h,patch.intersection(k['support']).area/patch.area) for h,k in p.items() if h<z and 'support' in k]
                good=[(h,f) for h,f in under if f>.30]
                assert good,(fol.name,i,z,under)
                h,f=max(good);starts.append(dict(z=z,support_z=h,overlap_pct=round(100*f,2),area_mm2=item['area_mm2']))
            row=dict(instance=i,part=obj['name'],layers=obj['model_layers'],contact_mm2=r['first_model_contact_mm2'],model_mm3=r['model_mm3'],support_mm3=r['support_mm3'],starts=starts)
            if i in ('385','396'):
                areas={k:unary_union([LineString(pts).buffer(w/2) for group,w,pts in first[i] if group==k]) for k in ('support','model','brim')}
                with zipfile.ZipFile(OUT) as zz:files={k:zz.read(k) for k in zz.namelist()}
                rt=E.fromstring(files[MODEL]);oid=2 if i=='385' else 24;m=read(files,rt,oid)[0];cm=Point(*(m.center_mass[:2]+[128,126]))
                hull=unary_union(list(areas.values())).convex_hull
                assert hull.contains(cm);row['base_margin_mm']=round(cm.distance(hull.boundary),2)
            assert row['layers']>1 and row['contact_mm2']>0;rows.append(row)
        records.append(rows)
    with zipfile.ZipFile(whole/'sliced.3mf') as zz:
        el=E.fromstring(zz.read('Metadata/slice_info.config')).findall('plate')[n-1];f,=el.findall('filament')
        assert f.get('id')==str([1,2,1,4,5,6,6,3][n-1]) and f.get('type')=='PLA'
    return dict(plate=n,grams=float(f.get('used_g')),seconds=int(el.find("metadata[@key='prediction']").get('value')),full_moves_sha256=full_digest,independent_moves_sha256=single_digest,parts=records[0],independent_checks=records[1:] or 'identical movements')
def run(root):
    assert native_read(root/'final0')['status']=='pass'
    f=source()
    with zipfile.ZipFile(OUT) as z:
        assert f['Metadata/project_settings.config']==z.read('Metadata/project_settings.config')
        assert all(f[k]==z.read(k) for k in f if k.startswith('3D/Objects/') and k not in ('3D/Objects/object_1.model','3D/Objects/object_12.model'))
    with ProcessPoolExecutor(3) as pool:rows=list(pool.map(plate,[(root,n) for n in range(1,9)]))
    assert sum(len(x['parts']) for x in rows)==27
    (HERE/'slice-review.json').write_text(json.dumps(dict(project=OUT.name,sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),plates=rows),indent=2)+'\n')
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
