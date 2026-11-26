"""Draw the actual released housing underside and a registered section through both grooves."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
import numpy as np
import trimesh

from build_housing import CENTERS, HERE, NAME, read


def draw():
    row = read(HERE/"part-orientations.json")[NAME]
    h = trimesh.load_mesh(HERE/row["print_stl"])
    h.apply_transform(np.linalg.inv(row["assembly_to_print"]))
    fig, (left,right) = plt.subplots(1,2,figsize=(12,4.8),gridspec_kw={"width_ratios":[1.12,1]})
    face = h.triangles[h.face_normals[:,2] < -.01]
    z = face[:,:,2].mean(axis=1)
    order = np.argsort(-z)
    colors = np.where(z <= -.15, "#536e68", np.where(z < .82, "#afc3b8", "#d7e2d9"))
    left.add_collection(PolyCollection(face[order,:,:2],facecolors=colors[order],edgecolors="face",linewidth=.08))
    for cx in CENTERS:
        left.add_patch(Rectangle((cx-1.5,-12),3,12,fill=False,edgecolor="#af462b",linewidth=1.3))
    left.plot([9,32],[-6,-6],ls="--",lw=1,color="#7b3428")
    left.set(xlim=(-55,61),ylim=(-36,42),title="Underside · installed XY coordinates",xlabel="X (mm)",ylabel="Y (mm)")
    left.set_aspect("equal")
    left.text(.03,.04,"Outlines show the rails on the inside face.",transform=left.transAxes,size=8,
              bbox=dict(facecolor="white",edgecolor="none",pad=2))
    for p in h.section(plane_origin=(0,-6,0),plane_normal=(0,1,0)).discrete:
        right.fill(p[:,0],p[:,2],facecolor="#afc3b8",edgecolor="#425f56",linewidth=1.1)
    for x in CENTERS:
        right.annotate("groove",xy=(x,4.38),xytext=(x,6.3),ha="center",fontsize=8,
                       arrowprops=dict(arrowstyle="->",lw=.8,color="#824a36"))
    right.axhline(4.6,color="#a74c34",ls="--",lw=.8)
    right.axhline(.8,color="#55716c",ls=":",lw=.8)
    right.text(15.3,4.87,"Z4.60",fontsize=8,ha="right")
    right.text(15.3,1.1,"Z0.80",fontsize=8,ha="right")
    right.set(xlim=(11.3,30.6),ylim=(-3.8,7),xlabel="X (mm)",ylabel="Installed Z (mm)",title="Housing section at Y−6.00")
    right.set_aspect("equal")
    for a in (left,right):
        a.spines[["top","right"]].set_visible(False)
        a.tick_params(labelsize=8)
    fig.suptitle("A3 bearing rails and the existing grip receiver",fontsize=16,fontweight="bold",x=.055,ha="left")
    fig.tight_layout()
    fig.savefig(HERE/"QA/floor-section.png",dpi=160,bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    draw()
