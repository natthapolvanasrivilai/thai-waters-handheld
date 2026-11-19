"""Generate two 0.6 mm, two-layer component carriers. Distances are mm."""
from pathlib import Path
import zipfile, json
import cadquery as cq

OUT = Path(__file__).resolve().parent
def xy(p):
    return "X%dY%d" % tuple(round(v*1e6) for v in p)
def gerber(name, apertures, objects):
    return "\n".join(["G04 "+name+" (mm)*","%FSLAX46Y46*%","%MOMM*%","%LPD*%"] +
                     ["%%ADD%d%s*%%" % (10+i,a) for i,a in enumerate(apertures)] +
                     ["G01*"]+objects+["M02*",""])
def flash(p):
    return xy(p)+"D03*"
def trace(a,b):
    return [xy(a)+"D02*",xy(b)+"D01*"]
def build(name,w,h,pad_spacing,padsize,terminal_x,terminal_y):
    c=(w/2,h/2)
    smd=[(c[0]-pad_spacing/2,c[1]),(c[0]+pad_spacing/2,c[1])]
    wire=[(c[0]-terminal_x,c[1]+terminal_y),(c[0]+terminal_x,c[1]+terminal_y)]
    corner=[(0,0),(w,0),(w,h),(0,h),(0,0)]
    layers={}
    for mask,ext in ((False,'Cu'),(True,'Mask')):
        grow=.1 if mask else 0
        apos=['R,%.3fX%.3f' % (padsize[0]+grow,padsize[1]+grow),'C,%.3f' % (.84+grow),'C,0.240']
        front=['D10*']+[flash(q) for q in smd]+['D11*']+[flash(q) for q in wire]
        if not mask:
            front+=['D12*']
            for a,b in zip(smd,wire):front+=trace(a,b)
        layers['F_'+ext+'.gbr']=gerber(name,apos,front)
        layers['B_'+ext+'.gbr']=gerber(name,apos,['D11*']+[flash(q) for q in wire])
    layers['F_Paste.gbr']=gerber(name,['R,%.3fX%.3f' % padsize],['D10*']+[flash(q) for q in smd])
    layers['Edge_Cuts.gbr']=gerber(name,['C,0.050'],['D10*',xy(corner[0])+'D02*']+[xy(p)+'D01*' for p in corner[1:]])
    layers['PTH.drl']='M48\nMETRIC,TZ\nT01C0.400\n%\nT01\n'+''.join('X%.4fY%.4f\n'%p for p in wire)+'M30\n'
    with zipfile.ZipFile(OUT/(name+'-fab.zip'),'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in layers.items():z.writestr(n,data)
    block=cq.Solid.makeBox(w,h,.6,cq.Vector(-w/2,-h/2,0))
    for x,y in wire:
        bore=cq.Solid.makeCylinder(.2,.8,cq.Vector(x-w/2,y-h/2,-.1))
        block=block.cut(bore)
    cq.exporters.export(block,str(OUT/(name+'-substrate.step')))
    return dict(width_mm=w,height_mm=h,thickness_mm=.6,pth_finished_mm=.4,front_pad_centers_mm=smd,pth_centers_mm=wire,
                coordinate_frame="Front view of emitter/component; origin lower left. Left LED pad K1/black, right A2/current-limited VBUS.")
if __name__=='__main__':
    boards={'USB-blue':build('USB-blue',4.8,3.2,1.65,(.8,.8),1.7,.0),
            'USB-limit':build('USB-limit',3.2,2,1.5,(.75,.75),1.02,.47)}
    (OUT/'carrier-layout.json').write_text(json.dumps(boards,indent=2)+'\n')

