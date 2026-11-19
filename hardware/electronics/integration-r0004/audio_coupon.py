"""Emit the four-wire, two-resistor evaluation coupon. Coordinates in millimetres."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def coord(x,y):
    return f'X{round(x*1e6)}Y{round(y*1e6)}'

def layer(apertures, shapes):
    header=['G04 R0004 BTL pad coupon*','%FSLAX46Y46*%','%MOMM*%','%LPD*%']
    header += [f'%ADD{code}{aperture}*%' for code,aperture in apertures.items()]
    return '\n'.join(header+['G01*']+shapes+['M02*',''])

def pad(code, x,y):
    return ['D%d*'%code,coord(x,y)+'D03*']

def line(code,points):
    return ['D%d*'%code,coord(*points[0])+'D02*']+[coord(*p)+'D01*' for p in points[1:]]

def generate():
    holes=[(x,y) for y in (4,10) for x in (2,18)]
    smd=[(x,y) for y in (4,10) for x in (7.1,12.9)]
    copper=[]
    for x,y in holes:
        copper+=pad(11,x,y)
        nearest=7.1 if x<10 else 12.9
        copper+=line(12,[(x,y),(nearest,y)])
    copper+=sum((pad(10,x,y) for x,y in smd),[])
    hole_pads=sum((pad(11,x,y) for x,y in holes),[])
    mask_pads=hole_pads+sum((pad(10,x,y) for x,y in smd),[])
    pieces={
        'F_Cu.gbr':layer({10:'R,2.4X3.5',11:'C,1.8',12:'C,1.4'},copper),
        'B_Cu.gbr':layer({11:'C,1.8'},hole_pads),
        'F_Mask.gbr':layer({10:'R,2.5X3.6',11:'C,1.9'},mask_pads),
        'B_Mask.gbr':layer({11:'C,1.9'},hole_pads),
        'F_Paste.gbr':layer({10:'R,2.2X3.3'},sum((pad(10,x,y) for x,y in smd),[])),
        'Edge_Cuts.gbr':layer({10:'C,0.05'},line(10,[(0,0),(20,0),(20,14),(0,14),(0,0)])),
        'PTH.drl':'M48\nMETRIC,TZ\nT01C0.800\n%\nT01\n'+''.join(f'X{x:.4f}Y{y:.4f}\n' for x,y in holes)+'M30\n',
    }
    with ZipFile(Path(__file__).with_name('audio-bench-coupon-fab.zip'),'w',ZIP_DEFLATED) as out:
        for name,content in pieces.items():
            out.writestr(name,content.encode('ascii'))

if __name__=='__main__':
    generate()
