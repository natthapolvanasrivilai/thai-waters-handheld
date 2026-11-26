"""Reproduce the original studies, then stress the routed power, audio and bus networks."""
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parents[1] / "electronics/integration-r0004"
sys.path.insert(0, str(ORIGINAL))
import verify as baseline
from corners import circuits

SOLVER_FAILURE = re.compile(r"^\s*(?:fatal|error)\b|simulation\(s\) aborted|failed!|timestep too small",re.I|re.M)

def postlayout(bounds, routing):
    a3 = {k:r["upper_ohm"] for k,r in bounds["A3"]["nets"].items()}
    a4 = {k:r["upper_ohm"] for k,r in bounds["A4"]["nets"].items()}
    a5 = {k:r["upper_ohm"] for k,r in bounds["A5"]["nets"].items()}
    audio = sum(a4[k] for k in ("AMP_P", "AMP_N", "SPK_P", "SPK_N"))
    for name, net, analysis, measures in circuits():
        if name.startswith("audio_"):
            net = net.replace("Rpos a p ", f"Rloop a a_pad {audio}\nRpos a_pad p ")
            net = net.replace("V(a,p)", "V(a_pad,p)")
        elif name.startswith("i2c_"):
            # Aged mated pair + crimp: SPCI172 sections 7.2/7.5. Four extra
            # mm allow for stripped ends. 0.129 mm² is nominal 26 AWG copper.
            def branch_ohms(signal):
                length = routing[signal]["full_jacket_length_mm"] + 4
                return 0.025 + length * 1.724e-5 * (1 + .00393*50) / .129
            bus = a4["VCC3V3"] + max(a4[n] + a3["/"+n] + branch_ohms(n) for n in ("SCL","SDA"))
            net = net.replace("Rp src line ", "Rp src joined ").replace("Ra2 src line ", "Ra2 src joined ")
            net += f"\nRroute joined line {bus}"
        elif name in ("usb_default_short", "usb_overlap_short"):
            # Minimal resistance gives maximum fault current. Also check resistor heat.
            net = net.replace("Rweak raw 0 55.44", "Rweak raw 0 55.44\nBloss w 0 V=V(raw)*V(raw)/55.44")
            measures = [*measures, ("heat", "max v(w)", "W", 0, 1)]
        elif name.startswith(("usb_unconfigured_", "usb_play_", "usb_lossy_", "usb_adapter_")):
            net = net.replace("Rweak raw pmic 55.44",
                              f"Rweak raw pout {55.44+a5['MID_S']+a5['LOW_OUT']}")
            net = net.replace("Bsw raw pmic", "Bsw raw pout").replace("V(raw,pmic)", "V(raw,pout)")
            net += f"\nRcopper pout pmic {a5['RAW']+a5['PMIC']+a5['GND']}\nCinput raw 0 .1u\nCoutlocal pout 0 1u"
        else:
            continue
        yield name, net, analysis, measures
    # The stock unbroken A1 VBUS trace would bypass this board; this must fail.
    yield "control_A1_uninterrupted_VBUS", (
        "Vusb raw 0 5.25\nRfactory raw pmic .05\nRload pmic 0 15\nBobs obs 0 V=-I(Vusb)"
    ), ".tran 1u 10u", [("port", "max v(obs)", "A", 0, .100)]
    # A3 R1/R2 are DNP. Populating the old resistor on either signal
    # alongside the fitted 1.5k and accessory 10k increases sink current.
    yield "control_A3_unremoved_pullup", (
        "Vrail src 0 3.6\nRa4 src line 1485\nRa2 src line 9500\nRa3 src line 2178\nVsink line 0 0.4"
    ), ".tran 1u 10u", [("sink","max i(Vsink)","A",0,.003)]


