"""Check that the published results describe one revision. Only the standard library is needed."""
from pathlib import Path
import csv
import hashlib
import json
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
M=ROOT/"hardware/mechanical/TW-A-0001-R0012"
H=ROOT/"hardware/electronics/harness-r0005"

def load(path):
    return json.loads(path.read_bytes())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def match(value,expected,description):
    if value!=expected:
        raise ValueError(description)

def main():
    step=load(M/"export-verification.json")
    motion=load(H/"clearance.json")
    sim=load(HERE/"replay.json")
    match(step["harness_manifest_sha256"],digest(H/"installed.json"),"STEP / harness mismatch")
    match(load(HERE/"installed-fit.json")["installed_step_sha256"],step["step_sha256"],"Static fit / STEP mismatch")
    match(load(M/"QA/service-roundtrip.json")["step_sha256"],step["step_sha256"],"Service sweep / STEP mismatch")
    match(load(HERE/"r19b-shell-fit.json")["harness_sha256"],digest(H/"installed.json"),"Printed shell / harness mismatch")
    match(sim["routing_sha256"],digest(H/"routing.json"),"SPICE / wire route mismatch")
    match(sim["copper_report_sha256"],digest(HERE/"copper.json"),"SPICE / copper mismatch")
    boards={"A3":"pcb-haptic-cie-r0001/A3-CIE-R0001.kicad_pcb","A4":"pcb-r0004/harness.kicad_pcb","A5":"pcb-power-r0004/usb-input.kicad_pcb"}
    for key,file in boards.items():
        match(sim["board_sha256"][key],digest(H.parent/file),key+" routed board mismatch")
    match(sim["archive_sha256"],digest(HERE/"postlayout-logs.zip"),"SPICE archive mismatch")
    with ZipFile(HERE/"postlayout-logs.zip") as logs:
        match(logs.testzip(),None,"Bad solver archive")
    rows=list(csv.DictReader((M/"QA/service-path.csv").open()))
    match(len(rows),76,"Incomplete service sweep")
    match(float(rows[-1]["travel_mm"]),motion["stroke_mm"],"Wrong motion endpoint")
    print("Verified routed sources, simulation evidence, STEP identity, both fit studies and the 76-station service path.")
if __name__=="__main__":
    main()
