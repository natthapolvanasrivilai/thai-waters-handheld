"""Show model and support from the exact sliced housing at each critical height."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from scipy import ndimage
from toolpaths import inspect

def figure(work):
    runs={"R0009":{.2:None,31.4:None,31.0:None}, "R0011":{.2:None}}
    for tag,shots in runs.items():
        inspect(work/tag/"plate_1.gcode",shots)
    fig,axes=plt.subplots(1,3,figsize=(12,4.7),layout="constrained")
    def panel(ax,shot,title,caption,highlight=False):
        model,support,origin=shot
        rgb=np.ones((*model.shape,3))
        rgb[support]=[.78,.81,.82]
        rgb[model]=[.07,.35,.38]
        if highlight:
            labels,count=ndimage.label(model,structure=np.ones((3,3)))
            for i,sl in enumerate(ndimage.find_objects(labels),1):
                ys,xs=sl
                if 30<(ys.stop-ys.start)*.1<40 and (xs.stop-xs.start)*.1<1:
                    rgb[labels==i]=[.83,.25,.10]
                    xx=origin[0]+(xs.start+xs.stop)*.05
                    yy=origin[1]+ys.stop*.1
                    ax.annotate("36.8 mm",xy=(xx,yy),xytext=(xx+5,yy+9),fontsize=10,color="#a73413",
                                arrowprops=dict(arrowstyle="->",color="#a73413"))
        ax.imshow(rgb,origin="lower",extent=(origin[0],origin[0]+rgb.shape[1]*.1,origin[1],origin[1]+rgb.shape[0]*.1),
                  interpolation="nearest")
        ax.set_aspect("equal")
        ax.set_title(title,fontsize=12,loc="left")
        ax.set_xlabel(caption,fontsize=10)
        ax.set_xticks([]);ax.set_yticks([])
        for spine in ax.spines.values():spine.set_color("#cbd6d6")
    panel(axes[0],runs["R0009"][.2],"R0009  ·  first layer","West/rear diagonal touches the bed")
    panel(axes[1],runs["R0009"][31.4],"R0009  ·  Z 31.4 mm","West receiver lip begins over support", True)
    panel(axes[2],runs["R0011"][.2],"R0011  ·  first layer","Both receiver lips join at their closed end")
    fig.suptitle("Rod-grip receiver in the housing toolpath",fontsize=19)
    fig.legend(handles=[Patch(color="#125961",label="Model"),Patch(color="#c7cfd1",label="Support on this layer"),
                        Patch(color="#d44019",label="Detached model strip")],loc="outside lower center",ncol=3,frameon=False)
    fig.savefig(Path(__file__).with_name("receiver-toolpaths.png"),dpi=180)
    # Intersect the isolated strand with the last support interface two nominal layers below.
    m,_,_=runs["R0009"][31.4]
    _,support,_=runs["R0009"][31.0]
    labs,_=ndimage.label(m,structure=np.ones((3,3)))
    strip=[i for i,(ys,xs) in enumerate(ndimage.find_objects(labs),1)
          if 30<(ys.stop-ys.start)*.1<40 and (xs.stop-xs.start)*.1<1]
    assert len(strip)==1
    footprint=labs==strip[0]
    print("Strip footprint over support at Z=31.0:",round(100*(support & footprint).sum()/footprint.sum(),1),"%")
    assert (support & footprint).sum() > .20*footprint.sum()

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("work",type=Path)
    figure(p.parse_args().work)
