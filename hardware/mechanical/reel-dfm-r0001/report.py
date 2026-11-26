"""Build the inspection table and a portable viewer of true mesh sections."""
import csv
import json
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent

def read(name):
    return json.loads((HERE/name).read_bytes())

def sections():
    mat=np.array(read("rotor-geometry.json")["installed_to_print"])
    data={}
    for title,filename in [("Previous",HERE.parent/"TW-A-0001-R0009/Print/rotor.stl"),("Reinforced",HERE/"rotor.stl")]:
        mesh=trimesh.load_mesh(filename)
        mesh.apply_transform(np.linalg.inv(mat))
        cuts=[]
        for x in XS:
            slice_=mesh.section([1,0,0],[x,0,14.8])
            assert slice_ is not None
            cuts.append([np.round(np.c_[p[:,1],14.8-p[:,2]],3).tolist() for p in slice_.discrete])
        data[title]=cuts
    return data

def diagram(data):
    canvas=Image.new("RGB",(1000,460),"#f8f6ef")
    d=ImageDraw.Draw(canvas)
    def font(size):
        for f in ["DejaVuSans.ttf","arial.ttf"]:
            try:return ImageFont.truetype(f,size)
            except OSError:pass
        return ImageFont.load_default()
    d.text((30,20),"Reel pocket at its front edge",font=font(31),fill="#15382e")
    d.text((32,68),"Same axial section through each rotor, X = 57.25 mm",font=font(18),fill="#41554c")
    for i,(title,cuts) in enumerate(data.items()):
        ox=256+i*490
        mask=Image.new("1",canvas.size)
        from PIL import ImageChops
        for p in cuts[XS.index(57.25)]:
            m=Image.new("1",canvas.size)
            ImageDraw.Draw(m).polygon([(ox+10.3*x,262+10.3*y) for x,y in p],fill=1)
            mask=ImageChops.logical_xor(mask,m)
        canvas.paste("#3c6258",mask=mask)
        d.ellipse((ox-150,229,ox-88,295),outline="#c36928",width=4)
        d.text((ox-145,407),title+" rotor",font=font(21),fill="#15382e")
    canvas.save(HERE/"rim-section.png")

def main():
    data=sections()
    diagram(data)
    checks={r["name"]:r["Hand check after cooling"] for r in csv.DictReader((HERE/"checks.csv").open(encoding="utf8"))}
    dep={r["name"]:r for r in read("deposition.json")["objects"]}
    walls={r["name"]:r for r in read("thickness.json")}
    rows=[]
    for p in read("part-paths.json"):
        name=p["name"]
        w=walls[name]
        rows.append({"plate":p["plate"],"part":name,"layers":dep[name]["model_layers"],
                     "bed_mm2":p["first_model_contact_mm2"],"brim_mm3":p["brim_mm3"],"support_mm3":p["support_mm3"],
                     "island_starts":len(p["model_component_backing"]["fully_unbacked_components"]),
                     "side_p05_mm":w["upright"]["p05_mm"],"underside_below_30deg_mm2":w["elevated_underside_under_30deg_mm2"],
                     "check":checks[name]})
    assert len(rows)==len(checks)==len(walls)==len(dep)==26
    with (HERE/"inspection.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    html=(HERE/"inspector-template.html").read_text(encoding="utf8")
    for k,v in [("CUTS",data),("AXIAL",XS),("PARTS",rows)]:
        html=html.replace("@@"+k+"@@",json.dumps(v,separators=(",",":")))
    (HERE/"Print-inspection.html").write_text(html,encoding="utf8")

XS=[49.4,50.3,51.2,52.1,53,53.6,54.5,55.4,56.3,56.9,57.25,57.45]
if __name__=="__main__":
    main()
