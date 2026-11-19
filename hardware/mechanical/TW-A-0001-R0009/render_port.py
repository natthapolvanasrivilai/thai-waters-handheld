"""Render the as-assembled edge directly from R0009 BReps and reference product CAD."""
import argparse
from pathlib import Path
import cadquery as cq
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
from build import HERE

def mesh(shape):
    pts,tri=shape.tessellate(.025,.075)
    xyz=np.ascontiguousarray([p.toTuple() for p in pts],dtype="float64")
    tri=np.ascontiguousarray(tri,dtype=np.int64)
    vertices=vtk.vtkPoints();vertices.SetData(numpy_to_vtk(xyz,deep=True))
    cells=vtk.vtkCellArray()
    cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(tri)+1,3,dtype="int64"),deep=True),
                  numpy_to_vtkIdTypeArray(tri.ravel(),deep=True))
    poly=vtk.vtkPolyData();poly.SetPoints(vertices);poly.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetFeatureAngle(40);norm.ComputePointNormalsOn()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
    actor=vtk.vtkActor();actor.SetMapper(mapper)
    return actor

def render(reference):
    renderer=vtk.vtkRenderer()
    renderer.SetBackground(.91,.91,.88)
    colors=vtk.vtkNamedColors()
    for n,folder,color,shine in [
        ("housing-battery-bay",HERE/"CAD","#82988e",.13),
        ("bezel",HERE/"CAD","#899a91",.14),
        ("power-cap",HERE/"CAD","#514c43",.14),
        ("usbSurround",HERE/"Installed/diaphragm","#82988e",.10),
        ("usbEscutcheonLip",HERE/"Installed/diaphragm","#292c2a",.09),
        ("status-charge-guide",HERE/"CAD","#9aa699",.55),
        ("status-usb-guide",HERE/"CAD","#a2aab0",.55),
        ("status-power-guide",HERE/"CAD","#b0a5a2",.55),
        ("A1-usb",reference,"#a2a39e",.55),
        ("A1-touch",reference,"#333c39",.7)]:
        actor=mesh(cq.Shape.importBrep(str(folder/(n+".brep"))))
        prop=actor.GetProperty();prop.SetColor(*[int(color[i:i+2],16)/255 for i in (1,3,5)]);prop.SetAmbient(.20);prop.SetDiffuse(.8)
        prop.SetSpecular(shine);prop.SetSpecularPower(38);renderer.AddActor(actor)
    for point,intensity in [((-100,-80,130),1.0),((-90,90,30),.42),((60,-80,80),.45)]:
        light=vtk.vtkLight();light.SetLightTypeToSceneLight();light.SetPosition(*point);light.SetFocalPoint(-46,0,17);light.SetIntensity(intensity);renderer.AddLight(light)
    shade=vtk.vtkRenderStepsPass();ao=vtk.vtkSSAOPass();ao.SetRadius(1.65);ao.SetBias(.045);ao.SetKernelSize(128);ao.BlurOn();ao.SetDelegatePass(shade);renderer.SetPass(ao)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetMultiSamples(0);win.SetSize(1500,930);win.AddRenderer(renderer)
    camera=renderer.GetActiveCamera();camera.SetViewUp(0,0,1);camera.ParallelProjectionOn()
    for fname,pos,focus,scale in [
        ("usb-front",(-140,0,17.8),(-43,0,17.8),12.5),
        ("usb-three-quarter",(-140,-32,40),(-45,0,17.2),13.8)]:
        camera.SetPosition(*pos);camera.SetFocalPoint(*focus);camera.SetParallelScale(scale);renderer.ResetCameraClippingRange();win.Render()
        cap=vtk.vtkWindowToImageFilter();cap.SetInput(win);cap.ReadFrontBufferOff();cap.Update()
        writer=vtk.vtkPNGWriter();writer.SetInputConnection(cap.GetOutputPort());writer.SetFileName(str(HERE/(fname+".png")));writer.Write()
    win.Finalize()

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("reference",type=Path);render(p.parse_args().reference)


