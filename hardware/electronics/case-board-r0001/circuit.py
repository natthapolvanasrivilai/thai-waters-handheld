"""Replay the USB circuit on conservative copper lengths extracted from the merged PCB."""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
from build import HERE,A5,parse,items,one

sys.path.insert(0,str(A5))
from verify_power import engine,cases,network,metric

def joined_cases(copper):
    yield from cases(copper)
    # V2 PMIC input and the key's diode share the routed PMIC node. Keep
    # the original worst-drop key model and an energized 3V3 logic fixture.
    from itertools import product
    for cell,cc,(action,contact) in product((3.,4.2),(.61,2.04),(("pressed",10000),("released",1e10))):
        key=f"""Vkeycell vc 0 {cell}
Bkeycell vc aon I=max((v(vc,aon)-.9)/2,0)+min(v(vc,aon),0)/65.625Meg
Bkeyusb pmic aon I=max((v(pmic,aon)-.9)/2,0)+min(v(pmic,aon),0)/65.625Meg
Rkeyleak aon 0 1G
Vlogic logic 0 3.3
Rpull aon key 326.7k
Rcontact key 0 {contact}
Mpkey drive key aon aon KEY_P W=1u L=1u
Roff drive 0 99k
Mnkey keyout drive 0 0 KEY_N W=1u L=1u
.model KEY_P PMOS(level=1 VTO=-1.5 KP=.05)
.model KEY_N NMOS(level=1 VTO=1.5 KP=.05)
Rinternal logic pwron 50k
R38 pwron keyout 510
R37 sensor keyout 1k
R65 logic sensor 100k
"""
        net=network(copper,src=4.75,cc1=cc,drop=True,load="Rload pmic 0 220")+key
        limits=(0,.33) if action=="pressed" else (2.97,3.31)
        yield f"combined_{cell}_{cc}_{action}",net,".tran 1u 25u",[
            metric("pwron","FIND v(pwron) AT=24u","V",*limits),
            metric("host","MAX v(total)","A",0,.100),
        ]

def main(executable):
    board=HERE/"case-board.kicad_pcb"
    root=parse(board)
    nets={}
    for kind in ("segment","via"):
        for element in items(root,kind):
            name=one(element,"net")[1].strip('"')
            entry=nets.setdefault(name,dict(track_mm=0.,vias=0,upper_ohm=0.))
            if kind=="segment":
                a,b=([float(x) for x in one(element,k)[1:]] for k in ("start","end"))
                length=math.dist(a,b)
                width=float(one(element,"width")[1])
                entry["track_mm"]+=length
                # Bound using 25 um copper at 70 C. Sum every branch.
                entry["upper_ohm"]+=length*2.07e-5/(.025*width)
            else:
                entry["vias"]+=1
                entry["upper_ohm"]+=.005
    copper=dict(sha256=engine.digest(board),nets=nets)
    with tempfile.TemporaryDirectory() as tmp:
        dest=Path(tmp)
        shutil.copyfile(board,dest/"usb-input.kicad_pcb")
        (dest/"copper.json").write_text(json.dumps(copper))
        engine.HERE=dest
        engine.cases=joined_cases
        engine.run(executable.resolve())
        for n in ("decks-and-logs.zip","measurements.csv","verification.json"):
            shutil.copyfile(dest/n,HERE/n)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ngspice",type=Path)
    main(parser.parse_args().ngspice)
