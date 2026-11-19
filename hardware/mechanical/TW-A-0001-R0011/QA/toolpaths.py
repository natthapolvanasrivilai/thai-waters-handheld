"""Measure isolated model starts in Bambu's relative-extrusion toolpath, excluding support and brim."""
import argparse
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely import LineString, union_all

FIELDS = re.compile(r"(?:^| )([XYIJE])([-.\d]+)")
AUX = {"Brim", "Custom", "Skirt", "Prime tower"}
GRID = 0.10

def inspect(path, captures=None):
    bbox = json.loads((path.parent / "result.json").read_text())["sliced_plates"][0]["objects"][0]["bbox"]
    origin = [bbox["x"]-1, bbox["y"]-1]
    size = tuple(math.ceil((bbox[k]+2)/GRID)+1 for k in ("width","depth"))
    def blank():
        return Image.new("L", size)
    img = blank()
    draw = ImageDraw.Draw(img)
    support = blank()
    support_draw = ImageDraw.Draw(support)
    previous = None
    z = 0
    last_model_z = None
    bed_beads = []
    first = None
    starts = []
    role = "Custom"
    width = .42
    x = y = 0
    layers = 0
    def finish():
        nonlocal previous, last_model_z, first, layers
        mask = np.array(img, dtype=bool)
        if captures is not None and z in captures:
            captures[z] = (mask, np.array(support,dtype=bool), origin)
        if not mask.any():
            return
        layers += 1
        labels, count = ndimage.label(mask, structure=np.ones((3,3), dtype=bool))
        if previous is not None and abs(z-last_model_z) < .205:
            overlap = np.bincount(labels[previous], minlength=count+1)
        else:
            overlap = np.zeros(count+1, dtype=int)
        boxes = ndimage.find_objects(labels)
        areas = np.bincount(labels.ravel())
        found = []
        for i in np.flatnonzero(overlap[1:]==0):
            ys, xs = boxes[i]
            dims = [(xs.stop-xs.start)*GRID, (ys.stop-ys.start)*GRID]
            area = areas[i+1]*GRID**2
            # Ignore individual rounding pixels but retain every otherwise detectable birth.
            if area < .05:
                continue
            found.append(dict(area_mm2=round(float(area),2), span_mm=[round(v,2) for v in dims],
                              bed_xy_center_mm=[round(origin[j]+s*GRID/2,2) for j,s in
                                             enumerate((xs.start+xs.stop-1,ys.start+ys.stop-1))]))
        if first is None:
            footprint = union_all(bed_beads)
            polygons = [footprint] if footprint.geom_type=="Polygon" else list(footprint.geoms)
            first = dict(z_mm=z, regions=found, raster_area_mm2=round(float(mask.sum()*GRID**2),2),
                         bead_union_area_mm2=round(footprint.area,2),bead_union_regions=len(polygons))
        else:
            starts.extend(dict(z_mm=z,**row) for row in found)
        previous, last_model_z = mask, z
    for line in path.open(encoding="utf8"):
        if line.startswith("; CHANGE_LAYER"):
            if z: finish()
            img=blank()
            draw=ImageDraw.Draw(img)
            support=blank()
            support_draw=ImageDraw.Draw(support)
            role="Custom"
        elif line.startswith("; Z_HEIGHT:"):
            z=float(line.split(":")[-1])
        elif line.startswith("; FEATURE:"):
            role=line.split(":")[-1].strip()
        elif line.startswith("; LINE_WIDTH:"):
            width=float(line.split(":")[-1])
        elif line.startswith(("G0 ","G1 ","G2 ","G3 ")):
            d={k:float(v) for k,v in FIELDS.findall(line.split(";",1)[0])}
            a,b=d.get("X",x),d.get("Y",y)
            if z and d.get("E",0)>0 and (x!=a or y!=b) and role not in AUX and (not role.startswith("Support") or (captures is not None and z in captures)):
                points=[(x,y),(a,b)]
                if line.startswith(("G2 ","G3 ")):
                    u,v=x+d["I"], y+d["J"]
                    radius=math.hypot(x-u,y-v)
                    start=math.atan2(y-v,x-u)
                    sign=-1 if line.startswith("G2 ") else 1
                    sweep=sign*((sign*(math.atan2(b-v,a-u)-start))%(2*math.pi))
                    # Tessellate to <0.02 mm chord error; use exact end points.
                    step=2*math.acos(max(-1,1-.018/max(radius,.018)))
                    n=max(1,math.ceil(abs(sweep)/step))
                    points=[points[0],*[(u+radius*math.cos(start+sweep*i/n),
                                       v+radius*math.sin(start+sweep*i/n)) for i in range(1,n)],points[1]]
                if first is None and not role.startswith("Support"):
                    bed_beads.append(LineString(points).buffer(width/2,quad_segs=8))
                xy=[(round((i-origin[0])/GRID),round((j-origin[1])/GRID)) for i,j in points]
                w=max(1,round(width/GRID))
                target=support_draw if role.startswith("Support") else draw
                target.line(xy,fill=255,width=w)
            x,y=a,b
    if z: finish()
    return dict(grid_mm=GRID, model_layers=layers, first_model_layer=first, elevated_starts=starts)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plate",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    report=inspect(args.plate)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(report["first_model_layer"])
    print([s for s in report["elevated_starts"] if max(s["span_mm"])>=10])
