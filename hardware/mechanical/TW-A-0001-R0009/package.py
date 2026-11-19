"""Package the R0009 installed CAD, self-contained inspection viewer, and print kit."""
import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
from zipfile import ZIP_DEFLATED, ZipFile
import zlib

import cadquery as cq
import numpy as np
from build import HERE

REV = HERE.name
REPO = HERE.parents[2]
HARD = REPO / "hardware"
PREVIOUS = "TW-A-0001-R0008"
STEP_HASH = "68251ab24efb2ca10c316666715c86133ce9c5163daa392ff4cc2d1c26e76ebb"
GEOMETRY = re.compile(r'(<script type="application/json" id="geometry">)(.+?)(</script>)', re.S)
CHECKS = re.compile(r'(<script type="application/json" id="checks">)(.+?)(</script>)', re.S)
COLORS = {"VCC":"#b93832","GND":"#353534","SDA":"#5195b2","SCL":"#ccab45"}

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n",encoding="utf8")

def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_reference(path, work):
    cache = work / "r8-reference"
    cache.mkdir(parents=True, exist_ok=True)
    stamp = cache / "sha256.txt"
    if stamp.exists() and stamp.read_text()==STEP_HASH and len(list(cache.glob("*.brep")))==79:
        return
    if hashfile(path)!=STEP_HASH:
        raise ValueError("Use decompressed TW-A-0001-R0008-dressed.step.gz")
    assembly = cq.Assembly.load(str(path))
    if len(assembly.children)!=79:
        raise ValueError("Unexpected R0008 STEP assembly structure")
    for node in assembly.children:
        node.obj.moved(node.loc).exportBrep(str(cache/(node.name+".brep")))
    stamp.write_text(STEP_HASH)
    print("R0008 reference extracted", flush=True)

def data_row(key,name,ref,group,kind,color,source,delta,stage,note,**options):
    return dict(id=key,name=name,ref=ref,group=group,kind=kind,color=color,
                source=source,delta=delta,stage=stage,note=note,option="",**options)

