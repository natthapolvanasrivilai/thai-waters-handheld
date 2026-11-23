"""Render a print-friendly plate 7 identification map from the delivered native 3MF."""
from pathlib import Path
from hashlib import sha256
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb

HERE = Path(__file__).resolve().parent
PROJECT = HERE / "Thai-Waters-R0013-PCB-Fit-X1C.3mf"
INK, MUTED = "#182f35", "#47656b"
GAUGES = {
    "A1 display and controller": ("A1", "Display and controller", "above"),
    "A2 reel sensor": ("A2", "Reel sensor", "above"),
    "A3 haptic board": ("A3", "Haptic board", "above"),
    "A4 integration board": ("A4", "Integration board", "below"),
    "A5 USB power board": ("A5", "USB power board", "below"),
    "Top power switch board": ("KEY", "Power switch", "below"),
    "USB indicator LED board": ("USB-PCB1", "Indicator LED", "below"),
    "USB lamp resistor board": ("USB-PCB2", "Lamp resistor", "below"),
}
SPACERS = {"A3": "floor strips", "A4": "display spacers", "A5": "display spacers"}


def metadata(node,key):
    return node.find(f"metadata[@key='{key}']").get("value")


def read_plate():
    with ZipFile(PROJECT) as pack:
        graph=ET.fromstring(pack.read("3D/3dmodel.model"))
        cfg=ET.fromstring(pack.read("Metadata/model_settings.config"))
        plate=next(p for p in cfg.findall("plate") if metadata(p,"plater_id")=="7")
        meshes={}
        shifts=[]
        for item in plate.findall("model_instance"):
            oid=metadata(item,"object_id")
            obj=cfg.find(f"object[@id='{oid}']")
            name=metadata(obj,"name")
            comp=graph.find(f".//{{*}}object[@id='{oid}']/{{*}}components/{{*}}component")
            path=next(v for k,v in comp.attrib.items() if k.endswith("}path")).lstrip("/")
            payload=ET.fromstring(pack.read(path))
            mesh=payload.find(f".//{{*}}object[@id='{comp.get('objectid')}']/{{*}}mesh")
            xyz=np.array([[float(v.get(k)) for k in "xyz"] for v in mesh.find("{*}vertices")])
            triangles=[[int(t.get(k)) for k in ("v1","v2","v3")] for t in mesh.find("{*}triangles")]
            world=np.array([float(s) for s in
                       graph.find(f".//{{*}}build/{{*}}item[@objectid='{oid}']").get("transform").split()]).reshape(4,3)
            plate_pose=np.fromstring(metadata(obj.find("part"),"matrix"),sep=" ").reshape(4,4)
            assert np.allclose(world[:3].T,plate_pose[:3,:3])
            shifts.append(plate_pose[:3,3]-world[3])
            shape=trimesh.Trimesh(xyz,triangles,process=False)
            shape.apply_transform(plate_pose)
            meshes[name]=shape
        assert len(meshes)==16 and np.max(np.ptp(shifts,axis=0))<.0001
        return meshes


def draw_mesh(ax,mesh,base):
    # Painter's order for top-facing triangles, so the PCB land is drawn before
    # the component roofs. Height changes remain visible on a monochrome print.
    faces=mesh.triangles
    mask=mesh.face_normals[:,2]>.004
    faces=faces[mask]
    normals=mesh.face_normals[mask]
    z=faces.mean(axis=1)[:,2]
    order=np.argsort(z,kind="stable")
    h=np.clip((z-mesh.bounds[0,2])/mesh.extents[2],0,1)
    base=np.array(to_rgb(base))
    strength=.36+.62*h+np.minimum(.08,.08*(1-normals[:,2]))
    colors=1-(1-base[None,:])*strength[:,None]
    ax.add_collection(PolyCollection(faces[order,:,:2],facecolors=colors[order],edgecolors="none",
                                     antialiased=False,zorder=3))
    trace=mesh.section(plane_origin=[0,0,.015],plane_normal=[0,0,1])
    def projected_area(loop):
        x,y=loop[:,0],loop[:,1]
        return abs(np.sum(x*np.roll(y,-1)-y*np.roll(x,-1)))
    # Outline only the substrate perimeter. Its hidden holes may have a solid
    # component above, so leave the interior to the top-face rendering.
    outline=max(trace.discrete,key=projected_area)
    ax.plot(outline[:,0],outline[:,1],lw=.57,color=INK,zorder=4)


