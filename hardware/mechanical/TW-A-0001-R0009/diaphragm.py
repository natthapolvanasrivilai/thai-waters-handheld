"""Define the two opaque TPU regions of one captive socket diaphragm and write their printable 3MF."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED,ZipFile
import cadquery as cq
import numpy as np
from build import HERE,tracking_regions,shield_mask

def main():
    p=HERE/"Installed"/"diaphragm";p.mkdir(parents=True,exist_ok=True)
    meta=json.loads((HERE/"part-orientations.json").read_text())["usb-c-shield-mask"]
    mat=np.array(meta["assembly_to_print"])
    core="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("",core)
    root=ET.Element("{"+core+"}model",unit="millimeter")
    res=ET.SubElement(root,"resources");colors=ET.SubElement(res,"basematerials",id="1")
    for n,c in [("Case-colour opaque TPU 95A","#82988EFF"),("Charcoal opaque TPU 95A","#292C2AFF")]:
        ET.SubElement(colors,"base",name=n,displaycolor=c)
    for k,s in tracking_regions().items():
        s.exportBrep(str(p/(k+".brep")))
    for i,(k,s) in enumerate(tracking_regions(free=True).items()):
        obj=ET.SubElement(res,"object",id=str(i+2),type="model",name=k,pid="1",pindex=str(i))
        mesh=ET.SubElement(obj,"mesh");vs=ET.SubElement(mesh,"vertices");ts=ET.SubElement(mesh,"triangles")
        pts,faces=s.tessellate(.01,.05)
        xyz=np.array([q.toTuple() for q in pts])@mat[:3,:3].T+mat[:3,3]
        # CAD emits separate face vertices. Weld the boundary before 3MF export.
        unique,index=np.unique(np.rint(xyz*1e6).astype(int),axis=0,return_inverse=True)
        for x,y,z in unique/1e6:ET.SubElement(vs,"vertex",x=str(x),y=str(y),z=str(z))
        for a,b,c in index[np.array(faces)]:ET.SubElement(ts,"triangle",v1=str(a),v2=str(b),v3=str(c),pid="1",p1=str(i),p2=str(i),p3=str(i))
    both=ET.SubElement(res,"object",id="4",type="model",name="USB-C rear diaphragm")
    assembly=ET.SubElement(both,"components")
    for i in (2,3):ET.SubElement(assembly,"component",objectid=str(i))
    ET.SubElement(ET.SubElement(root,"build"),"item",objectid="4")
    with ZipFile(HERE/"Print/usb-c-shield-mask-two-colour.3mf","w",ZIP_DEFLATED) as z:
        z.writestr("3D/3dmodel.model",ET.tostring(root,encoding="utf-8",xml_declaration=True))
        z.writestr("[Content_Types].xml",'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="model" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
if __name__=="__main__":main()
