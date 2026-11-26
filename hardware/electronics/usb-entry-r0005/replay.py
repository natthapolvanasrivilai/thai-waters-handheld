"""Exercise the V2 entry assembly and keep each ngspice deck with its solver log."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from itertools import product
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

HERE = Path(__file__).resolve().parent
ABORT = re.compile(
    r"^\s*(?:fatal|error)\b|simulation\(s\) aborted|failed!|timestep too small",
    re.I | re.M,
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def circuit(
    copper,
    *,
    source="5.25",
    cable=0.25,
    high="0",
    low="0",
    fixture="Rload pmic 0 15",
    corner="current",
    lamp_short=False,
    bridge=False,
    added_cap="0.01p",
    raw_control=0.00075,
    lamp_r=3564,
    current_limit=None,
    delay_us=None,
    cable_inductance=None,
):
    # Sum each entire net for the drop screen. Minimize series R in the high-current screen.
    lossy = corner == "drop"

    def route(*nets):
        return sum(copper[n]["upper_ohm"] for n in nets) if lossy else 0.0001

    wire = (
        0.075 if lossy else 0.0001
    )  # per-branch design allowance pending dressed lengths
    ilim = current_limit or (0.2621 if lossy else 0.3423)
    threshold = 0.16 if lossy else 0.075
    # 2 us is a published typical dynamic response, 10 us is an unqualified sensitivity.
    # Bypass the steady clamp briefly after a load edge only in these explicit stress fixtures.
    max_i = (
        str(ilim)
        if delay_us is None
        else f"(time >= 100u && time <= {100+delay_us}u ? 50 : {ilim})"
    )
    lamp = "Rled lamp 0 .01" if lamp_short else "Bled lamp 0 I=max(0,(v(lamp)-2.15)/10)"
    line = (
        f"Rcable host lead {cable}\nLcable lead j5 {cable_inductance}"
        if cable_inductance
        else f"Rcable host j5 {cable}"
    )
    return f"""Vhost host 0 {source}
{line}
RwireIN j5 entry {wire+route('ENTRY')}
Centry entry 0 70p
Rbead entry raw {(0.05 if lossy else .0001)+route('RAW')}
Craw raw 0 .11u
Cfixture raw 0 {added_cap}
Bcontrols raw 0 I={raw_control}*min(1,max(0,v(raw)/2))
Rlamp raw lamp {lamp_r}
{lamp}
Vw4 lo 0 {low}
Vw5 hi 0 {high}
R5 lo 0 100k
R4 hi 0 100k
Sdriver gate 0 lo 0 NDRV
.model NDRV SW(RON=1 ROFF=1e12 VT=1 VH=.05)
R3 mid gate 100k
Cgate gate 0 50p
Cgs mid gate 1n
Cgd1 raw gate 100p
Cgd2 lowout gate 100p
Mweak1 raw gate mid mid PCHAN W=1u L=1u
Mweak2 lowout gate mid mid PCHAN W=1u L=1u
.model PCHAN PMOS(LEVEL=1 VTO=-1.2 KP=10 RD=.025 RS=.025 IS=1e-18)
Dbody1 raw mid PDIODE
Dbody2 lowout mid PDIODE
.model PDIODE D(IS=1n N=1.4 RS=.04)
Rweak lowout pout {(56.56 if lossy else 55.44)+route('MID_S','LOW_OUT')}
Bhigh raw pout I=min(1,max(0,v(hi)/3.3))*min({max_i},max(0,v(raw,pout)/{threshold}))
Roff raw pout 100meg
Clocal pout 0 1.1u
Rout pout pmic {2*wire+route('PMIC','GND')}
C20 pmic 0 12u
C24 pmic 0 12u
{fixture}
Rfactory j5 pmic {'.05' if bridge else '1e12'}
Bport port 0 V=-i(Vhost)
Bheat heat 0 V=v(lowout,pout)*v(lowout,pout)/{56.56 if lossy else 55.44}
"""


def limit(tag, expr, unit, lo=None, hi=None, expected="PASS"):
    return (tag, expr, unit, lo, hi, expected if lo is not None else "RECORD")


def cases(copper):
    for corner, (label, lo, hi, budget), short in product(
        ("current", "drop"),
        (
            ("suspend", 0, 0, 0.0025),
            ("default_grant", 3.3, 0, 0.100),
            ("configured", 0, 3.3, 0.500),
            ("overlap_configured", 3.3, 3.3, 0.500),
        ),
        (False, True),
    ):
        net = circuit(
            copper,
            source="4.75" if corner == "drop" else "5.25",
            cable=0.65 if corner == "drop" else 0.25,
            low=lo,
            high=hi,
            fixture="Rload pmic 0 .01",
            corner=corner,
            lamp_short=short,
        )
        yield f"{label}_{corner}_{'shortlamp' if short else 'lamp'}", net, ".tran 1u 30u", [
            limit("port", "MAX v(port)", "A", 0, budget),
            limit("resistor_heat", "MAX v(heat)", "W", 0, 1),
        ]
    # Drop-test a supported 200 mA target, and a healthy-pack DPM surrogate subject
    # to workload shedding. Supply deficit is characterized in USB-equivalent A.
    yield "no_cell_200mA_configured", circuit(
        copper,
        source="4.75",
        cable=0.65,
        corner="drop",
        high=3.3,
        fixture="Iqualified pmic 0 .200\n.nodeset v(pmic)=4.4 v(pout)=4.5 v(raw)=4.6 v(mid)=4.6 v(gate)=4.6",
    ), ".tran 1u 30u", [
        limit("input", "MIN v(pmic)", "V", 3.9, 5.5),
        limit("port", "MAX v(port)", "A", 0, 0.500),
    ]
    for label, source, cable, low, high, peak in (
        ("default", 5, 0.25, 3.3, 0, 0.33),
        ("configured", 5, 0.25, 0, 3.3, 0.5),
        ("lossy", 4.75, 0.65, 0, 3.3, 0.65),
    ):
        fixture = f"""Vreq req 0 PULSE(.100 {peak} 1m 5u 5u 1m 10m)\n.nodeset v(pmic)=4.24 v(pout)=4.26 v(raw)=4.7 v(mid)=4.7