def source_rows():
    rows={}
    paths={}
    def add(path,row):
        paths[row["id"]]=path
        rows[row["id"]]=row
    def registered(path,key):
        return path.relative_to(REPO).as_posix()
    for key, color, name, ref in [
        ("usbSurround","#2e3231","Opaque TPU socket diaphragm","P13"),
        ("statusChgGuide","#b4c3b1","Charge light guide","P14"),
        ("statusUsbGuide","#aab9c7","USB-present light guide","P15"),
        ("statusPwrGuide","#c5b0ad","System-power light guide","P16")]:
        item=next(r for r in load(HERE/"part-orientations.json").values() if r["viewer_id"]==key)
        path=HERE/item["assembly_brep"]
        note="Perimeter-captured rear mask at the OEM socket mouth." if key=="usbSurround" else "Polished, separate light guide inside an opaque channel."
        add(path,data_row(key,name,ref,"Enclosure","R0009 manufactured CAD",color,registered(path,key),[-14,0,0],1,note,finish="rubber" if key=="usbSurround" else "glass"))
    for row in load(HERE/"Installed/speaker/parts.json"):
        path=HERE/"Installed/speaker"/row.pop("brep")
        row["option"]=""
        if row["source"]=="speaker.py":row["source"]=registered(HERE/"speaker.py",row["id"])
        if row["id"]=="speakerCloth":row["finish"]="fabric"
        if row["id"] in ["speakerRim","speakerMagnet","speakerPoleRing","speakerTerminal0","speakerTerminal1"]:row["finish"]="steel"
        add(path,row)
    for path in sorted((HARD/"electronics/haptic-r0009/placed").glob("*.brep")):
        key=path.stem
        color="#b67744" if key.endswith("-Cu") else "#424748"
        ref="A3";note="Placed from the Boardoza DRV2605L production board and assigned workshop wire routes."
        if key=="drvBoard":name="Boardoza DRV2605L PCB";color="#266b57"
        elif key=="drvParts":name="Boardoza DRV2605L populated parts and header"
        elif key=="motor":name="SparkFun ROB-08449 ERM motor and wire stubs";color="#929794";ref="M1";note="SparkFun manufacturer CAD. Two 10 mm modeled wire stubs join the fitted harness."
        elif key=="adhH":name="DRV2605L die-cut foam strips";color="#565550"
        else:
            name=key.removesuffix("-Cu")+" "+("stripped end" if key.endswith("-Cu") else "insulated lead")
            ref="Motor harness" if key.startswith("wm") else "A3 harness"
            if not key.endswith("-Cu"):
                color=COLORS.get(key[2:],"#c39182" if key=="wm0" else "#454a4a")
        kind="Supplier STEP" if key in ("drvBoard","drvParts","motor") else "Workshop cut and formed"
        row=data_row(key,name,ref,"Haptics" if key in ("drvBoard","drvParts","motor","adhH") else "Wiring",kind,color,registered(path,key),[10,5,-14],4,note)
        row["option"]="haptic"
        add(path,row)
    usb={"USB-BOND":("DOWSIL 3145 current-limiter anchor","#74736c"),"USB-D1":("Kingbright blue USB-present LED","#afbac9"),"USB-R1":("Yageo 2.70 kΩ series resistor","#514e4b"),
         "USB-PCB1":("USB light daughterboard","#506b57"),"USB-PCB2":("USB resistor daughterboard","#506b57")}
    for path in sorted((HARD/"electronics/usb-status-r0003/placed").glob("*.brep")):
        key=path.stem
        name,color=usb.get(key,(key+" "+("exposed conductor" if key.endswith("-Cu") else "insulated harness" if "W4" in key else "retention"),"#bd7851" if key.endswith("-Cu") else "#404447" if "W4C" in key else "#a4403c"))
        add(path,data_row(key,name,key,"Status & power","Supplier STEP" if key in ("USB-D1","USB-R1") else "Assembled electrical CAD",color,registered(path,key),[-12,4,-8],5,"Dedicated USB-present channel from J8 VBUS through R1."))
    for key,name,sub,ref,color in [
        ("Switch case","Omron B3F-1002-G switch case","omron-b3f-1002-g","SW1","#393a38"),
        ("Switch plunger","Omron B3F-1002-G plunger","omron-b3f-1002-g","SW1","#77746e"),
        ("Trimmed terminals","Omron B3F-1002-G trimmed terminals","omron-b3f-1002-g","SW1","#a6a49c"),
        ("Grip lock screw","goBILDA zinc-plated M3 × 10 socket screw","gobilda-2800-0003-0010","H7","#a9aaa5")]:
        path=HARD/"components"/sub/(key+".brep")
        row=data_row(key,name,ref,"Power key" if ref=="SW1" else "Rod handle","Supplier component CAD",color,registered(path,key),
                     [0,12,0] if ref=="SW1" else [0,-38,-12],3 if ref=="SW1" else 7,"Installed source geometry with the specified orientation.")
        if ref=="H7":row["option"]="rod"
        add(path,row)
    for file in sorted((HARD/"components/standard-fasteners/placed").glob("*.brep")):
        key=file.stem
        ref="H1" if key.startswith("H1") else "H6" if key=="Keeper screw" else "H8" if key=="Receiver nut" else "H9"
        n={"H1":"M2 × 8 ISO 14583 A2 T6","H6":"M2 × 6 ISO 14583 A2 T6","H8":"M3 DIN 934 hex nut","H9":"M2 × 4 ISO 14583 A2 T6"}[ref]
        add(file,data_row(key,n+" · "+key,ref,"Controller" if ref=="H1" else "Power key" if ref=="H6" else "Rod handle" if ref=="H8" else "Wiring","Standard fastener CAD","#a5a6a3",registered(file,key),[0,0,12],6,"Installed standard-based geometry.",finish="steel"))
    for key,name,color,finish in [("usbSurround","Case-colour TPU diaphragm","#82988e","rubber"),("usbEscutcheonLip","Charcoal TPU socket lip","#292c2a","rubber")]:
        path=HERE/"Installed/diaphragm"/(key+".brep")
        add(path,data_row(key,name,"P13","Enclosure","R0009 co-printed material region",color,registered(path,key),[-14,0,0],1,"One of two contiguous regions of the single flexible rear mask. Print both together.",finish=finish))
    pcb=HARD/"electronics/power-key-r0009/Key PCB.brep"
    add(pcb,data_row("Key PCB","Gerber-drilled power key carrier","PCB1","Power key","Fabricated board CAD","#398062",registered(pcb,"Key PCB"),[0,12,0],3,"Four nominal 1.00 mm plated lead holes from the released drill file. Confirm stamped-leg fit and solderability.",finish="soldermask"))
    for i in (0,1):
        key="shrink"+str(i);path=HARD/"components/te-rnf-100"/(key+".brep")
        add(path,data_row(key,"Raychem W2 splice insulation "+str(i+1),"W2","Wiring","Cut and recovered supplier stock","#363836",registered(path,key),[8,4,-8],4,"6 mm recovered sleeve on a 0.9 mm wire. Verify solder bulge and coverage on the assembly.",finish="rubber",mpn="RNF-100-1/16-0-SP",modelUrl="https://www.te.com/en/product-5052894048.html"))
    path=HARD/"electronics/harness-r0003/placed/W1-P.brep"
    add(path,data_row("J8plug","XKB right-angle J8 four-pin header","W1-P","Wiring","Supplier STEP","#404441",registered(path,"J8plug"),[0,5,-9],5,"3.80 mm pin engagement with the stock J8. Confirm solder-tail net order at the actual device.",mpn="X6511WR-04H-C60D30R1",modelUrl="https://lceda.cn/api/products/C2883842/components?version=6.4.19.5"))
    for path in sorted((HARD/"components/reel-fasteners/placed").glob("*.brep")):
        key=path.stem
        if key in ("H3-1","H3-2"):
            add(path,data_row(key,"OPAC DIN 125 nylon M2 hinge shim "+key[-1],"H3","Reel & encoder","Standard fastener CAD","#e4dfc6",registered(path,key),[7,0,0],2,"2.2 mm ID, 5 mm OD, 0.30 mm thick. Keep seated against the correct hinge cheek.",mpn="125N-2",modelUrl="https://www.opac.net/en/producto-581-din-34815-%28din-125%29%2A"))
    for net,color in COLORS.items():
        key="w1"+net
        path=HARD/"electronics/harness-r0003/placed"/(key+".brep")
        add(path,data_row(key,"Reel "+net,"W1","Wiring","Custom formed harness",color,registered(path,key),[0,5,-9],5,"J8-to-encoder branch, with the modeled solder-tail order and haptic tee kept on its registered datum."))
    suppliers=[
        ("reel0","H2","M2 × 10 black A2 pan screw","SHP-M2-10-V2-A2-BL","reel-fasteners/placed","#414340","https://www.accu.co.uk/torx-pan-head-screws/475614-SHP-M2-10-V2-A2-BL"),
        ("reel1","H4","M2 × 5 black A2 knob retainer","SHP-M2-5-V2-A2-BL","reel-fasteners/placed","#414340","https://www.accu.co.uk/torx-pan-head-screws/475608-SHP-M2-5-V2-A2-BL"),
        ("H5","H5","Stainless knob thrust washer","HPW-M2-A2","reel-fasteners/placed","#a6a6a0","https://www.accu.co.uk/metric-flat-washers/72476-HPW-M2-A2"),
        ("reel2","MG1","Diametric N35 nickel-plated rotor magnet","8995","radial-8995","#b3b3ab","https://radialmagnet.com/our-magnets/disk-sensor-n35-nicuni-d6mma-x-2-5mm/")
    ]
    for key,ref,name,mpn,folder,color,url in suppliers:
        path=HARD/"components"/folder/(key+".brep")
        add(path,data_row(key,name,ref,"Reel & encoder","Supplier CAD" if key=="reel2" else "Standard fastener CAD",color,registered(path,key),[10,0,2],2,"Installed to the registered rotating mechanism datum.",finish="steel",mpn=mpn,modelUrl=url))
    loom=HARD/"electronics/harness-r0003/placed"
    for key,name,mpn,url in [
        ("j7plug","J7 PicoBlade receptacle housing","51021-0200","https://www.molex.com/en-us/products/part-detail/510210200"),
        ("j9plug","J9 PicoBlade receptacle housing","51021-0200","https://www.molex.com/en-us/products/part-detail/510210200"),
        ("ph","W2 JST PH 2-pole header","B2B-PH-K-S","https://lceda.cn/api/products/C131337/components?version=6.4.19.5"),
        ("packplug","Battery JST PH receptacle housing","PHR-2","https://www.jst-mfg.com/product/detail_e.php?series=199")]:
        path=loom/(key+".brep")
        add(path,data_row(key,name,"W2" if key!="j9plug" else "W5","Wiring","Supplier component CAD", "#e5dfc8" if key!="ph" else "#d8cfb7",registered(path,key),[1,-6,-8],5,"Placed using the component mating interfaces. Check polarity and retention on the actual lot.",mpn=mpn,modelUrl=url))
    for site in ("J7","J9"):
        for pin in (1,2):
            key=site+"-C"+str(pin);path=loom/(key+".brep")
            add(path,data_row(key,site+" formed crimp contact "+str(pin),site,"Wiring","Supplier STEP","#a7a39c",registered(path,key),[1,-6,-8],5,"Molex formed PicoBlade contact at its source-housing cavity.",finish="steel",mpn="50079-8000",modelUrl="https://www.molex.com/en-us/products/part-detail/500798000"))
    for path in sorted(loom.glob("tee-*.brep")):
        key=path.stem
        add(path,data_row(key,key.replace("-"," "),"W4","Wiring","Formed harness junction","#9c6d49" if key.endswith("Cu") else "#44413d",registered(path,key),[0,5,-9],5,"Staggered soldered tap, individually insulated. Fit the optional motor loom before dressing the branch."))
    for path in sorted(loom.glob("termination-*.brep")):
        key=path.stem
        add(path,data_row(key,key.removeprefix("termination-")+" stripped conductor",key.split("-")[1],"Wiring","Formed wire termination","#af7551",registered(path,key),[1,-6,-8],5,"Bare end seated inside the crimp or soldered along its J8 header tail. Confirm crimp height and continuity on the physical loom."))
    for i in (1,2):
        for token,label,color in [("TAIL","lap conductor","#b18155"),("INS","joint sleeve","#504846")]:
            key=f"PH-{token}{i}"
            path=loom/(key+".brep")
            add(path,data_row(key,f"Battery adapter {label} {i}","W2","Wiring","Formed adapter termination",color,registered(path,key),[1,-6,-8],5,"Insulate the two PH header joints individually before installing the adapter."))
    if (loom/"batt0.brep").exists():
        for i in (0,1):
            for key,file,ref in [("batt"+str(i),"batt"+str(i),"W2"),("altTail"+str(i),"altTail"+str(i),"B1"),("drawingTail"+str(i),"drawingTail"+str(i),"B1"),("pack"+str(i),"catalogTail"+str(i),"B1")]:
                path=loom/(file+".brep")
                add(path,data_row(key,ref+" "+("positive" if i==0 else "return")+" lead",ref,"Wiring","Custom formed harness",["#b4483c","#353737"][i],registered(path,key),[5,-5,-12],4,"Factory lead length or measured adapter route to the actual connector exit."))
    return rows,paths