def render():
    meshes=read_plate()
    fig=plt.figure(figsize=(11.69,8.27),facecolor="white")
    fig.text(.066,.942,"Plate 7   PCB fit gauges",fontsize=25,fontweight="bold",color=INK)
    fig.text(.067,.903,"Top view of the saved X1 Carbon plate. The rear edge is toward the top.",
             fontsize=11,color=MUTED)
    fig.text(.934,.946,"THAI WATERS",ha="right",weight="bold",fontsize=10,color=INK)
    fig.text(.934,.918,"TW-A-0001-R0013",ha="right",fontsize=9,color=MUTED)
    ax=fig.add_axes([.075,.136,.865,.730])
    ax.set_xlim(26,229)
    ax.set_ylim(43,192)
    ax.set_aspect("equal",adjustable="box")
    ax.set_facecolor("#f8faf9")
    ax.set_xticks(np.arange(50,226,25))
    ax.set_yticks(np.arange(50,176,25))
    ax.set_axisbelow(True)
    ax.grid(color="#dce5e2",lw=.6)
    ax.tick_params(colors=MUTED,labelsize=8,length=3,pad=5)
    for spine in ax.spines.values():
        spine.set_color("#a4b8b3")
        spine.set_linewidth(.8)
    ax.set_xlabel("Plate X  (mm)",fontsize=9,color=MUTED,labelpad=6)
    ax.set_ylabel("Plate Y  (mm)",fontsize=9,color=MUTED,labelpad=6)
    for name,mesh in meshes.items():
        is_shim=name not in GAUGES
        color="#597ba1" if is_shim else "#16736f"
        if name=="A2 reel sensor":
            color="#865108"
        draw_mesh(ax,mesh,color)
        if is_shim:
            continue
        short,long,side=GAUGES[name]
        lo,hi=mesh.bounds
        x=(lo[0]+hi[0])/2
        if side=="above":
            y=hi[1]+3.1
            ax.text(x,y+4.0,short,ha="center",weight="bold",color=INK,fontsize=10,zorder=6)
            ax.text(x,y,long,ha="center",color=MUTED,fontsize=8.2,zorder=6)
        else:
            y=lo[1]-4.1
            ax.text(x,y,short,ha="center",weight="bold",color=INK,fontsize=10,zorder=6)
            ax.text(x,y-4.4,long,ha="center",color=MUTED,fontsize=8.2,zorder=6)
    for prefix,label in SPACERS.items():
        group=[m for name,m in meshes.items() if name.startswith(prefix+" ") and "spacer " in name]
        xmin=min(m.bounds[0,0] for m in group)
        xmax=max(m.bounds[1,0] for m in group)
        x=(xmin+xmax)/2
        y=59
        ax.plot([xmin,xmin,xmax,xmax],[y+1.6,y,y,y+1.6],lw=.85,color="#597ba1",zorder=5)
        ax.text(x,y-4.0,f"{prefix}   {len(group)} {label}",ha="center",weight="bold",color=INK,fontsize=9)
        height=group[0].extents[2]
        htext=f"{height:.3f}".rstrip("0").rstrip(".")
        ax.text(x,y-8.0,f"{htext} mm high",ha="center",color=MUTED,fontsize=8)
    fig.text(.075,.035,"Keep the A4 and A5 spacer sets separate when you lift them from the plate.",
             fontsize=10,color=INK)
    fig.text(.94,.035,"Cropped plate view  ·  Scale shown by axes",ha="right",fontsize=8,color=MUTED)
    fig.savefig(HERE/"plate-7.png",dpi=230,metadata={"Source3MF":sha256(PROJECT.read_bytes()).hexdigest()})
    plt.close(fig)


if __name__=="__main__":
    render()
