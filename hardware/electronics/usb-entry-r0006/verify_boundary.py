"""Cross-check the schematic netlist, vendor PDF pin list and assembly contacts."""

import argparse
import csv
import json
from pathlib import Path
import sys
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "usb-entry-r0005"))
from check_boundary import supplier_nets, digest, V2_SHA, SUPPLIER, STEP_SHA


def verify(pdf):
    nets = supplier_nets(pdf)
    assert set(nets["VBUS'"]) == {"J5-A4/B9", "J5-A9/B4", "LRC4-1"}
    assert set(nets["VBUS"]) == {"C20-2", "C24-1", "D3-1", "J8-1", "LRC4-2", "UP1-37"}
    assert set(nets["CC1"]) == {"R26-2", "J5-A5"} and set(nets["CC2"]) == {
        "R24-2",
        "J5-B5",
    }
    xml = ElementTree.parse(HERE / "connectivity.xml")
    pcb = {
        n.get("name"): {p.get("ref") + "-" + p.get("pin") for p in n}
        for n in xml.findall("./nets/net")
    }
    for row in csv.DictReader((HERE / "assembly.csv").open()):
        assert row["ref"] + "-1" in pcb[row["A5_net"]]
        if row["A1_pin"]:
            assert row["A1_pin"] in nets[row["A1_net"]]
    assert pcb["ENTRY"] == {"W1-1", "FB1-1"}
    assert pcb["RAW"] == {"FB1-2", "R2-1", "R9-1"}
    assert pcb["BALLAST"] == {"R2-2", "Q1-3", "D1-1"}
    assert pcb["MID_S"] == {"R3-1", "Q1-2", "Q2-2"}
    assert pcb["PMIC"] == {"W2-1", "C2-2", "Q2-3"}
    assert pcb["CTRL"] == {"R9-2", "C1-1", "C3-1", "Q3-1", "U1-6", "U2-6", "W7-1"}
    assert pcb["GRANT_N"] == {"U1-1", "U2-1", "Q3-2"}
    assert pcb["THRESH"] == {"R1-2", "R4-1", "U1-3", "U2-3"}
    design = json.loads((HERE / "design.json").read_text())
    old = json.loads((HERE.parent / "pcb-power-r0004/design.json").read_text())
    placed = {r[0]: r[2:6] for r in design["parts"]}
    assert all(placed[r[0]] == r[2:6] for r in old["parts"])
    assert (
        design["size_mm"] == old["size_mm"]
        and design["thickness_mm"] == old["thickness_mm"]
    )
    step = HERE.parents[1] / "mechanical/rev-E/scripts/inputs/Waveshare.stp"
    assert digest(step) == STEP_SHA
    return {
        "vendor_pdf": SUPPLIER,
        "vendor_pdf_sha256": V2_SHA,
        "vendor_STEP_sha256": STEP_SHA,
        "vendor_STEP_names_LRC4": b"LRC4" in step.read_bytes().upper(),
        "vendor_nets": {
            n: nets[n] for n in ("VBUS'", "VBUS", "CC1", "CC2", "USB_N", "USB_P")
        },
        "upstream_branches": sorted(pcb["RAW"]),
        "unchanged_legacy_footprints": len(old["parts"]),
        "A5_board_sha256": digest(HERE / "usb-input.kicad_pcb"),
        "A5_installed_brep_sha256": digest(HERE / "A5-power.brep"),
        "A5_STEP_sha256": digest(HERE / "usb-input.step"),
        "max_intentional_current_A_at_5V5": 5.5 / (62 * 0.99) + 5.5 / (3300 * 0.99),
        "worst_ideal_ballast_heat_W_at_5V5": 5.5**2 / (62 * 0.99),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pdf", type=Path)
    print(json.dumps(verify(p.parse_args().pdf), indent=2))
