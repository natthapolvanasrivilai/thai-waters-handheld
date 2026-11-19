"""Place the supplier speaker, its acoustic seal and two formed J9 leads."""
from pathlib import Path
import json
import math
import sys
import cadquery as cq
from build import HERE, SPEAKER_X, SPEAKER_Z, speaker_gasket

sys.path.insert(0,str(HERE.parent/"rev-G"))
from geometry import rounded,sweep

SOURCE=HERE.parents[1]/"components/adafruit-3923/adafruit-3923.step"
OUT=HERE/"Installed"/"speaker"
LABELS=[
 ("speakerRim","Nickel speaker rim","#b4b6af"),
 ("Speaker","SP1 molded frame","#252826"),
 ("speakerPoleRing","Magnet surround","#979994"),
 ("speakerMagnet","Rear magnet","#797c76"),
 ("speakerDiaphragm","Speaker diaphragm","#383b38"),
 ("speakerCloth","Acoustic front cloth","#272c29"),
 ("speakerTerminal0","SP1 factory terminal lead A","#a09d93"),
 ("speakerTerminal1","SP1 factory terminal lead B","#948d82"),
]

def speaker_parts():
    ss=cq.importers.importStep(str(SOURCE)).val().Solids()
    return {key:s.rotate((0,0,0),(0,0,1),180).translate((SPEAKER_X,0,SPEAKER_Z)) for (key,_,_),s in zip(LABELS,ss)}

def route(i):
    # Stubs terminate at Y=-17.70. Start on their end faces, tangent to the
    # exiting conductor. Use continuous insulated replacement leads to J9.
    x=SPEAKER_X+(-2.2 if i==0 else 2.2)
    z=SPEAKER_Z+5.80
    if i==0:
        pts=[(x,-17.70,z),(x,-20.8,z),(-35.4,-20.0,9.15),(-24.6,-21.1,13.25),
             (-10.,-19.75,15.1),(-6.6,-16.2,17.25),(-4.6,-14.85,18.95),
             (-1.315,-15.4,19.05),(-1.315,-18.25,19.05)]
    else:
        pts=[(x,-17.70,z),(x,-19.95,z),(-34.4,-19.65,13.15),(-24.,-17.68,14.0),
             (-17.,-17.7,16.7),(-10.,-14.2,17.6),(-6.,-13.3,18.2),(-3.,-12.4,19.05),
             (-.065,-14.8,19.05),(-.065,-18.25,19.05)]
    edges=rounded(pts,.95)
    shape,length=sweep(edges,.45)
    return shape,{"centerline_waypoints_mm":pts,"centerline_length_mm":round(length,3),
                  "diameter_mm":.90,"minimum_centerline_radius_mm":.95,"end":"J9 BTL position "+str(i+1)}

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    source="hardware/components/adafruit-3923/adafruit-3923.step"
    parts=speaker_parts();rows=[]
    for key,label,color in LABELS:
        rows.append(dict(id=key,name=label,ref="SP1",group="Audio",kind="Supplier STEP",color=color,source=source,
                         delta=[0,-15,-17],stage=3,note="Adafruit 3923 supplier CAD. Installed front cloth faces the grille."))
    parts["speakerGasket"]=speaker_gasket()
    rows.append(dict(id="speakerGasket",name="Speaker perimeter seal",ref="SP1-G",group="Audio",kind="Custom die-cut foam",color="#363733",
                     source="speaker.py",delta=[0,-12,-11],stage=3,note="0.50 mm compressed design stack, continuous ring. Confirm foam compliance and PSA compatibility."))
    wires={}
    for i in range(2):
        k="spk"+str(i);parts[k],wires[k]=route(i)
        rows.append(dict(id=k,name="J9 speaker lead "+str(i+1),ref="W5",group="Wiring",kind="Routed conductor solid",color=["#bb5950","#555958"][i],
                  source="speaker.py",delta=[0,-13,-10],stage=3,note="Custom direct J9 harness; preserve terminal interface and confirm first-article solderability."))
    for row in rows:
        k=row["id"];parts[k].exportBrep(str(OUT/(k+".brep")));row["brep"]=k+".brep"
    (OUT/"parts.json").write_text(json.dumps(rows,indent=2)+"\n",encoding="utf8")
    (OUT/"wire-routes.json").write_text(json.dumps(wires,indent=2)+"\n",encoding="utf8")

if __name__=="__main__":main()



