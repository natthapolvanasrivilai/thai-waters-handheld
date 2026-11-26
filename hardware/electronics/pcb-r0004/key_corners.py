"""Replay the changed W3 diode-OR key circuit with ngspice. Writes solver evidence."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--engine", required=True, type=Path)
parser.add_argument("--output", type=Path, default=ROOT)
options = parser.parse_args()
exe = options.engine.resolve()
ROOT = options.output.resolve()
ROOT.mkdir(parents=True, exist_ok=True)
rails = [
    ("cell_min",3,0), ("cell_full",4.2,0), ("usb_low",0,4.75), ("usb_nom",0,5),
    ("usb_high",0,5.25), ("both_lowpack",3,5), ("both_fullpack",4.2,4.75)
]
measurements = {
    "raw_v":"v(raw)", "pwron_v":"v(pwron)", "aon_v":"v(aon)", "gate_v":"v(drive)",
    "cell_source_a":"i(Vcell)", "usb_source_a":"i(Vusb)"
}
rows = []
with TemporaryDirectory() as work, ZipFile(ROOT/"key-solver.zip", "w", compression=ZIP_DEFLATED) as archive:
    tmp=Path(work)
    cases = list(product(rails, (1,2), (("pressed",.2),("dirty",10000),("released",1e10)), (.05,.9)))
    # The original 3.3 V sense fixture remains present while the no-cell OR input is disconnected.
    cases.append((("usb_lead_open_fault",0,0),2,("dirty",10000),.9))
    for (state,cell,usb),variant,(contact,resistance),vf in cases:
        ident=f"{state}_v{variant}_{contact}_{str(vf).replace('.','p')}"
        gate_network = ("R37 sensor raw 1k\nR65 logic sensor 100k" if variant==2 else
                        "R37 sensor pwron 1k\nRsensor sensor 0 1T")
        net = f"""R0004 {ident} / remote-key source selection
Vcell vc 0 {cell}
Vusb vu 0 {usb}
* Piecewise forward drop plus 2 ohms. Reverse branch gives 80 nA at 5.25 V.
Bcell vc aon I=max((v(vc,aon)-{vf})/2,0)+min(v(vc,aon),0)/65.625Meg
Busb vu aon I=max((v(vu,aon)-{vf})/2,0)+min(v(vu,aon),0)/65.625Meg
Rleak aon 0 1G
Vlogic logic 0 3.3
Rpull aon key 326.7k
Rcontact key 0 {resistance}
Mp drive key aon aon pmodel W=1u L=1u
Roff drive 0 99k
Mn raw drive 0 0 nmodel W=1u L=1u
.model pmodel PMOS(level=1 VTO=-1.5 KP=.05)
.model nmodel NMOS(level=1 VTO=1.5 KP=.05)
Rinternal logic pwron 50k
R38 pwron raw 510
{gate_network}
.options reltol=1e-6 abstol=1p gmin=1e-13
.tran 1u 10u
"""
        net += "\n".join(f".meas tran {name} FIND {node} AT=9u" for name,node in measurements.items()) + "\n.end\n"
        deck=tmp/(ident+".cir")
        log=tmp/(ident+".log")
        deck.write_text(net,encoding="ascii")
        run=subprocess.run([str(exe),"-b","-o",str(log),str(deck)],cwd=tmp,capture_output=True)
        logtext=log.read_text(errors="replace")
        if run.returncode or not logtext or re.search("failed|fatal error",logtext,re.I):
            raise RuntimeError(ident+"\n"+logtext[-2000:])
        values={name:float(re.search(r"^"+name+r"\s*=\s*([-+\d.eE]+)",logtext,re.M).group(1)) for name in measurements}
        good = (values["pwron_v"] >= 2.97 and values["raw_v"] >= 2.97 if contact == "released"
                else max(values["pwron_v"],values["raw_v"]) <= .33)
        if good != (state != "usb_lead_open_fault"):
            raise ValueError((ident,values))
        rows.append({"case":ident,"state":state,"A1_variant":variant,"contact":contact,"cell_v":cell,
                     "usb_v_at_D1":usb,"diode_knee_v":vf,**values,
                     "result":"PASS" if good else "EXPECTED FAULT"})
        archive.write(deck,deck.name)
        archive.write(log,log.name)
with (ROOT/"key-corners.csv").open("w",encoding="utf8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
valid=[r for r in rows if r["result"]=="PASS"]
pressed=[r for r in valid if r["contact"]!="released"]
release=[r for r in valid if r["contact"]=="released"]
summary={
    "ngspice_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
    "valid_cases":len(valid),"fault_controls":len(rows)-len(valid),
    "max_pressed_pwron_v":max(r["pwron_v"] for r in pressed),
    "max_pressed_raw_v":max(r["raw_v"] for r in pressed),
    "min_released_pwron_v":min(r["pwron_v"] for r in release),
    "min_released_raw_v":min(r["raw_v"] for r in release),
    "min_pressed_key_aon_v":min(r["aon_v"] for r in pressed),
    "max_active_source_current_uA":max(-min(r["cell_source_a"],r["usb_source_a"]) for r in valid)*1e6,
    "fault_control_pwron_v":rows[-1]["pwron_v"],
}
print(json.dumps(summary, indent=2))

