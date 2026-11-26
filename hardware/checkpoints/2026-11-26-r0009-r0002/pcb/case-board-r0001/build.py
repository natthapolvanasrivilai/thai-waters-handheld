"""Build the case-mounted board from the two registered, routed circuits (KiCad 10)."""
from pathlib import Path
import json
import re
import uuid

HERE = Path(__file__).resolve().parent
A4 = HERE.parent / "pcb-r0004"
A5 = HERE.parent / "usb-entry-r0006"
NAME = "case-board"
ORIGINS = [(100, 102), (100, 117)]
REST = (37.5, 19.85)
MOUNTS = [(123, 99.6), (97.5, 117.9)]
# Installed board mapping: X = KiCad X - 87, Y = KiCad Y - 114.
OUTLINE = [(93.8,102),(119.5,102),(121,97.5),(125.1,97.5),(125.5,98),
           (125.5,101.5),(123.2,103.3),(123.2,129.5),(126.3,131.5),
           (126.3,135.1),(125.7,135.7),(122,135.7),(120.7,133.2),
           (100,133.2),(99.7,132.9),(99.7,120.9),(95.2,120.0),
           (95.2,116.8),(93.5,115.0),(93.5,102.3)]

def parse(path):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', path.read_text(encoding="utf8"))
    stack, root = [], []
    for token in tokens:
        if token == "(":
            item = []
            (stack[-1] if stack else root).append(item)
            stack.append(item)
        elif token == ")":
            stack.pop()
        else:
            stack[-1].append(token)
    assert not stack and len(root) == 1
    return root[0]

def items(obj, key):
    return [n for n in obj if isinstance(n,list) and n[0] == key]

def one(obj,key):
    return items(obj,key)[0]

def walk(n):
    yield n
    for child in n:
        if isinstance(child,list):
            yield from walk(child)

def emit(n):
    if isinstance(n,str):
        return n
    return "("+" ".join(emit(child) for child in n)+")"

def write_file(root,ext):
    (HERE/(NAME+ext)).write_text("("+root[0]+"\n"+"\n".join(map(emit,root[1:]))+"\n)\n",encoding="utf8")

def quote(s):
    return json.dumps(s)

def unique(label):
    return quote(str(uuid.uuid5(uuid.NAMESPACE_URL, "thaiwaters:case-board:r1:"+label)))

def reference(name):
    return re.sub(r"^([A-Z]+)(\d+)$",lambda m:m[1]+str(100+int(m[2])),name)

def shift(point,dx,dy):
    for i,d in [(1,dx),(2,dy)]:
        point[i]=str(round(float(point[i])+d,6))

def schematic():
    sch=parse(A4/"harness.kicad_sch")
    power=parse(A5/"usb-input.kicad_sch")
    base=one(sch,"uuid")[1].strip('"')
    title=one(sch,"title_block")
    one(title,"title")[1]=quote("Thai Waters | Case-mounted control and USB power")
    one(title,"rev")[1]=quote("Engineering board R0001")
    sch[:]=[p for p in sch if not isinstance(p,list) or p[0]!="text"]
    one(sch,"paper")[1]='"A1"'
    for s in items(power,"lib_symbols")[0][1:]:
        one(sch,"lib_symbols").append(s)
    skips={"lib_symbols","generator","generator_version","version","uuid","paper",
           "title_block","sheet_instances","embedded_fonts"}
    for n in power[1:]:
        if n[0] in skips:continue
        for p in walk(n):
            if p[0] in ("at","xy"):shift(p,304.8,0)
            if p[0]=="reference" or (p[0]=="property" and p[1]=='"Reference"'):
                p[-1 if p[0]=="reference" else 2]=quote(reference(p[1 if p[0]=="reference" else 2].strip('"')))
        if n[0]=="text":
            # Preserve references to components on A1 in the source instructions.
            n[1]=re.sub(r'\b(?:W[1-7]|FB1|[QR][1-39]|U[12]|C[13])\b',lambda m:reference(m[0]),n[1])
        sch.append(n)
    for n in sch[1:]:
        if n[0]=="lib_symbols":continue
        for p in walk(n):
            if p[0]=="project":p[1]=quote(NAME)
            if p[0]=="path" and items(p,"reference"):p[1]=quote("/"+base)
            if p[0]=="global_label" and p[1]=='"USB_RAW"':p[1]='"PMIC"'
            if p[:3]==["property",'"Value"','"USB_RAW"']:p[2]='"PMIC"'
    write_file(sch,".kicad_sch")
    return {one(s,"property")[2].strip('"'):one(s,"uuid")[1].strip('"') for s in items(sch,"symbol")}

