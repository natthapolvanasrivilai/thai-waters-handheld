"""Transfer STEP/XCAF surface colours by exact installed face centre and area.
Usage: python vendor_colours.py path/to/placed/BREP-directory output.json
"""
import argparse,base64,json,math,zlib
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_LabelSequence
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.XCAFPrs import XCAFPrs,XCAFPrs_IndexedDataMapOfShapeStyle
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import Quantity_TOC_sRGB
ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/'hardware/mechanical/rev-E/scripts/inputs'
def signature(face,transform):
    x,y,z=transform(*face.Center().toTuple())
    return round(x,3),round(y,3),round(z,3),round(face.Area(),3)
def colors(path,transform):
    doc=TDocStd_Document(TCollection_ExtendedString('XCAF'))
    importer=STEPCAFControl_Reader();importer.SetColorMode(True)
    importer.ReadFile(str(path));assert importer.Transfer(doc)
    roots=TDF_LabelSequence();XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()).GetFreeShapes(roots)
    entries=[]
    for label in roots:
        m=XCAFPrs_IndexedDataMapOfShapeStyle()
        XCAFPrs.CollectStyleSettings_s(label,TopLoc_Location(),m)
        for i in range(1,m.Extent()+1):
            style=m.FindFromIndex(i)
            if style.IsSetColorSurf():
                rgb=tuple(round(c*255) for c in style.GetColorSurf().Values(Quantity_TOC_sRGB))
                shape=cq.Shape.cast(m.FindKey(i))
                entries.append((int(shape.wrapped.ShapeType()),shape,rgb))
    faceColors={}
    # More specific face styling takes precedence over a compound default.
    for _,shape,rgb in sorted(entries,key=lambda entry:entry[0]):
        for face in shape.Faces():faceColors[signature(face,transform)]=rgb
    return faceColors
def compressed(a,dtype):
    return base64.b64encode(zlib.compress(np.asarray(a,dtype=dtype).tobytes(),9)).decode()
def mesh_style(result,key,shape,src):
    v=[];tr=[];tints=[];matched=0;total=0
    for face in shape.Faces():
        col=src.get(signature(face,lambda x,y,z:(x,y,z)))
        if col:matched+=1
        total+=1
        pts,indices=face.tessellate(.065,.18)
        if not indices:continue
        start=len(v);v.extend(tuple(round(d*100) for d in q.toTuple()) for q in pts)
        tr.extend(tuple(start+k for k in tri) for tri in indices)
        tints.extend([col or (132,134,130)]*len(pts))
    if matched:
        result[key]=dict(v=compressed(v,'<i2'),t=compressed(tr,'<u4'),c=compressed(tints,'u1'),styledFaces=matched,faceCount=total)
    print(key,matched,total,flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('solids',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    result={}
    for prefix,file,transform in [('A1','Waveshare.stp',lambda x,y,z:(y,-x,z+27.4)),('A2','AS5600.step',lambda x,y,z:(z+39.48,x-12.7,y+5.91))]:
        src=colors(ORIGINAL/file,transform)
        for fn in sorted(args.solids.glob(prefix+'-*.brep')):
            mesh_style(result,fn.stem,cq.Shape.importBrep(str(fn)),src)
    battery=ROOT/'hardware/mechanical/rev-F/review/inputs/Adafruit-258.step'
    offset=(-10.4,-.65,3.6)
    src=colors(battery,lambda x,y,z:(x+offset[0],y+offset[1],z+offset[2]))
    mesh_style(result,'cellAlt',cq.importers.importStep(str(battery)).val().translate(offset),src)
    if not result:raise ValueError('No matching supplier face colours')
    args.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
if __name__=='__main__':main()
