"""Render the as-modeled Rev F rigid receiver and two registered planar sections."""
import math,sys
from pathlib import Path
import cadquery as cq
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy,numpy_to_vtk,numpy_to_vtkIdTypeArray
from PIL import Image,ImageDraw,ImageFont,ImageColor
from rod_grip import add_mount,saddle,mount_parts,ROOT

case=add_mount(cq.Shape.importBrep(sys.argv[1]))
grip=saddle()
hardware=mount_parts()
W,H=1640,1060
paper='#F5F4ED';ink='#173B3B';soft='#486265';line='#BECBC5';sage='#8DACA1';green='#24584F';copper='#BB7048';steel='#85959A'
page=Image.new('RGB',(W,H),paper)
draw=ImageDraw.Draw(page)
def font(n,bold=False,mono=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('consola.ttf' if mono else 'segoeuib.ttf' if bold else 'segoeui.ttf'),n)
def label(x,y,s,n=23,b=False,color=ink,anchor='lt',mono=False):
    draw.text((x,y),s,font=font(n,b,mono),fill=color,anchor=anchor)
def rgb(s):return tuple(x/255 for x in ImageColor.getrgb(s))
def render(parts,w,h,look,pos,up,scale):
    ren=vtk.vtkRenderer();ren.SetBackground(*rgb('#DBE5DC'))
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(w,h);win.SetMultiSamples(4);win.AddRenderer(ren)
    for shape,color in parts:
        v,t=shape.tessellate(.04,.12)
        arr=np.asarray([p.toTuple() for p in v]);tri=np.asarray(t,dtype=np.int64)
        points=vtk.vtkPoints();points.SetData(numpy_to_vtk(arr,deep=True))
        cells=vtk.vtkCellArray(); cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,tri.size+1,3,dtype=np.int64),deep=True),numpy_to_vtkIdTypeArray(tri.ravel(),deep=True))
        mesh=vtk.vtkPolyData();mesh.SetPoints(points);mesh.SetPolys(cells)
        normal=vtk.vtkPolyDataNormals();normal.SetInputData(mesh);normal.SetFeatureAngle(52)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normal.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);pr=actor.GetProperty();pr.SetColor(*rgb(color));pr.SetAmbient(.27);pr.SetDiffuse(.8);pr.SetSpecular(.17);pr.SetSpecularPower(24);ren.AddActor(actor)
    ren.AutomaticLightCreationOff()
    for delta,intensity in [((-45,-120,-150),1.05),((100,90,-100),.55),((10,80,80),.26)]:
        l=vtk.vtkLight();l.SetPosition(*[a+b for a,b in zip(look,delta)]);l.SetFocalPoint(*look);l.SetIntensity(intensity);ren.AddLight(l)
    cam=ren.GetActiveCamera();cam.SetFocalPoint(*look);cam.SetPosition(*pos);cam.SetViewUp(*up);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    ren.ResetCameraClippingRange();win.Render()
    f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.ReadFrontBufferOff();f.Update()
    im=Image.fromarray(vtk_to_numpy(f.GetOutput().GetPointData().GetScalars()).reshape(h,w,-1)[::-1].copy()).convert('RGB')
    win.Finalize();return im
def section(box,axis,value,world,parts):
    l,t,r,b=box;w,h=r-l,b-t
    im=Image.new('RGB',(w,h),'#E8EEE7')
    x0,z0,x1,z1=world
    sc=min(w/(x1-x0),h/(z1-z0))
    def pix(x,z):return ((x-(x0+x1)/2)*sc+w/2,((z0+z1)/2-z)*sc+h/2)
    def xy(p):return pix(p.x if axis=='y' else p.y,p.z)
    base=(0,value,0) if axis=='y' else (value,0,0);norm=(0,1,0) if axis=='y' else (1,0,0)
    plane=cq.Face.makePlane(380,380,cq.Vector(*base),cq.Vector(*norm))
    for solid,col in parts:
        for face in solid.intersect(plane).Faces():
            mask=Image.new('L',im.size);pen=ImageDraw.Draw(mask);strokes=[]
            for i,wire in enumerate([face.outerWire(),*face.innerWires()]):
                contour=[xy(p) for p in wire.sample(max(36,math.ceil(wire.Length()/.12)))[0]]
                pen.polygon(contour,fill=0 if i else 255);strokes.append(contour)
            im.paste(col,(0,0,w,h),mask)
            pen=ImageDraw.Draw(im)
            for curve in strokes:pen.line(curve+[curve[0]],fill='#38544E',width=2)
    page.paste(im,(l,t))
    return lambda x,z:(pix(x,z)[0]+l,pix(x,z)[1]+t)