def get_model():
    template=(REPO/"docs/models"/(PREVIOUS+"-exploded.html")).read_text(encoding="utf8")
    rows={r["id"]:r for r in json.loads(GEOMETRY.search(template)[2])}
    updates,paths=source_rows()
    for stem,item in load(HERE/"part-orientations.json").items():
        key=item["viewer_id"]
        if not key:continue
        path=HERE/item["assembly_brep"]
        if key not in updates:
            paths[key]=path
            row=rows[key].copy()
            row["source"]=path.relative_to(REPO).as_posix()
            row["kind"]="R0009 manufactured CAD"
            if key=="Housing":
                row.update(name="R0009 USB-baffled housing",note="Case-colour cable lead-in, captive opaque rear mask, independent status sleeves and bottom-firing SP1 seat.")
            updates[key]=row
    for key,row in updates.items():
        rows[key]={**rows.get(key,{}),**row}
    catalogue=[
       (lambda r:r["id"]=="motor","ROB-08449","https://github.com/sparkfun/3D_Models/tree/53d298c3b8202cf8fce9ab61885855720c84c012/products/8449"),
       (lambda r:r["id"] in ("drvBoard","drvParts"),"B0601V10000076","https://github.com/Boardoza/Boardoza_DRV2605L_Haptic_Driver_Breakout_Board/tree/a23e28dcaa4ffa82e68108e668a1f46f7c24a0a8"),
       (lambda r:r["ref"]=="SP1","3923","https://github.com/adafruit/Adafruit_CAD_Parts/tree/9f2a89f3d5c3491886d58cb7fe83385417563cf4/3923%20Mini%20Oval%20Speaker"),
       (lambda r:r["id"]=="Grip lock screw","2800-0003-0010","https://www.gobilda.com/content/step_files/2800-0003-0010.zip"),
       (lambda r:r["id"] in ("Switch case","Switch plunger","Trimmed terminals"),"B3F-1002-G","https://gitlab.com/kicad/libraries/kicad-packages3D/-/blob/master/Button_Switch_THT.3dshapes/SW_TH_Tactile_Omron_B3F-100x.step"),
       (lambda r:r["id"]=="USB-D1","APG1608QBC/D","https://www.kingbrightusa.com/images/catalog/3D/STEP/APG1608.STEP"),
       (lambda r:r["id"]=="USB-R1","RC0603FR-072K7L","https://lceda.cn/api/products/C114612/components?version=6.4.19.5"),
       (lambda r:r["id"]=="cellAlt","258","https://www.adafruit.com/product/258"),
       (lambda r:r["id"].startswith("A1-"),"ESP32-S3-Touch-LCD-3.5B","https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B/Resources-And-Documents"),
       (lambda r:r["id"].startswith("A2-"),"Adafruit AS5600","https://learn.adafruit.com/adafruit-as5600-magnetic-angle-sensor/downloads")
    ]
    for row in rows.values():
        for match,mpn,url in catalogue:
            if match(row):row.update(mpn=mpn,modelUrl=url);break
        if row["ref"] in ("H1","H6","H8","H9") and row["kind"]=="Standard fastener CAD":
            mpn={"H1":"SHP-M2-8-V2-A2","H6":"SHP-M2-6-V2-A2","H8":"HPN-M3-A2","H9":"SHP-M2-4-V2-A2"}[row["ref"]]
            row.update(mpn=mpn,modelUrl="https://github.com/gumyr/cq_warehouse/tree/a57bb7a24762d367d66369f280a24c38a64e73dd")
    for key,row in rows.items():
        inherited_supplier={"A1-touch","A1-mounts","A1-carrier","A1-population","A1-J8","A1-usb","A1-k3","A1-reset","A1-boot","A1-J7","A1-J9","A1-backing","A2-pcb","A2-population","A2-sockets","A2-chip","cellAlt"}
        formed_wires={"batt0","batt1","w30","w31","w1VCC","w1GND","w1SDA","w1SCL","altTail0","altTail1"}
        row["productEligible"]=(key in paths or key in inherited_supplier or key in formed_wires) and key not in {"Cell","cellDrawing","pack0","pack1","drawingTail0","drawingTail1","usbGauge","hdrPins"}
        if key=="cellAlt" or key.startswith("altTail"):row["batteryVariant"]="alt"
        if key.startswith("drawingTail"):row["batteryVariant"]="drawing"
    return template,rows,paths

