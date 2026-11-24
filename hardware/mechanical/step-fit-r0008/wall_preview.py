"""Show the USB well from the actual released print meshes at the same scale."""
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy
from PIL import Image, ImageDraw, ImageFont
from check_faces import HERE, OUT, PREVIOUS, T, load_print

def render(path):
    mesh=load_print(path)
    mesh.apply_transform(np.linalg.inv(T))
    v=mesh.vertices
    # Crop surrounding enclosure walls for this detail view only.
    vis=(v[:,0]<-29)&(abs(v[:,1])<24)&(v[:,2]>5)
    f=np.ascontiguousarray(mesh.faces[vis[mesh.faces].all(axis=1)],dtype=np.int64)
    vertices=vtk.vtkPoints()
    vertices.SetData(numpy_to_vtk(np.ascontiguousarray(v),deep=True))
    cells=vtk.vtkCellArray()
    cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(f)+1,3,dtype=np.int64),deep=True),
                  numpy_to_vtkIdTypeArray(f.ravel(),deep=True))
    data=vtk.vtkPolyData();data.SetPoints(vertices);data.SetPolys(cells)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(data)
    actor=vtk.vtkActor();actor.SetMapper(mapper)
    actor.GetProperty().SetColor(.58,.69,.60);actor.GetProperty().SetInterpolationToFlat()
    renderer=vtk.vtkRenderer();renderer.SetBackground(.92,.94,.92);renderer.AddActor(actor)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(620,350);win.AddRenderer(renderer)
    cam=renderer.GetActiveCamera()
    cam.SetPosition(10,80,60);cam.SetFocalPoint(-42,2,18.5);cam.SetViewUp(0,0,1)
    cam.ParallelProjectionOn();cam.SetParallelScale(9.2);renderer.ResetCameraClippingRange()
    win.Render()
    cap=vtk.vtkWindowToImageFilter();cap.SetInput(win);cap.ReadFrontBufferOff();cap.Update()
    px=vtk_to_numpy(cap.GetOutput().GetPointData().GetScalars()).reshape((350,620,-1))[::-1,:,:3].copy()
    win.Finalize()
    return Image.fromarray(px)

if __name__=='__main__':
    image=Image.new('RGB',(1260,418),'#edf0ec');draw=ImageDraw.Draw(image)
    for i,(model,title) in enumerate([(next(PREVIOUS.glob('*.3mf')),'R0007   ·   Prior print mesh'),(OUT,'R0008   ·   Exported from the editable STEP')]):
        x=6+630*i
        draw.text((x+10,12),title,fill='#244536',font=ImageFont.truetype('arialbd.ttf',24))
        image.paste(render(model),(x,60))
    image.save(HERE/'usb-wall-review.png')
