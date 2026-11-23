"""Summarize actual relative-E, XY model/support/brim paths from native X1C G-code."""
from collections import defaultdict
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage
from shapely.geometry import LineString
from shapely.ops import substring,unary_union

HERE=Path(__file__).resolve().parent
FIELDS=re.compile(r"(?:^| )([XYEIJ])(-?(?:\d+\.?\d*|\.\d+))")
FOCUS={'502','506','1201','516','518','520','1101','1102'}

def arc_points(a,b,fields,clockwise):
    x,y=a[0]+fields.get('I',0),a[1]+fields.get('J',0)
    radius=math.dist(a,(x,y));start=math.atan2(a[1]-y,a[0]-x)
    sign=-1 if clockwise else 1
    sweep=sign*((sign*(math.atan2(b[1]-y,b[0]-x)-start))%(2*math.pi))
    if a==b:sweep=2*math.pi*sign
    steps=max(1,math.ceil(abs(sweep)/max(.015,2*math.acos(max(-1,1-.015/max(radius,.015))))))
    return [a,*[(x+radius*math.cos(start+sweep*i/steps),y+radius*math.sin(start+sweep*i/steps)) for i in range(1,steps)],b]

def inspect(path,track_layers=False):
    role='Custom';instance='';z=0.;width=.42;xy=(0.,0.);debt=0.;rel=False;abs_xy=True
    volume=defaultdict(lambda:defaultdict(float)); first=defaultdict(list)
    support_layers=defaultdict(set);layers=defaultdict(lambda:defaultdict(list))
    for text in path.open(encoding='utf8'):
        line=text.strip()
        if line.startswith('; Z_HEIGHT:'):z=float(line.split(':')[1]);instance=''
        elif line.startswith('; FEATURE:'):role=line.split(':')[1].strip()
        elif line.startswith('; LINE_WIDTH:'):width=float(line.split(':')[1])
        elif line.startswith(('; OBJECT_ID:','; start printing object, unique label id:')):instance=line.split(':')[-1].strip()
        elif line.startswith('; stop printing object'):instance=''
        elif line.split(';')[0].strip()=='M83':rel=True
        elif line.split(';')[0].strip()=='M82':rel=False
        elif line.split(';')[0].strip()=='G90':abs_xy=True
        elif line.split(';')[0].strip()=='G91':abs_xy=False
        elif line.startswith(('G0 ','G1 ','G2 ','G3 ')):
            fields={k:float(v) for k,v in FIELDS.findall(line.split(';')[0])}
            new=tuple(fields.get(k,xy[i]) if abs_xy else xy[i]+fields.get(k,0) for i,k in enumerate('XY'))
            old=xy;xy=new
            if 'E' not in fields:continue
            if instance in FOCUS:assert rel and abs_xy
            e=fields['E']
            if e<0:debt-=e;continue
            paid=min(e,debt);debt-=paid
            if instance not in FOCUS or new==old or z<=0 or e-paid<1e-7:continue
            group='support' if role.startswith('Support') else ('brim' if role=='Brim' else 'model')
            if role in {'Custom','Skirt','Prime tower','Flush'}:continue
            volume[instance][group]+=(e-paid)*math.pi*(1.75/2)**2
            if group=='support':support_layers[instance].add(z)
            if abs(z-.2)>.0005 and not (track_layers and group=='model'):continue
            points=arc_points(old,new,fields,line.startswith('G2 ')) if line.startswith(('G2 ','G3 ')) else [old,new]
            if paid>1e-6:
                points=list(substring(LineString(points),paid/e,1,normalized=True).coords)
            if track_layers and group=='model':layers[instance][z].append((width,points))
            if abs(z-.2)<.0005:first[instance].append((group,width,points))
    result={}
    for i,groups in volume.items():
        bed=unary_union([LineString(pts).buffer(w/2,resolution=8) for role,w,pts in first[i] if role=='model'])
        result[i]={'model_mm3':round(groups['model'],3),'support_mm3':round(groups['support'],3),'brim_mm3':round(groups['brim'],3),
                   'support_layers':len(support_layers[i]),'first_model_contact_mm2':round(bed.area,3),
                   'first_model_contact_regions':len(bed.geoms) if hasattr(bed,'geoms') else int(not bed.is_empty)}
        if track_layers:
            result[i]['model_component_backing']=backing(layers[i])
    return result,first

