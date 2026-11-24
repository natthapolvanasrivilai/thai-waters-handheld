"""Register new CAD in the original native project coordinate systems."""
import json
import cadquery as cq
import numpy as np
from lxml import etree as E
from zipfile import ZipFile
from interfaces import HERE,OLD,build
from project import BASE,mesh,manifold,tr,CORE,PROD,MODEL,RELATIONSHIPS,read_mesh,replace_mesh,encode,value

def apply(files,model,cfg,cache):
    rels=E.fromstring(files[RELATIONSHIPS])
    for oid in (26,30,116):
        wrapper=model.find(f".//{CORE}object[@id='{oid}']")
        child=wrapper.find('.//'+CORE+'component')
        path=child.get(PROD+'path')
        del files[path.lstrip('/')]
        rels.remove(rels.find(f"*[@Target='{path}']"))
        wrapper.getparent().remove(wrapper)
        item=model.find(f".//{CORE}item[@objectid='{oid}']")
        item.getparent().remove(item)
        cfg.remove(cfg.find(f"object[@id='{oid}']"))
        inst=next(n for n in cfg.findall('plate/model_instance') if int(value(n,'object_id'))==oid)
        inst.getparent().remove(inst)
    files[RELATIONSHIPS]=encode(rels)
    names={2:('housing','Housing - single status window and rear screw access'),4:('bezel','Solid-front bezel - concealed hooks'),28:('diffuser','Single RGB diffuser'),114:('rgb-gauge','RGB carrier and emitter fit gauge'),142:('shelf','Status shelf with diffuser stops')}
    for oid,(filename,name) in names.items():
        obj=cfg.find(f"object[@id='{oid}']");part=obj.find('part')
        comp=model.find(f".//{CORE}object[@id='{oid}']/{CORE}components/{CORE}component")
        path=comp.get(PROD+'path').lstrip('/');pid=comp.get('objectid')
        doc=E.fromstring(files[path])
        shape=cq.importers.importStep(str(HERE/(filename+'.step'))).val()
        m=mesh(shape)
        if oid==2:
            # Preserve the original slicer-specific wall and overhang corrections.
            off=np.array([float(value(part,'source_offset_'+k)) for k in 'xyz'])
            shift=np.array([0,0,3.200001004005232])-off
            with ZipFile(BASE) as z: donor=manifold(read_mesh(E.fromstring(z.read(path)),pid))
            ops=[]
            build(cache,False,ops)
            for sign,solid in ops:
                tool=mesh(solid);tool.apply_translation(shift);t=manifold(tool)
                donor=donor-t if sign==-1 else donor+t
            assert donor.status().name=='NoError' and len(donor.decompose())==1
            m=tr(donor.simplify(.001))
        else:
            if oid==4:m.apply_transform(np.array(json.loads((HERE.parent/'TW-A-0001-R0009/part-orientations.json').read_bytes())['bezel']['assembly_to_print']))
            if oid==28:m.apply_transform(np.diag([1.,-1.,-1.,1.]))
            if oid==114:m.apply_transform([[0,1,0,0],[0,0,1,0],[1,0,0,0],[0,0,0,1]]);m.vertices[:,2]*=-1;m.invert()
            m.apply_translation(-m.bounds.mean(axis=0))
        assert m.is_volume and len(manifold(m).decompose())==1,(oid,m.is_watertight,m.is_volume,len(m.faces))
        replace_mesh(doc,pid,m);files[path]=encode(doc)
        for n in (obj,part):n.find("metadata[@key='name']").set('value',name)
        source=part.find("metadata[@key='source_file']")
        if source is not None:source.set('value',filename+'.step')
        part.find('mesh_stat').set('face_count',str(len(m.faces)))
        face=obj.find('metadata[@face_count]')
        if face is not None:face.set('face_count',str(len(m.faces)))
        item=model.find(f".//{CORE}item[@objectid='{oid}']")
        item.set('transform',' '.join(item.get('transform').split()[:-1]+[str(-m.bounds[0,2])]))
