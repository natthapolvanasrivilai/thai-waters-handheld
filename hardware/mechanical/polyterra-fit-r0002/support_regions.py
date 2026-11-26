"""Place removable native support modifiers in plate-local machine coordinates."""
from copy import deepcopy
from uuid import uuid5,NAMESPACE_DNS
from kit import *
def modifier(files,root,cfg,oid,id_,bounds,label):
    item=root.find(f".//{CORE}object[@id='{oid}']/{CORE}components")
    comp=deepcopy(item[0]);path=comp.get(PROD+'path').lstrip('/')
    doc=E.fromstring(files[path]);res=doc.find(CORE+'resources')
    obj=E.SubElement(res,CORE+'object',id=str(id_),type='model')
    uid=str(uuid5(NAMESPACE_DNS,'thaiwaters.angled.'+str(id_)))
    obj.set(PROD+'UUID',uid)
    m=E.SubElement(obj,CORE+'mesh');vertices=E.SubElement(m,CORE+'vertices');faces=E.SubElement(m,CORE+'triangles')
    z=float(root.find(f".//{CORE}item[@objectid='{oid}']").get('transform').split()[-1])
    for j,(x0,y0,z0,x1,y1,z1) in enumerate(bounds):
        b=trimesh.creation.box(bounds=[[x0-128,y0-126,z0-z],[x1-128,y1-126,z1-z]])
        for p in b.vertices:E.SubElement(vertices,CORE+'vertex',**dict(zip('xyz',map(str,p))))
        for face in b.faces:E.SubElement(faces,CORE+'triangle',**dict(zip(('v1','v2','v3'),map(str,face+j*8))))
    comp.set('objectid',str(id_));comp.set(PROD+'UUID',str(uuid5(NAMESPACE_DNS,uid)));item.append(comp)
    obj=cfg.find(f"object[@id='{oid}']");part=E.SubElement(obj,'part',id=str(id_),subtype='support_enforcer',uuid=uid)
    meta(part,'name',label);files[path]=encode(doc)
def tune(obj,threshold):
    for k,v in dict(support_threshold_angle=threshold,support_remove_small_overhang=0,support_interface_spacing=.12,support_object_xy_distance=.25,support_interface_top_layers=3).items():meta(obj,k,v)