def bbox(shape):
    b=shape.BoundingBox()
    return [round(getattr(b,a),4) for a in ("xmin","xmax","ymin","ymax","zmin","zmax")]

def shape_mesh(shape):
    v,f=shape.tessellate(.035,.10)
    def enc(a):
        return base64.b64encode(zlib.compress(a.tobytes(),7)).decode()
    return dict(v=enc(np.rint(np.array([p.toTuple() for p in v])*100).astype("<i2")),
                t=enc(np.array(f,dtype="<u4")),bounds_mm=bbox(shape),solids=len(shape.Solids()))

def write_viewer(exports,work):
    template,rows,paths=get_model()
    for key,path in paths.items():
        # Cache only geometry. Stale product metadata or renderer code never survives a rebuild.
        cache=work/"mesh-cache"
        cache.mkdir(exist_ok=True)
        signature=hashfile(path)
        meshfile=cache/(signature+"-035-10-v1.json")
        if meshfile.exists():
            mesh=load(meshfile)
        else:
            print("Tessellate",key,flush=True)
            shape=cq.Shape.importBrep(str(path))
            mesh=shape_mesh(shape)
            save(meshfile,mesh)
        rows[key].update(mesh)
        rows[key]["geometrySha256"]=signature
    for surface_file in (HARD/"visualization/vendor-surfaces.json",HERE/"Installed/source-surfaces.json"):
        for key,surf in load(surface_file).items():
            if key in rows:rows[key].update(surf)
    # An immutable historical model records the basis for the battery comparisons.
    checks=json.loads(CHECKS.search(template)[2]);checks.update(revision="R0009",reference="Rev G battery comparisons")
    checks["r0009_port"]=load(HERE/"QA/usb-port.json")
    template=GEOMETRY.sub(lambda m:m[1]+json.dumps(list(rows.values()),ensure_ascii=False,separators=(",",":"))+m[3],template,count=1)
    template=CHECKS.sub(lambda m:m[1]+json.dumps(checks,separators=(",",":"))+m[3],template,count=1)
    js=(HARD/"visualization/assembly-renderer.min.js").read_text(encoding="utf8")
    template=re.sub(r"<script>.*?</script>",lambda m:"<script>"+js+"</script>",template,count=1,flags=re.S)
    template=template.replace("R0008 · Assembly","R0009 · Assembly").replace(">R0008<",">R0009<").replace('<option value="alt">','<option value="alt" selected>').replace('<option value="drawing" selected>','<option value="drawing">')
    out=REPO/"docs/models"/(REV+"-exploded.html")
    out.write_text(template,encoding="utf8")
    shutil.copyfile(out,exports/out.name)
    save(HERE/"assembly-parts.json",[{k:v for k,v in row.items() if k not in ("v","t","c")} for row in rows.values()])
    print("Viewer entries",len(rows),flush=True)

