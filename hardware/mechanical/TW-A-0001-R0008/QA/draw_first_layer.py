"""Render the first printed layer of six individual Bambu G-code files in plan view."""
import argparse
import json
import math
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np

from audit_prints import HERE

INK = "#134956"
SUPPORT = "#cc5e27"
FIELDS = re.compile(r"(?:^| )([XYIJE])([-.\d]+)")


def first_layer(path):
    layer = 0
    role = ""
    pos = np.array([np.nan,np.nan])
    tracks = {INK:[],SUPPORT:[]}
    for line in path.open(encoding="utf-8",errors="replace"):
        if line.startswith("; CHANGE_LAYER"):
            layer += 1
            if layer>1:
                break
        if line.startswith("; FEATURE: "):
            role=line.strip()[11:]
        code=line.split(";",1)[0].strip()
        if not code.startswith(("G0 ","G1 ","G2 ","G3 ")):
            continue
        d={k:float(v) for k,v in FIELDS.findall(code)}
        target=np.array([d.get("X",pos[0]),d.get("Y",pos[1])])
        draw=(layer==1 and d.get("E",0)>0 and ("X" in d or "Y" in d)
              and np.all(np.isfinite(pos)) and role!="Custom")
        if draw:
            points=np.array([pos,target])
            if code.startswith(("G2 ","G3 ")) and "I" in d and "J" in d:
                centre=pos+[d["I"],d["J"]]
                start=math.atan2(*(pos-centre)[::-1]);end=math.atan2(*(target-centre)[::-1])
                sign=-1 if code.startswith("G2 ") else 1
                angle=sign*((sign*(end-start))%(2*math.pi))
                t=np.linspace(start,start+angle,max(2,math.ceil(abs(angle)*12)))
                points=centre+np.linalg.norm(pos-centre)*np.column_stack((np.cos(t),np.sin(t)))
            tracks[SUPPORT if role.startswith("Support") else INK].append(points)
        pos=target
    return tracks


def main():
    p=argparse.ArgumentParser()
    p.add_argument("work",type=Path)
    args=p.parse_args()
    fig,axes=plt.subplots(2,3,figsize=(11.5,6),layout="constrained")
    parts=[("housing-battery-bay","Housing"),("rod-grip","Rod grip"),("rotor","Reel rotor")]
    for i,(k,label) in enumerate(parts):
        plots=[]
        span=0.
        for version in ("baseline","candidate"):
            tracks=first_layer(args.work/version/k/"plate_1.gcode")
            pts=np.vstack([t for paths in tracks.values() for t in paths])
            lo,hi=pts.min(axis=0),pts.max(axis=0)
            span=max(span,max(hi-lo))
            plots.append((tracks,(lo+hi)/2))
        for j,(tracks,centre) in enumerate(plots):
            ax=axes[j,i];ax.set_aspect("equal");ax.axis("off")
            for color,paths in tracks.items():
                if paths:
                    ax.add_collection(LineCollection(paths,colors=color,linewidths=.55))
            half=span*.56
            ax.set_xlim(centre[0]-half,centre[0]+half)
            ax.set_ylim(centre[1]-half,centre[1]+half)
            left=centre[0]-half*.94;bottom=centre[1]-half*.91
            bar=10 if span>60 else 5
            ax.plot([left,left+bar],[bottom,bottom],color="#333333",lw=2)
            ax.text(left,bottom+half*.035,f"{bar} mm",fontsize=7)
            ax.set_title(f"{label}   ·   R000{7+j}",fontsize=12,loc="left")
    fig.suptitle("First-layer toolpaths at 0.20 mm",fontsize=18)
    fig.legend(handles=[Line2D([],[],color=INK,label="Part extrusion"),
                        Line2D([],[],color=SUPPORT,label="Support extrusion")],
               loc="outside lower center",ncol=2,frameon=False)
    fig.savefig(HERE/"first-layer-toolpaths.png",dpi=170)
    plt.close(fig)


if __name__=="__main__":
    main()
