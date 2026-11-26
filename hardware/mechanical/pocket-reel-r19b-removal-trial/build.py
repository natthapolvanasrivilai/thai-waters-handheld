"""Build an inert fit trial directly from the hash-checked withdrawn R19b native project."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from lxml import etree as E
import manifold3d as mf
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
SOURCE="dcfc3c9c0725d91c54026f1e65f5b9855a036b35f61483d5b1dfcfb471db546c"
C="{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
P="{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
M=mf.Manifold
MATRIX=[[0,0,-1,47],[-1,0,0,0],[0,1,0,13.005]]
EXCLUDE={'27':'proof-only rod grip','42':'held folding crank','44':'engineering-only spring cassette'}
SAMPLE_NAMES={'9':'R20 floor pocket section','40':'R20 spring-free encoder thumbwheel','61':'R20 keyed encoder carrier'}
TINY={'19','21','23','35','37'}

def save(path,data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def meta(el,k):
    return el.find(f"metadata[@key='{k}']").get('value')

def put(el,k,v):
    found=el.find(f"metadata[@key='{k}']")
    if found is None:
        found=E.SubElement(el,'metadata',key=k)
    found.set('value',str(v))

def to_mesh(shape):
    d=shape.to_mesh64()
    return trimesh.Trimesh(d.vert_properties[:,:3],d.tri_verts,process=False)

def read_mesh(resources,pid):
    mesh=resources.find(f"{C}object[@id='{pid}']/{C}mesh")
    vertices=np.array([[float(v.get(k)) for k in 'xyz'] for v in mesh.find(C+'vertices')])
    faces=np.array([[int(v.get(k)) for k in ('v1','v2','v3')] for v in mesh.find(C+'triangles')])
    merged=trimesh.Trimesh(vertices,faces)
    shape=M(mf.Mesh64(np.asarray(merged.vertices),np.array(merged.faces,dtype=np.uint64)))
    assert shape.status()==mf.Error.NoError and len(shape.decompose())==1
    return shape

def install_mounts(housing):
    return housing.rotate((0,45,0)).translate((4.09078566,2.5749988,14.74312))

def block(lo,hi):
    return M.cube(np.subtract(hi,lo)).translate(lo)

def new_wheel(original):
    # In original print coordinates the encoder axis runs along X. Retain the
    # *entire* original mating shaft, blind socket, stop and rear shoulder.
    back=original^block((-20,-20,-20),(-4.72,20,20))
    # Use the actual polygon of the wheel at the continuous solid rear disc.
    # It captures the source OD, centre and tessellation without a fitted circle.
    yz=original.rotate((0,-90,0))
    profile=yz.slice(-4.75)
    assert 508<profile.area()<512
    disc=profile.extrude(6.28).translate((0,0,-4.74))
    # Front rotates inside the checked R19b envelope. The 45-degree bevel
    # starts at X1.52 and ends at X3.52, leaving a broad, continuous bed face.
    lower=profile.extrude(.04).translate((0,0,1.49))
    upper=profile.offset(-2.0).extrude(.02).translate((0,0,3.50))
    inert=back+(disc+M.batch_hull([lower,upper])).rotate((0,90,0))
    return inert

def new_carrier(original):
    # Add a tapered stiffening rib only along the tops of the two long webs.
    # Each shaped rib stays within the web's existing XY projection. The last
    # 4 mm of each tab and the two keys, seating faces and PCB posts are original.
    web=original.slice(.30).offset(-.16)
    additions=[]
    for side in (-1,1):
        xlo,xhi=(9.7,28.25) if side>0 else (-28.25,-9.7)
        patch=web^mf.CrossSection.square((xhi-xlo,1.25)).translate((xlo,-8.93))
        rib=patch.extrude(.85).translate((0,0,.57))
        for x,sign in ((xlo,1),(xhi,-1)):
            # Clip 45-degree ramps into the rib at the root and tip.
            rib=rib.trim_by_plane((sign,0,-1),(sign*x-.58)/np.sqrt(2))
        additions.append(rib)
    revised=original+additions[0]+additions[1]
    return revised

def floor_sample(housing):
    # Exact floor and asymmetric pockets. Crop below the global rear plane so
    # no integral rod receiver or distant shell wall is included in this coupon.
    return housing^block((40,-11,0.1),(48,11,2.50))

def geometry(source):
    housing=install_mounts(source['9'])
    wheel=new_wheel(source['40']); carrier=new_carrier(source['61'])
    coupon=floor_sample(housing)
    for shape in [wheel,carrier,coupon]:
        assert shape.status()==mf.Error.NoError and len(shape.decompose())==1 and shape.volume()>0
    return {'9':coupon,'40':wheel.rotate((0,90,0)),'61':carrier},housing,wheel

def write_mesh(resources,pid,mesh):
    obj=resources.find(f"{C}object[@id='{pid}']")
    old=obj.find(C+'mesh');obj.remove(old)
    node=E.SubElement(obj,C+'mesh');verts=E.SubElement(node,C+'vertices');tris=E.SubElement(node,C+'triangles')
    for v in mesh.vertices:
        E.SubElement(verts,C+'vertex',**{k:format(float(f),'.9g') for k,f in zip('xyz',v)})
    for a,b,c in mesh.faces:
        E.SubElement(tris,C+'triangle',v1=str(a),v2=str(b),v3=str(c))

def xml(node):
    return E.tostring(node,encoding='utf-8',xml_declaration=True)

def package(path,files):
    with ZipFile(path,'w') as out:
        for key,data in sorted(files.items()):
            out.writestr(ZipInfo(key,(2026,11,23,0,0,0)),data,compress_type=ZIP_DEFLATED,compresslevel=6)

def make(source,dest):
    assert digest(source)==SOURCE,'Require exact withdrawn owner R19b project'
    dest.mkdir(exist_ok=True,parents=True)
    with ZipFile(source) as archive:
        files={k:archive.read(k) for k in archive.namelist()}
    main=E.fromstring(files['3D/3dmodel.model']); cfg=E.fromstring(files['Metadata/model_settings.config'])
    relpath='3D/_rels/3dmodel.model.rels'; rels=E.fromstring(files[relpath])
    resources=main.find(C+'resources'); build=main.find(C+'build')
    meshes={}; members={}
    for oid in SAMPLE_NAMES:
        obj=resources.find(f"{C}object[@id='{oid}']");comp=obj.find(C+'components')[0]
        path=comp.get(P+'path').lstrip('/'); m=E.fromstring(files[path]);pid=comp.get('objectid')
        meshes[oid]=read_mesh(m.find(C+'resources'),pid);members[oid]=(m,path,pid)
    shapes,housing,wheel=geometry(meshes)
    mapping={}; samples={}
    for plate in cfg.findall('plate'):
        for ins in plate.findall('model_instance'):
            oid=meta(ins,'object_id');mapping[oid]=(meta(plate,'plater_id'),meta(ins,'identify_id'))
            if oid in EXCLUDE:plate.remove(ins)
    for definition in list(cfg.findall('object')):
        oid=definition.get('id');wrap=resources.find(f"{C}object[@id='{oid}']");component=wrap.find(C+'components')
        item=build.find(f"{C}item[@objectid='{oid}']")
        if oid in EXCLUDE:
            path=component[0].get(P+'path')
            for rel in list(rels):
                if rel.get('Target')==path:rels.remove(rel)
            del files[path.lstrip('/')]
            cfg.remove(definition);resources.remove(wrap);build.remove(item)
            continue
        if oid in shapes:
            root,path,pid=members[oid];lib=root.find(C+'resources')
            for member in list(lib):
                if member.get('id')!=pid:lib.remove(member)
            for child in list(component)[1:]:component.remove(child)
            for child in list(definition.findall('part'))[1:]:definition.remove(child)
            for child in list(definition.findall('metadata')):
                if child.get('key') not in ('name','extruder'):definition.remove(child)
            part=definition.find('part')
            for child in list(part):part.remove(child)
            name=SAMPLE_NAMES[oid];put(definition,'name',name);put(part,'name',name)
            mesh=to_mesh(shapes[oid]);bounds=mesh.bounds;mid=bounds.mean(axis=0)
            outmesh=mesh.copy();outmesh.apply_translation((0,0,-bounds[0,2]));outmesh.export(dest/(name+'.stl'))
            mesh.apply_translation(-mid);write_mesh(lib,pid,mesh)
            files[path]=xml(root)
            x,y=map(float,item.get('transform').split()[-3:-1]);z=(bounds[1,2]-bounds[0,2])/2
            item.set('transform',f'1 0 0 0 1 0 0 0 1 {x} {y} {z:.9f}')
            put(part,'matrix',f'1 0 0 {x} 0 1 0 {y} 0 0 1 {z:.9f} 0 0 0 1')
            E.SubElement(part,'mesh_stat',face_count=str(len(mesh.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
            for key,val in {'enable_support':'0','wall_loops':'4','sparse_infill_density':'30%'}.items():put(definition,key,val)
            samples[name]={'id':mapping[oid][1],'plate':int(mapping[oid][0]),'mesh_volume_mm3':shapes[oid].volume(),
                           'native_to_gcode_translation':[float(x-mid[0]),float(y-mid[1]-2),float(-bounds[0,2])]}
        if oid in shapes or oid in TINY:
            for key,val in {'brim_type':'no_brim','brim_width':'0','wall_generator':'arachne','enable_support':'0'}.items():put(definition,key,val)
    put(cfg.find('plate'),'plater_name','01 Charcoal PETG - inert fit parts and floor pocket')
    files['3D/3dmodel.model']=xml(main);files['Metadata/model_settings.config']=xml(cfg);files[relpath]=xml(rels)
    files['Metadata/layer_heights_profile.txt']=b'';files['Metadata/layer_config_ranges.xml']=b'<?xml version="1.0" encoding="UTF-8"?><objects/>'
    package(dest/'Pocket-Reel-R20-Unpowered-Fit-X1C.3mf',files)
    # The first article has only changed parts, their matching pocket, and the
    # small retainers. Do not ask an operator to enable/disable objects by hand.
    keep=set(SAMPLE_NAMES)|TINY
    for el in list(cfg.findall('object')):
        oid=el.get('id')
        if oid in keep:continue
        wrapper=resources.find(f"{C}object[@id='{oid}']")
        path=wrapper.find(C+'components')[0].get(P+'path')
        cfg.remove(el);resources.remove(wrapper);build.remove(build.find(f"{C}item[@objectid='{oid}']"))
        del files[path.lstrip('/')]
        for rel in list(rels):
            if rel.get('Target')==path:rels.remove(rel)
    first=cfg.find('plate')
    for other in cfg.findall('plate')[1:]:cfg.remove(other)
    for instance in list(first.findall('model_instance')):
        if meta(instance,'object_id') not in keep:first.remove(instance)
    put(first,'plater_name','R20 support-removal and fit samples')
    files['3D/3dmodel.model']=xml(main);files['Metadata/model_settings.config']=xml(cfg);files[relpath]=xml(rels)
    package(dest/'Pocket-Reel-R20-First-Article-X1C.3mf',files)
    return meshes,shapes,housing,wheel,samples

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('r19b',type=Path)
    make(parser.parse_args().r19b,HERE/'Print')