def write_step(exports,work):
    _,rows,paths=get_model()
    from sys import path as import_paths
    import_paths.insert(0,str(HERE.parent/"rev-G"))
    import geometry as g
    cell=cq.importers.importStep(str(HERE.parent/"rev-F/review/inputs/Adafruit-258.step")).val().translate((g.CX,g.CY,g.Z))
    extra={"cellAlt":cell}
    for i in range(2):
        if "altTail"+str(i) not in paths:extra["altTail"+str(i)]=g.factory_lead("alt",i)[0]
    result=cq.Assembly(name="TW_A_0001_R0009_supplier_cell")
    ledger={}
    for k,row in rows.items():
        if not row["productEligible"]:continue
        path=paths.get(k,work/"r8-reference"/(k+".brep"))
        shape=extra.get(k)
        if shape is None:shape=cq.Shape.importBrep(str(path))
        result.add(shape,name=k,color=cq.Color(row["color"]))
        ledger[k]=dict(volume_mm3=round(shape.Volume(),5),solids=len(shape.Solids()),bounds_mm=bbox(shape))
    dest=work/(REV+".step")
    result.export(str(dest))
    output=exports/(REV+"-dressed.step.gz")
    with dest.open("rb") as inp,output.open("wb") as file:
        with gzip.GzipFile(filename="",fileobj=file,mode="wb",compresslevel=6,mtime=0) as packed:
            shutil.copyfileobj(inp,packed)
    save(HERE/"installed-step.json",dict(component_count=len(ledger),step_sha256=hashfile(dest),components=ledger))
    print("Installed STEP",len(ledger),output.stat().st_size,flush=True)

