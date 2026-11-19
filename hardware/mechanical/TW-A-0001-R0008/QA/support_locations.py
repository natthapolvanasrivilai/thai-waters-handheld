"""Locate Bambu support-interface samples under the supplied STL, in assembly millimetres."""
import json
import re
import sys
import numpy as np
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
import vtk
from audit_prints import HERE,REV


def contacts(folder,part,meta):
    role=""; z=0.; pos=np.zeros(2); points=[]
    for line in (folder/"plate_1.gcode").open():
        if line.startswith("; FEATURE: "):
            role=line.strip()[11:]
        if line.startswith("; Z_HEIGHT:"):
            z=float(line.split(":")[1])
        if not line.startswith(("G0 ","G1 ","G2 ","G3 ")):
            continue
        d={a:float(b) for a,b in re.findall(r"(?:^| )([XYE])([-.\d]+)",line)}
        dest=np.array([d.get("X",pos[0]),d.get("Y",pos[1])])
        if role=="Support interface" and d.get("E",0)>0 and ("X" in d or "Y" in d):
            # Sample contact paths at 1 mm maximum spacing. Arc moves are chord approximated.
            n=max(1, int(np.ceil(np.linalg.norm(pos-dest))))
            points.extend([*xy,z] for xy in pos+np.outer((np.arange(n)+.5)/n,dest-pos))
        pos=dest
    pts=np.array(points)
    rec=json.loads((folder/"result.json").read_text())["sliced_plates"][0]["objects"][0]["bbox"]
    rd=vtk.vtkSTLReader();rd.SetFileName(str(REV/"Print"/(part+".stl")));rd.Update()
    poly=rd.GetOutput(); bb=poly.GetBounds()
    # The 3MF bbox min XY is the translated STL min XY (arrangement without rotation).
    offset=np.array([rec["x"]-bb[0],rec["y"]-bb[2],0])
    assert abs(rec["width"]-(bb[1]-bb[0]))<.02 and abs(rec["depth"]-(bb[3]-bb[2]))<.02
    pts-=offset
    locator=vtk.vtkOBBTree();locator.SetDataSet(poly);locator.BuildLocator()
    hit=[]
    for p in pts:
        q=vtk.vtkPoints();ids=vtk.vtkIdList()
        locator.IntersectWithLine(p,p+[0,0,1.0],q,ids)
        if q.GetNumberOfPoints():
            hit.append(q.GetPoint(0))
    t=np.array(meta["assembly_to_print"])
    a=(np.array(hit)-t[:3,3])@t[:3,:3]
    edges=cKDTree(a).query_pairs(3.,output_type="ndarray")
    graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(a),)*2)
    count,labels=connected_components(graph,directed=False)
    out=[]
    for label in np.argsort(np.bincount(labels))[::-1]:
        cloud=a[labels==label]
        out.append(dict(samples=len(cloud),min_xyz=np.round(cloud.min(axis=0),2).tolist(),
                        max_xyz=np.round(cloud.max(axis=0),2).tolist()))
    return {"interface_path_samples":len(pts),"mesh_hits_within_1mm":len(a),"groups_at_3mm":out}


if __name__=="__main__":
    work=Path(sys.argv[1]);meta=json.loads((REV/"part-orientations.json").read_text())
    out={k:contacts(work/"candidate"/k,k,meta[k]) for k in ["housing-battery-bay","rotor"]}
    (HERE/"support-locations.json").write_text(json.dumps(out,indent=2)+"\n")
    for k,v in out.items():
        print(k,v["interface_path_samples"],v["mesh_hits_within_1mm"],v["groups_at_3mm"][:8])
