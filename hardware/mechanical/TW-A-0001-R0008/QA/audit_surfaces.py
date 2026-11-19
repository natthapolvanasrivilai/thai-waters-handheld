"""Inventory CAD revolved faces relative to the released print Z (mm, degrees)."""
import argparse
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.BRepAdaptor import BRepAdaptor_Surface

from audit_fit import HERE, REV, MECH, IDS

# Original STL export transforms in rev-G/deliver.py, rev-F/power_key.py,
# rev-F/rod_grip.py, plus the six inherited right-side reel parts.
OLD_UP = {"housing-battery-bay":(0,0,1),"bezel":(0,0,-1),"rotor":(-1,0,0),
          "folding-stem":(0,1,0),"grip":(0,1,0),"collar":(-1,0,0),"power-cap":(0,1,0),
          "rod-grip":(1,0,0),"grip-screw-keeper":(0,0,1),"receiver-nut-keeper":(0,0,1),
          "key-board-retainer-west":(0,0,-1),"battery-wire-bridge":(0,0,1)}
GAUGES = ("PKCELL-max-body-with-wire-sockets","Adafruit-258-CAD-with-PCM-and-stubs")


def baseline_gauges():
    def bore(x):
        return cq.Solid.makeCylinder(.8,6,cq.Vector(x,31.35,2.65),cq.Vector(0,-1,0))
    pk = cq.Solid.makeBox(35.3,62.3,5.3,cq.Vector(-17.65,-31.15,0)).cut(bore(-1.45),bore(1.45))
    shapes = cq.importers.importStep(str(MECH/"rev-F/review/inputs/Adafruit-258.step")).val().Solids()
    return {GAUGES[0]:pk,GAUGES[1]:shapes[0].fuse(*shapes[1:]).clean()}


def inspect(shape, up):
    up=np.asarray(up,dtype=float); up/=np.linalg.norm(up)
    rows=[]
    for index,face in enumerate(shape.Faces()):
        typ=face.geomType()
        if typ=="PLANE":
            continue
        vertices,faces=face.tessellate(.025,.1)
        if not faces:
            continue
        pts=np.array([v.toTuple() for v in vertices],dtype=float)[faces]
        cr=np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0])
        lengths=np.linalg.norm(cr,axis=1)
        valid=lengths>1e-10
        if not np.any(valid):
            continue
        pts=pts[valid]; lengths=lengths[valid]; normal=cr[valid]/lengths[:,None]
        low=normal@up < -math.cos(math.radians(30))-1e-7
        shallow=round(float(np.sum(lengths[low])/2),3)
        record={"face":index,"surface":typ,"sub30_area_mm2":shallow}
        if typ=="CYLINDER":
            c=BRepAdaptor_Surface(face.wrapped).Cylinder()
            axis=np.array(c.Axis().Direction().Coord()); origin=np.array(c.Location().Coord())
            radial=pts.mean(axis=1)-origin
            radial-=np.outer(radial@axis,axis)
            inward=bool(np.median(np.sum(radial*normal,axis=1))<0.)
            horizontal=abs(axis@up) < math.sin(math.radians(1))
            record.update(radius_mm=round(c.Radius(),4),axis=axis.round(4).tolist(),inward=inward,horizontal=bool(horizontal))
            if not shallow and not (inward and horizontal):
                continue
        elif not shallow:
            continue
        box=face.BoundingBox()
        record["assembly_bbox_mm"]=[round(x,2) for x in (box.xmin,box.xmax,box.ymin,box.ymax,box.zmin,box.zmax)]
        rows.append(record)
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("revision",choices=["baseline","candidate"])
    parser.add_argument("--cache",type=Path)
    args=parser.parse_args()
    if args.revision=="baseline":
        shapes={stem:cq.Shape.importBrep(str(args.cache/(key+".brep"))) for stem,key in IDS.items()}
        shapes.update(baseline_gauges())
        ups=OLD_UP | {n:(0,0,1) for n in GAUGES}
    else:
        manifest=json.loads((REV/"part-orientations.json").read_text(encoding="utf-8-sig"))
        shapes={f.stem:cq.Shape.importBrep(str(f)) for f in (REV/"CAD").glob("*.brep")}
        ups={k:v["build_up_assembly"] for k,v in manifest.items()}
    rows={k:inspect(s,ups[k]) for k,s in shapes.items()}
    assert len(rows)==14
    (HERE/(args.revision+"-curved-faces.json")).write_text(json.dumps(rows,indent=2)+"\n",encoding="utf-8")
    for k,features in rows.items():
        h=[r for r in features if r.get("inward") and r["horizontal"]]
        print(k,len(h),sum(r["sub30_area_mm2"]>.001 for r in h),round(sum(r["sub30_area_mm2"] for r in features),2),flush=True)


if __name__=="__main__":
    main()
