"""Cross-check both circuit pin lists against the candidate schematic and generate its BOM."""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from build import HERE,A4,A5,reference

def pins(file,power=False,controls=False):
    nets=defaultdict(set)
    root=ET.parse(file)
    for net in root.findall(".//nets/net"):
        name=net.get("name")
        if controls and name=="USB_RAW":name="PMIC"
        if power:name=re.sub(r"(?<=\()([A-Z]+\d+)-",lambda m:reference(m[1])+"-",name)
        for pin in net.findall("node"):
            r=pin.get("ref")
            nets[name].add((reference(r) if power else r,pin.get("pin")))
    return nets

def run(controls,combined):
    expected=pins(controls,controls=True)
    for n,ps in pins(A5/"connectivity.xml",power=True).items():expected[n].update(ps)
    actual=pins(combined)
    assert actual==expected,{n:(expected.get(n),actual.get(n)) for n in actual.keys()|expected.keys() if actual.get(n)!=expected.get(n)}
    assert actual["ENTRY"]=={("W101","1"),("FB101","1")}
    assert ("W102","1") in actual["PMIC"] and ("J8","1") in actual["PMIC"]
    rows=[]
    for power,path in [(False,A4),(True,A5)]:
        for row in csv.reader((path/"bom.csv").read_text(encoding="utf8").splitlines()[1:]):
            if not row:continue
            ref,qty,maker,mpn,desc,src=row
            if ref=="PCB":continue
            if power and (" " not in ref or ref.startswith(("W","Q","C","R"))) and not ref.startswith(("USB-PCB","A1 ")):
                ref=" ".join(reference(s) for s in ref.split())
                desc=re.sub(r"\b(?:U[12]|R[78])\b",lambda m:reference(m[0]),desc)
            if src=="assembly.csv":src="../usb-entry-r0006/assembly.csv"
            rows.append([ref,qty,maker,mpn,desc,src])
    rows.extend([["PCB","1","Custom","Case-board R0001","32.8 × 38.2 mm overall, 0.8 mm FR4, two copper layers","case-board.kicad_pcb"],
                 ["Mount screws","2","Accu","SHP-M2-4-V2-A2","M2 × 4 ISO 14583 T6 pan head","../../components/standard-fasteners/README.md"]])
    with (HERE/"bom.csv").open("w",encoding="utf8",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["reference","quantity","manufacturer","part_number","description","source"])
        writer.writerows(rows)
    print(len(actual),"nets,",sum(len(ps) for ps in actual.values()),"pins")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("controls_netlist",type=Path)
    p.add_argument("combined_netlist",type=Path)
    args=p.parse_args()
    run(args.controls_netlist,args.combined_netlist)
