"""Sample opposed surfaces of each positive solid in the saved print orientation."""
from pathlib import Path
from zipfile import ZipFile
import json
import sys
from lxml import etree as ET
import numpy as np
import trimesh
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

HERE = Path(__file__).resolve().parent
PROJECT = HERE / "Thai-Waters-DFM-R0001-X1C.3mf"

def affine(text):
    if text is None:
        return np.eye(4)
    out = np.eye(4)
    out[:3] = np.array(text.split(), dtype=float).reshape(4, 3).T
    return out

def samples(mesh):
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(mesh.vertices.copy(), deep=True))
    ids = np.c_[np.full(len(mesh.faces), 3), mesh.faces].ravel().astype(np.int64)
    cells = vtk.vtkCellArray()
    cells.SetCells(len(mesh.faces), numpy_to_vtkIdTypeArray(ids, deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(cells)
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(poly)
    locator.BuildLocator()
    orig, idx = trimesh.sample.sample_surface(mesh, 18000, seed=1203)
    result = {"upright": [], "inclined_or_flat": []}
    normals = mesh.face_normals
    end = [0., 0., 0.]
    uv = [0., 0., 0.]
    t, sub, cell = vtk.reference(0.), vtk.reference(0), vtk.reference(0)
    for point, face in zip(orig, idx):
        n = normals[face]
        if locator.IntersectWithLine(point - .004*n, point - 160*n, 1e-8, t, end, uv, sub, cell):
            if np.dot(n, normals[int(cell)]) < -.65:
                dist = float(np.linalg.norm(point - end))
                result["upright" if abs(n[2]) < .65 else "inclined_or_flat"].append(dist)
    stats = {}
    for key, values in result.items():
        if values:
            a = np.array(values)
            stats[key] = {"count": len(a), "p05_mm": round(float(np.percentile(a, 5)), 3),
                          "min_sample_mm": round(float(a.min()), 3),
                          "fraction_under_0_84": round(float((a < .84).mean()), 4)}
    return stats

def run():
    report = []
    with ZipFile(PROJECT) as archive:
        root = ET.fromstring(archive.read("3D/3dmodel.model"))
        cfg = ET.fromstring(archive.read("Metadata/model_settings.config"))
        for item in root.findall(".//{*}build/{*}item"):
            oid = item.get("objectid")
            wrapper = root.find(f".//{{*}}resources/{{*}}object[@id='{oid}']")
            props = cfg.find(f"object[@id='{oid}']")
            name = props.find("metadata[@key='name']").get("value")
            solids = []
            for child in wrapper.findall(".//{*}component"):
                cid = child.get("objectid")
                part = props.find(f"part[@id='{cid}']")
                if part.get("subtype") != "normal_part":
                    continue
                path = next(v.lstrip("/") for k,v in child.attrib.items() if k.endswith("}path"))
                xml = ET.fromstring(archive.read(path)).find(f".//{{*}}object[@id='{cid}']/{{*}}mesh")
                vertices = [[float(p.get(k)) for k in ("x","y","z")] for p in xml.find("{*}vertices")]
                faces = [[int(p.get(k)) for k in ("v1","v2","v3")] for p in xml.find("{*}triangles")]
                mesh = trimesh.Trimesh(vertices, faces, process=True)
                mesh.apply_transform(affine(item.get("transform")) @ affine(child.get("transform")))
                solids.append(mesh)
            mesh = trimesh.util.concatenate(solids)
            dims = mesh.extents.round(3).tolist()
            # Triangle-area screen in build coordinates. Faces touching the bed are excluded.
            elevated = mesh.triangles[:,:,2].min(axis=1) > mesh.bounds[0,2]+.025
            shallow = mesh.face_normals[:,2] < -np.cos(np.radians(30))
            shallow_area = round(float(mesh.area_faces[elevated & shallow].sum()),3)
            report.append(dict(name=name, elevated_underside_under_30deg_mm2=shallow_area, volume_mesh=bool(mesh.is_volume), size_mm=dims,
                               connected_shells=len(mesh.split(only_watertight=False)), **samples(mesh)))
    (HERE/"thickness.json").write_text(json.dumps(report,indent=2)+"\n")

if __name__ == "__main__":
    run()