def execute(engine, *, output=HERE, routing_file=None, a3_board="pcb-haptic-cie-r0001/A3-CIE-R0001.kicad_pcb",
            a5_board="pcb-power-r0004/usb-input.kicad_pcb", reference_usb_copper=None):
    copper_file = output / "copper.json"
    copper_bytes = copper_file.read_bytes()
    bounds = json.loads(copper_bytes)
    if routing_file is None:
        routing_file = ORIGINAL.parent / "harness-r0005" / "routing.json"
    routing_bytes = routing_file.read_bytes()
    routing = json.loads(routing_bytes)
    names = {"A3": a3_board,
             "A4": "pcb-r0004/harness.kicad_pcb", "A5": a5_board}
    for key,name in names.items():
        assert baseline.digest(ORIGINAL.parent / name) == bounds[key]["sha256"], key
    with tempfile.TemporaryDirectory() as temp:
        scratch = Path(temp)
        baseline.HERE = scratch
        sys.argv = [str(baseline.__file__), "--engine", str(engine)]
        baseline.main()
        old = json.loads((scratch/"verification.json").read_text())
        assert list(csv.DictReader((scratch/"results.csv").open())) == list(csv.DictReader((ORIGINAL/"results.csv").open()))
        rows = []
        with zipfile.ZipFile(scratch/"postlayout-logs.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            simulation_bounds=dict(bounds)
            if reference_usb_copper is not None:
                # These legacy tests specifically exercise the old dual-path circuit.
                # A replacement topology is tested from its own schematic and deck.
                simulation_bounds["A5"]=json.loads(reference_usb_copper.read_bytes())["A5"]
            for name, net, tran, specs in postlayout(simulation_bounds, routing):
                deck = scratch / (name + ".cir")
                log = scratch / (name + ".log")
                deck.write_text("\n".join([name,net,tran,*[".meas tran " + t + " " + cmd for t,cmd,*_ in specs],".end",""]))
                subprocess.run([engine,"-b","-o",log,deck],capture_output=True,check=True,timeout=30)
                txt = log.read_text(errors="replace")
                if SOLVER_FAILURE.search(txt):
                    raise ValueError(name)
                for tag,_,unit,low,high in specs:
                    value = float(re.search(r"^"+tag+r"\s*=\s*([0-9Ee+.-]+)",txt,re.M)[1])
                    status = "RECORD" if low is None else "WITHIN" if low <= value <= high else "OUTSIDE"
                    rows.append(dict(case=name,measurement=tag,value=value,unit=unit,low=low,high=high,status=status))
                archive.write(deck,deck.name)
                archive.write(log,log.name)
        faults = [(r["case"],r["measurement"]) for r in rows if r["status"]=="OUTSIDE"]
        if faults != [("control_A1_uninterrupted_VBUS","port"), ("control_A3_unremoved_pullup","sink")]:
            raise ValueError(faults)
        with (scratch/"measurements.csv").open("w", newline="") as dest:
            writer = csv.DictWriter(dest,rows[0].keys());writer.writeheader();writer.writerows(rows)
        if routing_file.read_bytes() != routing_bytes or copper_file.read_bytes() != copper_bytes:
            raise RuntimeError("Routing or extracted copper changed during replay")
        for key,name in names.items():
            if baseline.digest(ORIGINAL.parent / name) != bounds[key]["sha256"]:
                raise RuntimeError(f"{key} layout changed during replay")
        report = dict(engine_sha256=baseline.digest(engine), routing_sha256=hashlib.sha256(routing_bytes).hexdigest(),
            copper_report_sha256=hashlib.sha256(copper_bytes).hexdigest(),
            board_sha256={name:data["sha256"] for name,data in bounds.items()},
            historical_cases=sum(s["cases"] for s in old["historical"].values()),
            original_candidate_cases=old["candidate_cases"], original_metrics_reproduced=old["candidate_metrics"],
            new_postlayout_cases=len({r["case"] for r in rows}), postlayout_measurements=len(rows),
            status={s:sum(r["status"]==s for r in rows) for s in ("WITHIN","RECORD","OUTSIDE")},
            outside=faults,archive_sha256=baseline.digest(scratch/"postlayout-logs.zip"))
        if reference_usb_copper is not None:
            report["legacy_USB_copper_sha256"]=baseline.digest(reference_usb_copper)
            report["legacy_USB_board_sha256"]=simulation_bounds["A5"]["sha256"]
            report["scope"]="A3/A4 bus and audio used current routed copper. Legacy USB cases replay their original dual-path network. The fitted prototype USB entry has a separate schematic-specific simulation report."
        (scratch/"replay.json").write_text(json.dumps(report,indent=2)+"\n")
        for name in ("postlayout-logs.zip","measurements.csv","replay.json"):
            shutil.copyfile(scratch/name,output/name)
        print(json.dumps(report))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine",type=Path,required=True)
    execute(parser.parse_args().engine.resolve())
