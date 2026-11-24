"""Read and orient supplier and enclosure solids inside the native X1C project."""
from pathlib import Path
import sys, json, hashlib,zipfile
import numpy as np,trimesh
from lxml import etree as E
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'polyterra-fit-r0001'
SOURCE=next(BASE.glob('*.3mf'))
OUT=HERE/'Thai-Waters-R0006-PolyTerra-SuperTack-X1C.3mf'
CORE='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
PROD='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
MODEL='3D/3dmodel.model'
CFG='Metadata/model_settings.config'
def encode(node):return E.tostring(node,encoding='UTF-8',xml_declaration=True)
def meta(n,k,v):
    m=n.find(f"metadata[@key='{k}']")
    if m is None:m=E.SubElement(n,'metadata',key=k)
    m.set('value',str(v))
def source():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='bd35e50bb2b7cb3a9798d53c2ee64de83905259c7bf73e2b3f321ecfdf2e61e2'
    with zipfile.ZipFile(SOURCE) as z:return {k:z.read(k) for k in z.namelist()}
def read(files,root,oid):
    c=root.find(f".//{CORE}object[@id='{oid}']/{CORE}components/{CORE}component")
    path=c.get(PROD+'path').lstrip('/');xml=E.fromstring(files[path]);m=xml.find(f".//{CORE}object[@id='{c.get('objectid')}']/{CORE}mesh")
    vs=[[float(v.get(k)) for k in 'xyz'] for v in m[0]]
    fs=[[int(t.get(k)) for k in ('v1','v2','v3')] for t in m[1]]
    return trimesh.Trimesh(vs,fs),xml,path
def write(files,path):
    with zipfile.ZipFile(path,'w') as z:
        for k,v in sorted(files.items()):z.writestr(zipfile.ZipInfo(k,(2026,11,24,0,0,0)),v,compress_type=zipfile.ZIP_DEFLATED)
def pose(files,root,cfg,oid,n):
    m,doc,path=read(files,root,oid)
    n=np.array(n,dtype=float);n/=np.linalg.norm(n)
    rot=trimesh.geometry.align_vectors(n,[0,0,-1]);m.apply_transform(rot)
    center=m.bounds.mean(axis=0); rot[:3,3]=-center
    # Apply the identical rigid transform to the model and support exclusions.
    for v in doc.iter(CORE+'vertex'):
        p=rot[:3,:3]@np.array([float(v.get(k)) for k in 'xyz'])-center
        for k,val in zip('xyz',p):v.set(k,f'{val:.8f}')
    files[path]=encode(doc)
    item=root.find(f".//{CORE}item[@objectid='{oid}']")
    wp=list(map(float,item.get('transform').split()[-3:]))
    wp[2]=m.extents[2]/2
    item.set('transform','1 0 0 0 1 0 0 0 1 '+' '.join(f'{x:.10g}' for x in wp))
    obj=cfg.find(f"object[@id='{oid}']")
    for part in obj.findall('part'):
        mnode=part.find("metadata[@key='matrix']")
        if mnode is not None:
            mat=np.array(list(map(float,mnode.get('value').split()))).reshape(4,4)
            tr=np.eye(4);tr[:3,3]=wp
            prior=np.eye(4);prior[:3,3]=-np.array(list(map(float,E.fromstring(source()[MODEL]).find(f".//{CORE}item[@objectid='{oid}']").get('transform').split()[-3:])))
            meta(part,'matrix',' '.join(f'{x:.10g}' for x in (tr@rot@prior@mat).flat))
    return obj
