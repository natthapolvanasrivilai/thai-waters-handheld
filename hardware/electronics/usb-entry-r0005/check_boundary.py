"""Read the manufacturer PDF's embedded netlist and check the assembly boundary."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pymupdf

HERE = Path(__file__).resolve().parent
V2_SHA = "a0b65d8be900a4017d056d5b9ef8626bd138cb8be8d5814f40fb7ad34d4f321b"
STEP_SHA = "d774a7edf75b5fc4b699b55c2f60837b46ce24a0da6edce2aa11f6f508266666"
SUPPLIER = "https://raw.githubusercontent.com/waveshareteam/ESP32-S3-Touch-LCD-3.5B/main/hardware/schematic/ESP32-S3-Touch-LCD-3.5B-V2-Schematic.pdf"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def supplier_nets(path):
    if digest(path) != V2_SHA:
        raise ValueError("Unrecognized A1 schematic")
    nets = {}
    with pymupdf.open(path) as doc:
        for level, value, _ in doc.get_toc():
            if level == 4:
                net = value
            if level == 5:
                group = value
            if level == 6 and group == "Pins":
                nets.setdefault(net, []).append(value)
    return nets


def run(pdf):
    nets = supplier_nets(pdf)
    assert sorted(nets["VBUS'"]) == ["J5-A4/B9", "J5-A9/B4", "LRC4-1"]
    assert sorted(nets["VBUS"]) == [
        "C20-2",
        "C24-1",
        "D3-1",
        "J8-1",
        "LRC4-2",
        "UP1-37",
    ]
    assert "J8-3" in nets["GND"]
    wires = list(csv.DictReader((HERE / "assembly.csv").open()))
    device = ET.parse(HERE / "connectivity.xml")
    pcb_nets = {
        n.attrib["name"]: {p.attrib["ref"] + "-" + p.attrib["pin"] for p in n}
        for n in device.findall("./nets/net")
    }
    for row in wires:
        if row["A5"]:
            assert row["A5"] + "-1" in pcb_nets[row["A5_net"]]
        if row["A1_net"]:
            assert row["A1_pin"] in nets[row["A1_net"]]
    active = {r["A5"]: r["A1_pin"] for r in wires if r["A1_net"]}
    assert active == {"W1": "LRC4-1", "W2": "J8-1", "W3": "J8-3"}
    assert pcb_nets["ENTRY"] == {"D1-1", "FB1-1", "W1-1"}
    assert pcb_nets["RAW"] == {"FB1-2", "C1-1", "Q1-3", "U1-1", "W7-1"}
    assert pcb_nets["PMIC"] == {"W2-1", "U1-6", "R2-2", "C2-2"}
    legacy = json.loads((HERE.parent / "pcb-power-r0004/design.json").read_text())
    candidate = json.loads((HERE / "design.json").read_text())
    placed = {r[0]: r[2:6] for r in candidate["parts"]}
    assert all(placed[r[0]] == r[2:6] for r in legacy["parts"])
    assert (candidate["size_mm"], candidate["thickness_mm"]) == (
        legacy["size_mm"],
        legacy["thickness_mm"],
    )
    step = HERE.parents[1] / "mechanical/rev-E/scripts/inputs/Waveshare.stp"
    assert digest(step) == STEP_SHA
    labels = step.read_bytes().upper()
    return {
        "vendor_pdf": SUPPLIER,
        "vendor_pdf_sha256": V2_SHA,
        "vendor_STEP_sha256": STEP_SHA,
        "vendor_STEP_contains_LRC4": b"LRC4" in labels,
        "vendor_STEP_contains_bead_MPN": b"BTREF1608A3R121" in labels,
        "vendor_net_pins": {
            n: nets[n]
            for n in ("VBUS'", "VBUS", "USB_N", "USB_P", "CC1", "CC2")
            if n in nets
        },
        "fixed_legacy_footprints": len(legacy["parts"]),
        "A5_pcb_sha256": digest(HERE / "usb-input.kicad_pcb"),
        "installed_brep_sha256": digest(HERE / "A5-power.brep"),
        "installed_lands": active,
        "matched_lot_and_access": "unverified",
    }


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument("pdf", type=Path)
    print(json.dumps(run(arg.parse_args().pdf), indent=2))