def write_kit(exports):
    members={}
    controls=io.BytesIO()
    baseline=HERE.parent/PREVIOUS
    with ZipFile(controls,"w",ZIP_DEFLATED,compresslevel=6) as inputs:
        inputs.write(baseline/"part-orientations.json","part-orientations.json")
        for folder in ("CAD","Print"):
            for file in sorted((baseline/folder).iterdir()):
                if file.is_file():inputs.write(file,file.relative_to(baseline).as_posix())
    parts=load(HERE/"part-orientations.json")
    for stem,r in parts.items():
        members[r["print_stl"]]=HERE/r["print_stl"]
    members["Print/usb-c-shield-mask-two-colour.3mf"]=HERE/"Print/usb-c-shield-mask-two-colour.3mf"
    for sub in ["CAD","QA","Installed"]:
        for path in (HERE/sub).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                members[path.relative_to(HERE).as_posix()]=path
    for filename in ["build.py","package.py","speaker.py","diaphragm.py","render_port.py","surface_finishes.py","verify_exports.py","usb-front.png","usb-three-quarter.png","PRINT-GUIDE.md","part-orientations.json","assembly-parts.json","installed-step.json","export-verification.json"]:
        members[filename]=HERE/filename
    output=exports/(REV+"-fit-print.zip")
    with ZipFile(output,"w",ZIP_DEFLATED,compresslevel=7) as z:
        raw=controls.getvalue()
        z.writestr("inputs/R0008-print-inputs.zip",raw)
        hashes=[hashlib.sha256(raw).hexdigest()+"  inputs/R0008-print-inputs.zip"]
        for name,path in sorted(members.items()):
            data=path.read_bytes();z.writestr(name,data)
            hashes.append(hashlib.sha256(data).hexdigest()+"  "+name)
        z.writestr("SHA256SUMS.txt","\n".join(hashes)+"\n")
    with ZipFile(output) as z:
        assert z.testzip() is None
        for line in z.read("SHA256SUMS.txt").decode().splitlines():
            digest,path=line.split("  ",1)
            assert hashlib.sha256(z.read(path)).hexdigest()==digest
        assert len([path for path in z.namelist() if path.endswith(".stl")])==18
    print("Print kit",len(members),output.stat().st_size,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("targets",nargs="+",choices=("cache","step","viewer","kit"))
    p.add_argument("--exports",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--reference-step",type=Path)
    a=p.parse_args()
    if "cache" in a.targets or "step" in a.targets:read_reference(a.reference_step,a.work)
    if "step" in a.targets:write_step(a.exports,a.work)
    if "viewer" in a.targets:write_viewer(a.exports,a.work)
    if "kit" in a.targets:write_kit(a.exports)