def backing(layers):
    # 0.10 mm raster of swept line widths. Check every new connected component
    # for contact with this object's preceding deposited layer. Partial ledges
    # and real bead adhesion are not determined by a single overlapping pixel.
    all_xy=np.array([pt for layer in layers.values() for _,path in layer for pt in path])
    lo=all_xy.min(axis=0)-1;hi=all_xy.max(axis=0)+1
    size=tuple(np.ceil((hi-lo)*10).astype(int))
    prev=None;previous_lines=[];last=0.;unsupported=[];components=0;refined=[]
    for z,lines in sorted(layers.items()):
        image=Image.new('L',size);draw=ImageDraw.Draw(image)
        for width,pts in lines:
            pixels=[tuple(np.round((np.array(p)-lo)*10).astype(int)) for p in pts]
            draw.line(pixels,fill=255,width=max(1,round(width*10)))
        mask=np.array(image)>0
        labels,count=ndimage.label(mask,structure=np.ones((3,3),bool));components+=count
        if prev is not None:
            seen=set(np.unique(labels[prev])) if z-last<=.205 else set()
            if any(k not in seen for k in range(1,count+1)):
                # Resolve raster-only single pixels using buffered native
                # centreline polygons on this pair of complete layers.
                def swept(paths):
                    return unary_union([LineString(points).buffer(w/2,resolution=12) for w,points in paths])
                current=swept(lines);under=swept(previous_lines)
                pieces=list(current.geoms) if hasattr(current,'geoms') else [current]
                refined.append(dict(z=z,raster_flag_count=sum(k not in seen for k in range(1,count+1)),
                                    refined_component_count=len(pieces)))
                for piece in pieces:
                    if z-last>.205 or not piece.intersects(under):
                        unsupported.append(dict(z=z,area_mm2=round(piece.area,5),bbox=piece.bounds))
        prev=mask;last=z;previous_lines=lines
    return dict(grid_mm=.1,layers=len(layers),components=components,refined_layers=refined,fully_unbacked_components=unsupported)

def draw(before,after,path):
    names=[('506','Reel'),('1201','Encoder carrier'),('1101','Diffuser retainer'),('1102','Card retainer')]
    canvas=Image.new('RGB',(1040,1050),'#FFFFFF');d=ImageDraw.Draw(canvas)
    try:
        font=ImageFont.truetype('arial.ttf',20); small=ImageFont.truetype('arial.ttf',16); title=ImageFont.truetype('arialbd.ttf',30)
    except OSError:font=small=title=ImageFont.load_default()
    d.text((28,18),'First layer on the X1 Carbon',font=title,fill='#152B3D')
    d.text((28,65),'R19b withdrawn print',font=font,fill='#152B3D')
    d.text((545,65),'R20 inert fit trial',font=font,fill='#152B3D')
    colors={'model':'#1A546D','support':'#B83250','brim':'#C57A16'}
    for row,(oid,label) in enumerate(names):
        left,right=before[oid],after[oid]
        bounds=[]
        for paths in (left,right):
            points=np.array([p for _,_,pts in paths for p in pts]);bounds.append((points.min(0),points.max(0)))
        scale=min(min(465/(hi[0]-lo[0]+1),164/(hi[1]-lo[1]+1)) for lo,hi in bounds)
        for col,(paths,(lo,hi)) in enumerate(zip((left,right),bounds)):
            ox=col*515+12;oy=100+row*220
            d.rounded_rectangle((ox,oy,ox+505,oy+210),radius=8,fill='#F4F7F9')
            d.text((ox+12,oy+8),label,font=small,fill='#142D39')
            center=(hi+lo)/2
            for group,w,pts in paths:
                d.line([(ox+252+(x-center[0])*scale,oy+120-(y-center[1])*scale) for x,y in pts],
                       fill=colors[group],width=max(1,round(w*scale)))
    for i,(role,col) in enumerate(colors.items()):
        x=32+i*165;d.rectangle((x,1000,x+18,1017),fill=col);d.text((x+25,997),role.title(),fill='#142D39',font=small)
    d.text((560,997),'Matched scale within each pair. Z = 0.20 mm.',fill='#142D39',font=small)
    canvas.save(path)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('r19b_gcode',type=Path);p.add_argument('r20_gcode',type=Path)
    args=p.parse_args()
    before,old=inspect(args.r19b_gcode);after,new=inspect(args.r20_gcode,track_layers=True)
    assert all(row['support_mm3']==row['brim_mm3']==0 and row['first_model_contact_mm2']>0 for row in after.values())
    qa=HERE/'QA'
    (qa/'removal-paths.json').write_text(json.dumps({'r19b':before,'r20_first_article':after},indent=2)+'\n')
    draw(old,new,qa/'first-layer-comparison.png')