def board(symbols):
    a=parse(A4/"harness.kicad_pcb")
    b=parse(A5/"usb-input.kicad_pcb")
    header={"version","generator","generator_version","general","paper","layers","setup","embedded_fonts"}
    pcb=[a[0]]+[p for p in a[1:] if p[0] in header]
    for index,src in enumerate((a,b)):
        dx,dy=ORIGINS[index]
        for p in src[1:]:
            if p[0] in header:continue
            if items(p,"layer") and one(p,"layer")[1]=='"Edge.Cuts"':continue
            if p[0]=="footprint":
                ref=next(v for v in items(p,"property") if v[1]=='"Reference"')
                name=ref[2].strip('"')
                if index:name=reference(name)
                ref[2]=quote(name)
                p[:]=[v for v in p if not isinstance(v,list) or v[0] not in ("path","sheetname","sheetfile")]
                p.append(["path",quote("/"+symbols[name])])
                shift(one(p,"at"),dx - (6 if not index and name in {"R1","R2","J1","J2","J3","J4"} else 0),dy)
            else:
                for v in walk(p):
                    if v[0] in ("start","end","at","mid","xy"):
                        audio=not index and items(p,"net") and one(p,"net")[1].strip('"') in {"AMP_P","SPK_P","AMP_N","SPK_N"}
                        shift(v,dx-(6 if audio else 0),dy)
            for v in walk(p):
                if v[:3]==["property",'"Value"','"USB_RAW"']:v[2]='"PMIC"'
                if v[0]=="net":
                    if v[1]=='"USB_RAW"':v[1]='"PMIC"'
                    if index:v[1]=re.sub(r"(?<=\()([A-Z]+\d+)-",lambda m:reference(m[1])+"-",v[1])
            pcb.append(p)
    for i,start in enumerate(OUTLINE):
        end=OUTLINE[(i+1)%len(OUTLINE)]
        pcb.append(["gr_line",["start",*map(str,start)],["end",*map(str,end)],
                ["stroke",["width","0.05"],["type","default"]],["layer",'"Edge.Cuts"'],["uuid",unique("edge"+str(i))]])
    for i,(x,y) in enumerate(MOUNTS):
        pcb.append(["gr_circle",["center",str(x),str(y)],["end",str(x+1.15),str(y)],["stroke",["width","0.05"],["type","default"]],["fill","no"],["layer",'"Edge.Cuts"'],["uuid",unique("hole"+str(i))]])
    routing=HERE/"links.json"
    if routing.exists():
        for j,link in enumerate(json.loads(routing.read_text())):
            net,layer,*points=link
            if layer=="via":
                x,y=points[0]
                pcb.append(["via",["at",str(x),str(y)],["size","0.55"],["drill","0.3"],["layers",'"F.Cu"','"B.Cu"'],["net",quote(net)],["uuid",unique("via"+str(j))]])
            else:
                for k,(start,end) in enumerate(zip(points,points[1:])):
                    pcb.append(["segment",["start",*map(str,start)],["end",*map(str,end)],["width","0.25"],["layer",quote(layer)],["net",quote(net)],["uuid",unique(f"link{j}-{k}")]])
    write_file(pcb,".kicad_pcb")

if __name__=="__main__":
    board(schematic())
    for kind in ("sym","fp"):
        file=kind+"-lib-table"
        a,b=parse(A4/file),parse(A5/file)
        names={one(v,"name")[1] for v in items(a,"lib")}
        for lib in items(b,"lib"):
            if one(lib,"name")[1] not in names:a.append(lib)
        (HERE/file).write_text(emit(a).replace("${KIPRJMOD}/TW.pretty","${KIPRJMOD}/../pcb-r0004/TW.pretty").replace("${KIPRJMOD}/TW_Power.kicad_sym","${KIPRJMOD}/../usb-entry-r0006/TW_Power.kicad_sym").replace("\\$","$")+"\n")
    (HERE/(NAME+".kicad_pro")).write_text((A5/"usb-input.kicad_pro").read_text().replace("usb-input",NAME))
