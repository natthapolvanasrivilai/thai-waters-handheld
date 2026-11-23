"""Verify that the service viewer, mechanical model and electrical evidence use one revision."""
from pathlib import Path
import csv
import hashlib
import json
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MECH=ROOT/"hardware/mechanical/TW-A-0001-R0013"
ELEC=ROOT/"hardware/electronics"
WIRES=ELEC/"harness-r0006"
A3=ELEC/"pcb-haptic-cie-r0002"
A5=ELEC/"usb-entry-r0006"

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def verify():
    overlay=read(MECH/"overlay.json")
    for row in overlay["add"]:
        require(sha(MECH/row["brep"])==row["sha256"],row["name"])
    export=read(MECH/"export-verification.json")
    require(export["harness_manifest_sha256"]==sha(MECH/"overlay.json"),"STEP versus assembly overlay")
    step=export["step_sha256"]
    for p,field in [(MECH/"installed-step.json","step_sha256"), (MECH/"QA/installed-fit.json","step_sha256")]:
        require(read(p)[field]==step,p.name)
    studies=read(MECH/"clearance.json")
    require(studies["source_hashes"]=={r["name"]:r["sha256"] for r in overlay["add"]},"service versus installed parts")
    paths=list(csv.DictReader((MECH/"QA/service-path.csv").open()))
    require(len(paths)==76 and float(paths[-1]["travel_mm"])==8.25,"service stroke")
    require(all(float(r["installed_W4_mesh_mm"])>0 and float(r["installed_rigid_mesh_mm"])>0 for r in paths),"seated path")
    continuous=read(MECH/"QA/interval-clearance.json")
    require(continuous["overlay_sha256"]==sha(MECH/"overlay.json") and continuous["form_sha256"]==sha(WIRES/"loop-forms.json"),"continuous service evidence")
    require(min(continuous[k]["lower_bound_mm"] for k in ("flex_to_seated_mesh","flex_to_flex"))>0,"continuous clearance")
    native=read(WIRES/"continuous-clearance.json")
    require(native["pass_nominal"] and native["uncertified_count"]==0 and
            native["continuous_external_and_interlead_clearance_test_mm"]>=0.500,"native W4 clearance")
    negative=read(MECH/"QA/installed-negative-control.json")
    require(negative["R0012"]["stations_mm"]["0.5"]["common_mm3"]>0 and
            all(x["common_mm3"]==0 for x in negative["R0013"]["stations_mm"].values()),"old route and corrected route")
    terminal=read(WIRES/"connector-clearance.json")
    require(terminal["pass_nominal"] and terminal["form_sha256"]==sha(WIRES/"loop-forms.json"),"terminal lock passage")
    require(read(WIRES/"clearance.json")["station_count"]==133,"full harness study")
    require(native["fixed_overlay_sha256"]["A5-power"]==sha(A5/"A5-power.brep"),"native certificate versus fitted power board")
    fixed=A5/"installed-leads"
    fit=read(fixed/"fit.json")
    require(fit["installed_manifest_sha256"]==sha(fixed/"installed.json") and not fit["unwanted_contacts"],"fitted USB lead geometry")
    for row in read(fixed/"installed.json")["add"]:
        require(native["fixed_overlay_sha256"][row["name"]]==row["sha256"],"W4 versus fitted "+row["name"])
    usb=read(A5/"verification.json")
    require(usb["board_sha256"]==sha(A5/"usb-input.kicad_pcb") and usb["archive_sha256"]==sha(A5/"decks-and-logs.zip"),"fitted USB circuit")
    require(usb["statuses"]["OPEN_FAIL"]==2 and sum(usb["statuses"].values())==usb["measurements"],"fitted USB case dispositions")
    for folder in (A3,A5,ELEC/"pcb-r0004"):
        drc=read(HERE/"a4-drc.json" if folder.name=="pcb-r0004" else folder/"drc.json")
        require(not any(drc.get(k) for k in ("violations","unconnected_items","schematic_parity")),"DRC "+folder.name)
        erc=read(HERE/"a4-erc.json" if folder.name=="pcb-r0004" else folder/"erc.json")
        require(all(not sheet["violations"] for sheet in erc["sheets"]),"ERC "+folder.name)
    replay=read(HERE/"replay.json")
    require(replay["copper_report_sha256"]==sha(HERE/"copper.json"),"routed circuit replay")
    require(replay["routing_sha256"]==sha(WIRES/"routing.json"),"SPICE lead length")
    for board, path in {"A3": A3/"A3-CIE-R0002.kicad_pcb","A4":ELEC/"pcb-r0004/harness.kicad_pcb","A5":A5/"usb-input.kicad_pcb"}.items():
        require(replay["board_sha256"][board]==sha(path),board+" routed board")
    require(replay["archive_sha256"]==sha(HERE/"postlayout-logs.zip"),"circuit archive")
    with ZipFile(HERE/"postlayout-logs.zip") as archive:
        require(archive.testzip() is None,"damaged solver logs")
    carrier=read(MECH/"QA/r20-carrier-fit.json")
    require(carrier["overlay_sha256"]==sha(MECH/"overlay.json"),"first-article configuration")
    require(all(c["unresolved_solids"]==0 and c["common_volume_mm3"]<=1e-5 for c in carrier["tests"].values()),"first-article carrier fit")
    print("Cross-checked CAD, through-stroke fit, R20 carrier, native boards, wire lengths and routed circuit replay.")

if __name__=="__main__":
    verify()
