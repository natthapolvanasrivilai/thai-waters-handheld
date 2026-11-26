"""Compare fixed A5 leads to the assembly and the 8.25 mm W4 service sweep."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile
import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
E = HERE.parents[1]
sys.path.insert(0, str(E/"harness-r0006"))
import check as h6
sc = h6.sc


def lamp_mesh(name):
    from form import OLD, OPEN, JACKET, COPPER
    config=json.loads((OLD/"placement.json").read_bytes())
    source=name.split("-Cu")[0]
    e=cq.Edge.makeSpline([cq.Vector(*p) for p in config["wire_control_points"][source]])
    length=e.Length()
    radius=COPPER if name.endswith("-Cu") else JACKET
    intervals=((0,OPEN[0]),(OPEN[1],length)) if name=="USB-W4C" else ((0,length),)
    pieces=[]
    for a,b in intervals:
        u=np.linspace(a/length,b/length,max(3,round((b-a)/.10)+1))
        pieces.append([e.positionAt(float(t)).toTuple() for t in u])
    meshes=[sc.tube(p,radius) for p in pieces]
    if name=="USB-W4C-Cu":
        tails=cq.Shape.importBrep(str(OLD/"USB-W4C-Cu.brep"))
        meshes.extend(sc.model(*sc.tri(s)) for s in tails.Solids())
    return meshes


def gap(a,b):
    lo,hi = sc.BOXES[id(a)] + a.getTranslation()
    l,h = sc.BOXES[id(b)] + b.getTranslation()
    return float(np.linalg.norm(np.maximum(0, np.maximum(lo-h,l-hi))))


def metal_contacts(board, header, parts):
    def planar(shape,z):
        return next(f for f in shape.Faces() if f.BoundingBox().zlen<1e-6 and abs(f.Center().z-z)<1e-5)
    data={}
    for ref,x,y,z in (("W2",34.45,12,17.84),("W3",34.45,5,17.84),("W7",30.65,17.3,17.05)):
        cu=parts["A5-"+ref+"-Cu"]
        a5,far=sorted(parts["A5-"+ref+"-solder"].Solids(),key=lambda s:-s.Center().x)
        pads=[s for s in board.Solids() if abs(s.Center().x-x)<.01 and abs(s.Center().y-y)<.01
              and abs(s.BoundingBox().xlen-1.70)<1e-4 and s.BoundingBox().zmin-1e-6<=z<=s.BoundingBox().zmax+1e-6]
        assert len(pads)==1
        area=planar(a5,z).intersect(planar(pads[0],z)).Area()
        row=dict(a5_solder_to_copper_gap_mm=round(a5.distance(cu),7),
                 a5_solder_on_assigned_native_pad_mm2=round(area,6),far_solder_to_copper_gap_mm=round(far.distance(cu),7))
        assert area>.1 and row["a5_solder_to_copper_gap_mm"]==0 and row["far_solder_to_copper_gap_mm"]==0
        if ref=="W2":
            row["far_wetting_to_J8_1_gap_mm"]=round(far.distance(header),7)
            assert row["far_wetting_to_J8_1_gap_mm"]==0
        elif ref=="W3":
            ground=parts["USB-W4C-Cu"]
            tail=min(ground.Solids(),key=lambda s:(s.Center()-cq.Vector(-16.52,19.82,20.625)).Length)
            row["far_solder_to_shared_copper_gap_mm"]=round(far.distance(ground),7)
            row["single_tail_to_J8_3_gap_mm"]=round(tail.distance(header),7)
            assert row["far_solder_to_shared_copper_gap_mm"]==0 and row["single_tail_to_J8_3_gap_mm"]==0
        else:
            # The USB resistor-carrier STEP contains only FR4. Recover the
            # flashed bottom copper and finished hole from its controlled plot.
            archive=E/"usb-status-r0003/USB-limit-fab.zip"
            with ZipFile(archive) as fab:
                back=next(fab.read(k) for k in fab.namelist() if k.endswith("B_Cu.gbr"))
                drill=next(fab.read(k) for k in fab.namelist() if k.endswith(".drl"))
            assert b"%ADD11C,0.840*%" in back and b"X2620000Y1470000D03*" in back
            assert b"C0.400" in drill or b"C0.4" in drill
            origin=cq.Vector(-19.98,18.47,17.60)
            ring=cq.Face.makeFromWires(cq.Wire.makeCircle(.42,origin,cq.Vector(0,0,1)),
                                       [cq.Wire.makeCircle(.20,origin,cq.Vector(0,0,1))])
            row["far_solder_on_lamp_gerber_annulus_mm2"]=round(planar(far,17.60).intersect(ring).Area(),6)
            row["lamp_fab_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
            assert row["far_solder_on_lamp_gerber_annulus_mm2"]>.1
        data[ref]=row
    return data


def run(cache):
    manifest = json.loads((HERE/"installed.json").read_bytes())
    s = sc.read_shapes(cache)
    previous = E/"harness-r0005"
    sources = {k:cache/(k+".brep") for k in s}
    sources.update({row["name"]:previous/row["brep"] for row in json.loads((previous/"installed.json").read_bytes())["add"]})
    overrides = {key:E/"pcb-haptic-cie-r0002/placed"/(key+".brep") for key in ("drvParts","drvBoard")}
    overrides.update({"A5-power": HERE.parent/"A5-power.brep",
                      "A5-bond": E.parent/"mechanical/TW-A-0001-R0013/A5-bond.brep"})
    support=json.loads((overrides["A5-bond"].parent/"QA/A5-bond.json").read_bytes())
    board_sha=hashlib.sha256(overrides["A5-power"].read_bytes()).hexdigest()
    bond_sha=hashlib.sha256(overrides["A5-bond"].read_bytes()).hexdigest()
    assert support["A5_sha256"]==board_sha and support["fitted_bond_sha256"]==bond_sha
    for r in manifest["add"]:
        assert hashlib.sha256((HERE/r["brep"]).read_bytes()).hexdigest()==r["sha256"]
    routing=json.loads((HERE/"routes.json").read_bytes())
    design=json.loads((HERE.parent/"design.json").read_bytes())
    net={"W2":"PMIC","W3":"GND","W7":"CTRL"}
    for ref,wire_net in net.items():
        row=next(r for r in design["parts"] if r[0]==ref)
        assert row[-1]==[wire_net]
        assert np.allclose(routing[ref]["dressing_points_mm"][0], [13+row[3],3+row[4],18.30],rtol=0,atol=1e-8)
    sources.update(overrides)
    s.update({k:cq.Shape.importBrep(str(p)) for k,p in overrides.items()})
    for name in manifest["remove"]:
        del s[name]
    for n in h6.NET_PIN:
        sources["wh"+n]=E/"harness-r0006/placed"/("wh"+n+".brep")
        s["wh"+n] = cq.Shape.importBrep(str(sources["wh"+n]))
    new = {r["name"]:cq.Shape.importBrep(str(HERE/r["brep"])) for r in manifest["add"]}
    s["USB-BOND"]=new.pop("USB-BOND")
    original_bond=cq.Shape.importBrep(str(cache/"USB-BOND.brep"))
    bond=s["USB-BOND"]
    projection={"volume_removed_mm3":round(original_bond.Volume()-bond.Volume(),6),
                "new_volume_outside_original_mm3":round(bond.cut(original_bond).Volume(),6),
                "contact_mm":{k:round(bond.distance(s[k]),6) for k in ("A1-J8","USB-PCB2")}}
    assert bond.isValid() and len(bond.Solids())==1 and min(projection["contact_mm"].values())>=0
    assert max(projection["contact_mm"].values())<1e-5 and projection["new_volume_outside_original_mm3"]<1e-6
    native = dict(s, **new)
    sources.update({r["name"]:HERE/r["brep"] for r in manifest["add"]})
    tess = cache.parent/"r0013-mesh-025-010"
    tess.mkdir(exist_ok=True)
    mesh = {}
    # Limit each static tessellation to triangles near the changed harness.
    # Keep the complete new leads and swept candidates for the motion screen.
    def bounds(v):
        b=v.BoundingBox()
        return np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])
    newboxes=[bounds(v) for v in new.values()]
    for k,v in native.items():
        if k in new and not v.isValid(): raise ValueError(k)
        lo,hi=bounds(v)
        if not any(np.all(hi>=nlo-2) and np.all(lo<=nhi+2) for nlo,nhi in newboxes):continue
        # These uninterrupted swept splines have a known circular section.
        # Use arc-length centerlines for screening, and native CAD for near pairs.
        if k in ("USB-W4B","USB-W4C","USB-W4C-Cu"):
            for i,obj in enumerate(lamp_mesh(k)):
                mesh[k if i==0 else k+"#"+str(i)]=obj
            continue
        path=tess/(hashlib.sha256(sources[k].read_bytes()).hexdigest()+".npz")
        if path.exists():
            with np.load(path) as saved:
                vertices,faces=saved["vertices"],saved["faces"]
        else:
            print("Tessellate",k,flush=True)
            vertices,faces=sc.tri(v)
            np.savez_compressed(path,vertices=vertices,faces=faces)
        if k not in new:
            vlo=vertices[faces].min(axis=1)
            vhi=vertices[faces].max(axis=1)
            keep=np.zeros(len(faces),dtype=bool)
            for nlo,nhi in newboxes:
                keep |= np.all(vhi>=nlo-2,axis=1)&np.all(vlo<=nhi+2,axis=1)
            if not keep.any():continue
            ix,inv=np.unique(faces[keep],return_inverse=True)
            vertices=vertices[ix];faces=inv.reshape(-1,3)
        mesh[k]=sc.model(vertices,faces)
    print("Loaded seated meshes",len(mesh),flush=True)
    intentional = []
    unexpected = []
    nearest = {}
    # Interface labels apply only to the nominated end. Check unwanted distant
    # overlap by clipping the intersection against a short, registered joint window.
    def classify(a,b):
        if (a.startswith('A5-W') and b.startswith('A5-W') and a[:5]==b[:5]) or (
            a in ('USB-W4C','USB-W4C-Cu') and b in ('USB-W4C','USB-W4C-Cu')):
            return "formed lead materials",None
        if {a,b} == {'USB-W4C-Cu','A1-J8'}:
            return "retained common J8-3 solder tail",(-16.52,19.82,20.75,.52)
        if {a,b} == {'USB-W4C-Cu','USB-PCB1'}:
            return "retained lamp cathode solder tail",(-41.6,-1.7,13.1,.9)
        if a.startswith('A5-W3') and b.startswith('USB-W4C') or b.startswith('A5-W3') and a.startswith('USB-W4C'):
            return "single J8-3 pigtail splice",(-17.56,17.74,16.36,2.0)
        for wire, xy in (("W2",(34.45,12)),("W3",(34.45,5)),("W7",(30.65,17.3))):
            if 'A5-power' in (a,b) and ({a,b} & {'A5-'+wire+'-Cu','A5-'+wire+'-solder'}):
                return "assigned A5 plated landing",(*xy,17.45,.94)
        if "A1-J8" in (a,b) and ({a,b} & {"A5-W2-Cu","A5-W2-solder"}):
            return "fixed J8-1 solder tail",(-19.06,19.82,20.75,.39)
        if "USB-PCB2" in (a,b) and ({a,b} & {"A5-W7-Cu","A5-W7-solder"}):
            return "lamp resistor input land",(-19.98,18.47,17.9,.52)
        return None,None
    pairs = {(a,b) if a<b else (b,a) for a in mesh if a.split("#")[0] in new for b in mesh
             if a.split("#")[0]!=b.split("#")[0]}
    checked=set()
    for a,b in sorted(pairs):
        lower = gap(mesh[a],mesh[b])
        if lower>2.0: continue
        mgap=sc.meshgap(mesh[a],mesh[b])
        a,b=sorted((a.split("#")[0],b.split("#")[0]))
        label,window=classify(a,b)
        if label=="formed lead materials":
            continue
        if mgap>.75: continue
        if (a,b) in checked:continue
        if mgap<.12:checked.add((a,b))
        # Use native common-volume and distance at near-contact locations.
        if mgap<.12:print("Native near pair",a,b,flush=True)
        dist=native[a].distance(native[b]) if mgap<.12 else mgap
        data=dict(pair=[a,b],gap_mm=round(dist,6),method="native" if mgap<.12 else "mesh")
        if dist<1e-5:
            common=native[a].intersect(native[b])
            volume=abs(common.Volume(1e-9))
            data["common_mm3"]=round(volume,7)
            if label and window:
                x,y,z,r=window
                limit=cq.Solid.makeBox(2*r,2*r,2*r,cq.Vector(x-r,y-r,z-r))
                beyond=abs(common.cut(limit).Volume(1e-9)) if volume>1e-7 else 0.
                data.update(interface=label, outside_joint_mm3=round(beyond,7))
                if beyond<1e-6:
                    intentional.append(data);continue
            unexpected.append(data)
        if not label:
            for key in (a,b):
                if key in new and (key not in nearest or data["gap_mm"]<nearest[key]["gap_mm"]):
                    nearest[key]=data
    print("Seated unintended",unexpected,flush=True)
    # Check both release and withdrawal of actual rigid shapes, and the formed
    # W4 free leads on every translation station. Report mesh minima and confirm
    # the limiting posed pair in native OpenCascade geometry.
    body, latch=h6.split_latch(s["A3-J1-plug"])
    rigid={"plug-body":body,"TPA":s["A3-J1-TPA"],**{k:v for k,v in s.items()
           if k.startswith('A3-J1-C') or k.startswith('wh') and k.endswith('-Cu')}}
    best={"rigid":(100.,),"jacket":(100.,)}
    def sweep_test(kind, moving, name, d, angle):
        for key in (k for k in mesh if k.split("#")[0] in new):
            if gap(moving,mesh[key])>best[kind][0]: continue
            result=(sc.meshgap(moving,mesh[key]),name,key.split("#")[0],float(d),float(angle))
            best[kind]=min(best[kind],result)
    for ratio in np.linspace(0,1,9):
        posed=h6.actuate(latch,float(ratio))
        sweep_test('rigid',sc.model(*sc.tri(posed)),'rocker',0,ratio)
    rigid["rocker"]=h6.actuate(latch,1.)
    rmesh={n:sc.model(*sc.tri(v)) for n,v in rigid.items()}
    for d in np.linspace(0,h6.STROKE,133):
        for n,obj in rmesh.items():
            obj.setTranslation(np.array([0,d,0]));sweep_test('rigid',obj,n,d,1)
        for n in h6.NET_PIN:
            r=h6.ROUTES[n]
            x,_,z=r["tap_center_mm"]
            pts=h6.guide(n,x,z,float(d),97)
            obj=sc.tube([[pts[0][0],-5.35+d,10.36]]+pts,h6.RADIUS)
            sweep_test('jacket',obj,n,d,1)
    moving={}
    for kind,(g,n,key,d,ratio) in best.items():
        obj=(h6.native_at(n,d) if kind=='jacket' else
              (h6.actuate(latch,ratio) if n=='rocker' else rigid[n]).translate((0,d,0)))
        exact=sc.native_gap(obj,new[key])
        moving[kind]=dict(moving=n,fixed=key,withdrawal_mm=d,latch_release_fraction=ratio,
                          sampled_mesh_gap_mm=round(g,6),native_at_sample=exact)
    out=dict(installed_manifest_sha256=hashlib.sha256((HERE/"installed.json").read_bytes()).hexdigest(),
             fitted_board_sha256=hashlib.sha256(sources["A5-power"].read_bytes()).hexdigest(),
             fitted_bond_sha256=hashlib.sha256(sources["A5-bond"].read_bytes()).hexdigest(),
             lamp_adhesive_relief=projection,
             nominal_metal_contacts=metal_contacts(s["A5-power"], s["A1-J8"], new),
             seated_shell_members_considered=len(s),inside_broadphase=len(mesh),
             nearest_reported_within_0_75_mm=nearest,unwanted_contacts=unexpected,
             intended_contacts=intentional,service_minima=moving,
             scope="Seated nominal assembly. Native checks below 0.12 mm mesh gap. Nine rocker stations and 133 withdrawal stations, 0.0625 mm spacing. Tabulated minima are sampled.")
    (HERE/"fit.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(moving),flush=True)
    if unexpected or any(v['native_at_sample']['gap_mm']<1e-5 for v in moving.values()):
        raise ValueError("Unwanted contact recorded in fit.json")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cache",type=Path)
    run(cli.parse_args().cache)
