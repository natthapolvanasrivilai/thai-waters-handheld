"""Render the registered case and removable cover from the assembled bottom edge."""
import argparse
import base64
import json
import re
import zlib

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

from build import BASE, HERE


def mesh(row):
    def unpack(key,dtype):
        return np.frombuffer(zlib.decompress(base64.b64decode(row[key])),dtype=dtype).reshape(-1,3)
    v = unpack("v","<i2").astype("float32") / 100
    t = unpack("t","<u4").astype("int64")
    vertices = vtk.vtkPoints()
    vertices.SetData(numpy_to_vtk(v,deep=True))
    faces = vtk.vtkCellArray()
    faces.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(t)+1,3,dtype="int64"),deep=True),
                  numpy_to_vtkIdTypeArray(t.ravel(),deep=True))
    poly=vtk.vtkPolyData()
    poly.SetPoints(vertices)
    poly.SetPolys(faces)
    normals=vtk.vtkPolyDataNormals()
    normals.SetInputData(poly)
    normals.SetFeatureAngle(35)
    mapper=vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor=vtk.vtkActor()
    actor.SetMapper(mapper)
    color=row["color"].lstrip("#")
    prop=actor.GetProperty()
    prop.SetColor(*[int(color[j:j+2],16)/255 for j in (0,2,4)])
    prop.SetAmbient(.23)
    prop.SetDiffuse(.78)
    prop.SetSpecular(.07 if row["id"]=="serviceCover" else .14)
    prop.SetSpecularPower(27)
    return actor


def render(work):
    template=(HERE.parents[2]/"docs/models"/(BASE.name+"-exploded.html")).read_text(encoding="utf8")
    rows=json.loads(re.search(r'<script type="application/json" id="geometry">(.*?)</script>',template,re.S)[1])
    rows.extend(json.loads((work/"viewer-rows.json").read_text()))
    scene=vtk.vtkRenderer()
    scene.SetBackground(.93,.94,.92)
    scene.SetBackground2(.82,.86,.84)
    scene.GradientBackgroundOn()
    actors={}
    for row in rows:
        if row.get("productEligible"):
            actors[row["id"]]=mesh(row)
            scene.AddActor(actors[row["id"]])
    # This screen texture is the one installed in the registered inspection viewer.
    img=vtk.vtkPNGReader()
    img.SetFileName(str(HERE.parents[1]/"visualization/lcd.png"))
    texture=vtk.vtkTexture()
    texture.SetInputConnection(img.GetOutputPort())
    plane=vtk.vtkPlaneSource()
    plane.SetOrigin(-36.72,-24.48,28.52)
    plane.SetPoint1(36.72,-24.48,28.52)
    plane.SetPoint2(-36.72,24.48,28.52)
    mapper=vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(plane.GetOutputPort())
    lcd=vtk.vtkActor()
    lcd.SetMapper(mapper)
    lcd.SetTexture(texture)
    lcd.GetProperty().LightingOff()
    scene.AddActor(lcd)
    for position,strength in [((-90,-110,145),.85),((85,-60,40),.47),((20,75,110),.30)]:
        light=vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(*position)
        light.SetFocalPoint(-4,-20,18)
        light.SetIntensity(strength)
        scene.AddLight(light)
    shade=vtk.vtkRenderStepsPass()
    ao=vtk.vtkSSAOPass()
    ao.SetRadius(1.9)
    ao.SetBias(.035)
    ao.SetKernelSize(128)
    ao.BlurOn()
    ao.SetDelegatePass(shade)
    scene.SetPass(ao)
    win=vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetMultiSamples(0)
    win.SetSize(1560,920)
    win.AddRenderer(scene)
    cam=scene.GetActiveCamera()
    cam.SetViewUp(0,0,1)
    cam.ParallelProjectionOn()
    for name,visible in [("service-cover-installed",True),("service-cover-removed",False)]:
        actors["serviceCover"].SetVisibility(visible)
        cam.SetPosition(-42,-153,77)
        cam.SetFocalPoint(-3,-29,17.5)
        cam.SetParallelScale(28)
        scene.ResetCameraClippingRange()
        win.Render()
        cap=vtk.vtkWindowToImageFilter()
        cap.SetInput(win)
        cap.ReadFrontBufferOff()
        cap.Update()
        writer=vtk.vtkPNGWriter()
        writer.SetInputConnection(cap.GetOutputPort())
        writer.SetFileName(str(HERE/"QA"/(name+".png")))
        writer.Write()
    win.Finalize()


if __name__=="__main__":
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path,required=True)
    render(parser.parse_args().work)

