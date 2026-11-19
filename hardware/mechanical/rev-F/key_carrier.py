"""Generate fabrication layers for the four isolated, hand-soldered power key lands."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parents[2]/"electronics"
pad_centers=[(2.25,2.75),(8.75,2.75),(8.75,7.25),(2.25,7.25)]
def xy(x,y):
    return f"X{round(x*10000):07d}Y{round(y*10000):07d}"
def layer(diameter, commands):
    return ("G04 Thai Waters Rev F power key, millimetres*\n%FSLAX34Y34*%\n%MOMM*%\n"
            f"%ADD10C,{diameter:.3f}*%\n%LPD*%\nG01*\nD10*\n"+
            "\n".join(commands)+"\nM02*\n")
flashes=[xy(x,y)+"D03*" for x,y in pad_centers]
outline=[xy(x,y)+("D02*" if i==0 else "D01*") for i,(x,y) in enumerate([(0,0),(11,0),(11,10),(0,10),(0,0)])]
drills="M48\n;FILE_FORMAT=3:3\nMETRIC\nT01C1.000\n%\nT01\n"+"".join(f"X{x:.3f}Y{y:.3f}\n" for x,y in pad_centers)+"M30\n"
note="""PCB1 / Rev F power key carrier
Finished size 11.00 mm x 10.00 mm. Order 1.00 mm FR-4 with two copper layers.
Gerber outline describes the routed edge on its centerline. Copper pads are 1.95 mm
diameter. Drill coordinates are in millimetres, four 1.00 mm finished plated holes.
All four lands are isolated until the Omron B3F-1002-G is installed. Hand solder.
Orient 6.50 mm hole pitch along the 11 mm board edge. Seat the switch on the front.
Trim all tails and dress the two wires flat on the rear to meet the 0.8 mm
rear envelope. Check switch poles and continuity against the wiring note.
"""
with ZipFile(root/"Rev-F-power-key-carrier-Gerber.zip","w",ZIP_DEFLATED) as z:
    for ext in ("gtl","gbl"):z.writestr("power-key."+ext,layer(1.95,flashes))
    for ext in ("gts","gbs"):z.writestr("power-key."+ext,layer(2.10,flashes))
    z.writestr("power-key.gko",layer(.10,outline))
    z.writestr("power-key-PTH.drl",drills)
    z.writestr("FAB-NOTES.txt",note)