def arrow(a,b,col):
    draw.line((a,b),fill=col,width=3);theta=math.atan2(b[1]-a[1],b[0]-a[0])
    draw.polygon([b]+[(b[0]-12*math.cos(theta+i),b[1]-12*math.sin(theta+i)) for i in (-.42,.42)],fill=col)
label(54,39,'Riffle Pocket',52,True)
label(55,117,'Rigid slide-lock grip',33)
label(1583,49,'REV F  /  INTERFACE INSPECTION',21,False,soft,'rt',True)
draw.line((55,174,1585,174),fill=line,width=2)
label(55,206,'Receiver exposed',28,True);label(855,206,'Grip seated',28,True)
left=render([(case,sage)],735,306,(9,-7,7),(73,-112,-150),(0,1,0),40)
right=render([(case,sage),(grip,green),*[(s,steel if k in ['Receiver nut','Grip lock screw'] else copper) for k,s in hardware.items()]],730,306,(3,-42,1),(70,-119,-191),(0,1,0),70)
page.paste(left,(55,248));page.paste(right,(855,248))
label(55,572,'Rear shoe stands 3.20 mm proud of the case.',22)
label(855,572,'Slide the tongue to the closed stop, then tighten the M3 screw.',21)
draw.line((55,623,1585,623),fill=line,width=2)
label(55,649,'Dovetail section',28,True)
label(789,655,'Y = −10 mm',19,False,soft,'rt',True)
label(855,649,'Fastener and end-stop section',28,True)
label(1584,655,'X = +17 mm',19,False,soft,'rt',True)
parts=[(case,sage),(grip,green)]+[(v,steel if k in ['Receiver nut','Grip lock screw'] else copper) for k,v in hardware.items()]
p=section((55,699,790,903),'y',-10,(-5,-10.7,39,4.3),parts)
q=section((855,699,1585,903),'x',17,(-36,-18,13,7),parts)
# Measurement witness lines are drawn in registered model coordinates.
a,b=p(17-9.90,-3.20),p(17+9.90,-3.20)
for x,y in [a,b]:draw.line((x,y,x,879),fill='#F6EEDF',width=2)
draw.line((a[0],878,b[0],878),fill='#F6EEDF',width=2)
draw.rectangle((int((a[0]+b[0])/2)-81,864,int((a[0]+b[0])/2)+81,892),fill=green)
label((a[0]+b[0])/2,879,'19.80 mm',19,False,'#FFFFFF','mm',True)
ex,ey=q(5,.20);draw.line([(ex,ey),(ex+42,ey+28),(ex+100,ey+28)],fill=ink,width=2)
label(ex+48,ey+37,'Stop',18,True)
sx,sy=q(-24.5,-15.06);arrow((sx,sy+19),(sx,sy-13),copper)
label(55,925,'Female root 26.20 mm  ·  male head 24.98 mm',21)
label(55,959,'Undercut height 4.00 mm  ·  floor above slot 1.70 mm',20,False,soft)
label(855,925,'35 mm engaged  ·  M3 × 10 screw  ·  2.5 mm hex drive',21)
label(855,959,'Back screw out 5.30 mm, then slide toward the lower edge.',20,False,soft)
draw.line((55,1001,1585,1001),fill=line,width=2)
label(55,1022,'Housing',17,True);draw.rectangle((132,1023,153,1038),fill=sage)
label(175,1022,'Grip',17,True);draw.rectangle((225,1023,246,1038),fill=green)
label(273,1022,'Fasteners',17,True);draw.rectangle((359,1023,380,1038),fill=steel)
label(405,1022,'Keepers',17,True);draw.rectangle((479,1023,500,1038),fill=copper)
label(1585,1022,'Nominal CAD sections  /  physical fit and retention pending',17,False,soft,'rt')
page.save(ROOT/'CAD/grip-interface-inspection.png')