Bpmic pmic 0 I=min(v(req),max(0,10*(v(pmic)-4.2292)))
Bdeficit deficit 0 V=max(0,v(req)-min(v(req),max(0,10*(v(pmic)-4.2292))))"""
        yield "pack_DPM_" + label, circuit(
            copper,
            source=source,
            cable=cable,
            corner="drop",
            low=low,
            high=high,
            fixture=fixture,
        ), ".tran .5u 3m 0 .5u", [
            limit("port", "MAX v(port)", "A", 0, 0.1 if low else 0.5),
            limit("input", "MIN v(pmic)", "V", 3.9, 5.5),
            limit("missing", "MAX v(deficit)", "A"),
        ]
    yield "short_minimum_source_resistance", circuit(
        copper, cable=0.0001, low=3.3, lamp_short=True, fixture="Rload pmic 0 .0001"
    ), ".tran 1u 30u", [
        limit("port", "MAX v(port)", "A", 0, 0.1),
        limit("heat", "MAX v(heat)", "W", 0, 1),
    ]
    yield "damaged_raw_wire_prelimit_short", circuit(
        copper, fixture="Rload pmic 0 15\nRdamaged j5 0 .1"
    ), ".tran 1u 30u", [limit("port", "MAX v(port)", "A", 0, 0.1, "CONTROL_FAIL")]
    # Same 15 ohm legacy fixture and exact untouched control.
    yield "R0012_factory_bypass", "Vusb j5 0 5.25\nRfactory j5 pmic .05\nRload pmic 0 15\nBport port 0 V=-i(Vusb)", ".tran 1u 10u", [
        limit("port", "MAX v(port)", "A", 0, 0.100, "CONTROL_FAIL")
    ]
    for fault in (False, True):
        yield "same_15ohm_" + ("LRC4_refitted" if fault else "LRC4_DNP"), circuit(
            copper, low=3.3, bridge=fault
        ), ".tran 1u 30u", [
            limit(
                "port",
                "MAX v(port)",
                "A",
                0,
                0.100,
                "CONTROL_FAIL" if fault else "PASS",
            )
        ]
    # No-cell baseline load is 330 mA at the 3.9 V rail floor (11.818 ohm).
    for label, low, high in (("default", 3.3, 0), ("configured", 0, 3.3)):
        yield "no_cell_330mA_" + label, circuit(
            copper,
            source="4.75",
            cable=0.65,
            corner="drop",
            low=low,
            high=high,
            fixture=f"Rload pmic 0 {3.9/.33}",
        ), ".tran 1u 30u", [
            limit("port", "MAX v(port)", "A", 0, 0.1 if low else 0.5),
            limit("input", "MIN v(pmic)", "V", 3.9, 5.5, "OPEN_FAIL"),
        ]
    yield "old_2k7_lamp_short_suspend", circuit(
        copper, lamp_short=True, lamp_r=2673
    ), ".tran 1u 30u", [limit("port", "MAX v(port)", "A", 0, 0.0025, "CONTROL_FAIL")]
    yield "false_high_suspend", circuit(copper, high=3.3), ".tran 1u 30u", [
        limit("port", "MAX v(port)", "A", 0, 0.0025, "CONTROL_FAIL")
    ]
    # Max caps are 110 nF input ceramic and 70 pF TVS. Model an extra 2.2 uF
    # controller allowance, then deliberately bridge the two OEM 10 uF positions.
    for capname, cap, bridged in (
        ("board_only", "1p", False),
        ("control_allowance", "2.2u", False),
        ("LRC4_refitted", "2.2u", True),
    ):
        for rise in (1, 100):
            attach = f"PWL(0 0 10u 0 {10+rise}u 5.25 500u 5.25)"
            net = circuit(
                copper,
                source=attach,
                cable=0.25,
                added_cap=cap,
                bridge=bridged,
                fixture="Rload pmic 0 10meg",
            )
            yield f"attach_{capname}_{rise}us", net, ".tran .05u 250u 0 .05u", [
                limit("peak", "MAX v(port)", "A"),
                limit(
                    "charge",
                    "INTEG v(port) FROM=10u TO=240u",
                    "C",
                    0,
                    50e-6,
                    "CONTROL_FAIL" if bridged else "PASS",
                ),
            ]
    # Force grants at the A5 pins, allowing 100 us of overlap and 100 us ramp-down.
    net = circuit(
        copper,
        low="PWL(0 0 100u 0 101u 3.3 900u 3.3 901u 0)",
        high="PWL(0 0 800u 0 900u 3.3 2m 3.3 2.1m 0)",
        fixture="Rload pmic 0 .1",
    )
    yield "default_to_grant_to_suspend", net, ".tran .2u 3m 0 .2u", [
        limit("default", "MAX v(port) FROM=300u TO=790u", "A", 0, 0.100),
        limit("grant", "MAX v(port) FROM=800u TO=2m", "A", 0, 0.500),
        limit("suspend", "MAX v(port) FROM=2.5m TO=3m", "A", 0, 0.0025),
    ]
    for hold in (2, 10):
        net = circuit(
            copper,
            high=3.3,
            delay_us=hold,
            cable_inductance="0.3u",
            fixture="Vload en 0 PWL(0 0 100u 0 100.02u 3.3)\nRidle pmic 0 1000\nSload pmic 0 en 0 SWLOAD\n.model SWLOAD SW(RON=.1 ROFF=1e12 VT=1.5 VH=.05)",
        )
        yield f"configured_abrupt_fault_{hold}us", net, ".tran .01u 350u 0 .02u", [
            limit("peak", "MAX v(port) FROM=99u TO=125u", "A", 0, 0.5, "OPEN_FAIL"),
            limit("settled", "MAX v(port) FROM=300u TO=350u", "A", 0, 0.5),
        ]
    for granted in (False, True):
        net = circuit(
            copper,
            low=3.3 if granted else 0,
            source="0",
            fixture="Vexternal pmic 0 4.2",
        )
        net += "Bback back 0 V=i(Vhost)\n"
        yield f"reverse_{'stale_weak_grant' if granted else 'inhibited'}", net, ".tran 1u 30u", [
            limit(
                "reverse",
                "MAX v(back)",
                "A",
                0,
                5e-6,
                "CONTROL_FAIL" if granted else "PASS",
            )
        ]
    # Omitted measuring resistor across A5 is a positive coverage control.
    for label, value in (("leaky_flux", 1e6), ("parallel_10ohm", 10)):
        net = (
            circuit(copper, low=3.3, fixture="Rload pmic 0 15")
            + f"Rhidden j5 pmic {value}\n"
        )
        yield label, net, ".tran 1u 30u", [
            limit(
                "port",
                "MAX v(port)",
                "A",
                0,
                0.1,
                "CONTROL_FAIL" if value == 10 else "PASS",
            )
        ]


def run(engine):
    copper = json.loads((HERE / "copper.json").read_text())
    if copper["sha256"] != digest(HERE / "usb-input.kicad_pcb"):
        raise ValueError("Refresh copper extraction for this PCB")
    rows = []
    with tempfile.TemporaryDirectory() as work:
        temp = Path(work)
        with ZipFile(temp / "decks-and-logs.zip", "w", ZIP_DEFLATED) as archive:
            for name, net, analysis, metrics in cases(copper["nets"]):
                deck = temp / (name + ".cir")
                log = temp / (name + ".log")
                deck.write_text(
                    "\n".join(
                        [
                            name,
                            net,
                            analysis,
                            *[f".meas tran {tag} {expr}" for tag, expr, *_ in metrics],
                            ".end",
                            "",
                        ]
                    )
                )
                proc = subprocess.run(
                    [str(engine), "-b", "-o", str(log), str(deck)],
                    capture_output=True,
                    timeout=30,
                )
                output = log.read_text(errors="replace")
                if proc.returncode or ABORT.search(output):
                    raise RuntimeError(name + "\n" + output[-3000:])
                for tag, _, unit, lo, hi, want in metrics:
                    m = re.search(r"^" + tag + r"\s*=\s*([0-9.eE+-]+)", output, re.M)
                    if m is None:
                        raise RuntimeError(name + " " + tag + "\n" + output[-3000:])
                    value = float(m[1])
                    status = (
                        "RECORD"
                        if lo is None
                        else (
                            "PASS"
                            if lo <= value <= hi
                            else want if want.endswith("FAIL") else "FAIL"
                        )
                    )
                    if status != want:
                        raise ValueError((name, tag, value, lo, hi, want, status))
                    rows.append(
                        dict(
                            case=name,
                            measurement=tag,
                            value=value,
                            unit=unit,
                            low=lo,
                            high=hi,
                            status=status,
                        )
                    )
                for path in (deck, log):
                    archive.write(path, path.name)
        (HERE / "decks-and-logs.zip").write_bytes(
            (temp / "decks-and-logs.zip").read_bytes()
        )
    with (HERE / "measurements.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    unique = {r["case"] for r in rows}
    report = dict(
        engine_sha256=digest(engine),
        board_sha256=copper["sha256"],
        circuit_cases=len(unique),
        measurements=len(rows),
        statuses={
            s: sum(r["status"] == s for r in rows)
            for s in ("PASS", "RECORD", "CONTROL_FAIL", "OPEN_FAIL")
        },
        archive_sha256=digest(HERE / "decks-and-logs.zip"),
    )
    (HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    run(parser.parse_args().engine.resolve())
