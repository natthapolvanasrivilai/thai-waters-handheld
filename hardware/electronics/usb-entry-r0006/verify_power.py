"""Replay the passive R0006 power bound and the two hardware CC qualification channels."""

import argparse
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "usb-entry-r0005"))
import replay as engine

metric = engine.limit


def network(
    copper,
    *,
    src=5.25,
    cc1=0.61,
    cc2=0,
    drop=False,
    offset=0,
    ref=1.242,
    lamp_short=False,
    load="Rload pmic 0 15",
    cable=0.25,
    stray="100p",
    shorted_ballast=False,
    bridge=False,
    stale=False,
    wire1=0.0001,
):
    def route(*nets):
        return sum(copper[n]["upper_ohm"] for n in nets) if drop else 0.0001

    wire = 0.075 if drop else 0.0001
    rlim = 0.01 if shorted_ballast else (62.62 if drop else 61.38)
    # Both comparator channels are voltage-sensed. Apply the complete end-to-end
    # offset / hysteresis / CMRR guard at each threshold in the sweep.
    upper = 100000 * (1.0035 if offset < 0 else 0.9965)
    lower = 110000 * (0.9965 if offset < 0 else 1.0035)
    return f"""Vhost host 0 {src}
Rcable host j5 {cable}
Cstray j5 0 {stray}
Rfeed j5 entry {wire+route('ENTRY')}
Rbead entry raw {(0.05 if drop else .0001)+route('RAW')}
R2 raw ballast {rlim+route('BALLAST')}
R9 raw ctrl {3333 if drop else 3267}
C1 ctrl 0 110n
C3 ctrl 0 110n
Bctrl ctrl 0 I=18u*max(0,min(1,v(ctrl)/1.65))
Rlamp ctrl anode 3564
Bled anode 0 I=max(0,(v(anode)-{0 if lamp_short else 2.15})/{.02 if lamp_short else 10})
Ctv ballast 0 70p
Rtvsleak ballast 0 550k
Vcc1 vcc1 0 {cc1}
Vcc2 vcc2 0 {cc2}
R26 vcc1 0 5049
R24 vcc2 0 5049
Rtap1 vcc1 cc1 {wire1}
Rtap2 vcc2 cc2 .075
R7 cc1 sense1 100k
R8 cc2 sense2 100k
R5 sense1 0 10meg
R6 sense2 0 10meg
C4 sense1 0 10n
C5 sense2 0 10n
Breference vref 0 V=min({ref},max(0,v(ctrl)-.1))
R1 vref vth {upper}
R4 vth 0 {lower}
* The reference output and quiescent burden are drawn from the control rail.
Bdivider ctrl 0 I=v(vref)/({upper}+{lower})
Bcmp1 drive1 0 V=v(sense1)-v(vth)-({offset})-100*max(0,1.65-v(ctrl))
Bcmp2 drive2 0 V=v(sense2)-v(vth)-({offset})-100*max(0,1.65-v(ctrl))
Sout1 grant 0 drive1 0 COMP
Sout2 grant 0 drive2 0 COMP
.model COMP SW(RON=40 ROFF=1e12 VT=0 VH=.001)
Rstale grant 0 {1 if stale else '1e9'}
Coutcomp grant 0 10p
Mn gate ctrl grant grant NDRV W=1u L=1u
.model NDRV NMOS(LEVEL=1 VTO=1.2 KP=2 IS=1e-17)
R3 mid gate 100k
Cgs mid gate 1n
Cgd1 ballast gate 100p
Cgd2 pout gate 100p
Mweak1 ballast gate mid mid PCHAN W=1u L=1u
Mweak2 pout gate mid mid PCHAN W=1u L=1u
.model PCHAN PMOS(LEVEL=1 VTO=-1.2 KP=10 RD=.025 RS=.025 IS=1e-18)
Dbody1 ballast mid DP
Dbody2 pout mid DP
.model DP D(IS=1n N=1.4 RS=.04)
Resr pout cap .025
C2 cap 0 1.1u
Rout pout pmic {2*wire+route('GND','PMIC','MID_S')}
R20esr pmic c20die .04
L20loop c20die c20cap 10n
C20 c20cap 0 12u
R24esr pmic c24die .04
L24loop c24die c24cap 10n
C24 c24cap 0 12u
{load}
Rfactory j5 pmic {'.05' if bridge else '1e12'}
Bport port 0 V=-i(Vhost)
Bcc icc 0 V=-i(Vcc1)-i(Vcc2)
Baggregate total 0 V=v(port)+v(icc)
Bheat heat 0 V=v(raw,ballast)*v(raw,ballast)/{rlim}
Bmain current 0 V=v(raw,ballast)/{rlim+route('BALLAST')}
"""


def cases(copper):
    static = ".tran 1u 25u"
    # Pin voltages include the worst default maximum and medium minimum. Both
    # orientations, both reference extremes, both supply/transport corners.
    for orient, (name, cc), (ref, err), drop in product(
        (1, 2),
        (("open", 0), ("default", 0.61), ("medium", 0.70), ("high", 2.04)),
        ((1.209, -0.021), (1.274, 0.021)),
        (False, True),
    ):
        enabled = name in ("medium", "high")
        values = (cc, 0) if orient == 1 else (0, cc)
        net = network(
            copper,
            src=4.75 if drop else 5.5,
            cable=0.65 if drop else 0.0001,
            cc1=values[0],
            cc2=values[1],
            ref=ref,
            offset=err,
            drop=drop,
            lamp_short=True,
            load="Rload pmic 0 .001",
        )
        yield f"cc{orient}_{name}_{'high' if err>0 else 'low'}_trip_{'drop' if drop else 'max'}", net, static, [
            metric(
                "vbus",
                "MAX v(port)",
                "A",
                0.05 if enabled else 0,
                0.100 if enabled else 0.0025,
            ),
            metric(
                "including_cc", "MAX v(total)", "A", 0, 0.100 if enabled else 0.0025
            ),
            metric("control_supply", "MIN v(ctrl)", "V", 1.65, 5.5),
            metric("heat", "MAX v(heat)", "W", 0, 1),
        ]
    for resistive in (False, True):
        for src, rise in ((4.75, 1), (5.5, 1), (5.5, 100)):
            ramp = f"PWL(0 0 5u 0 {5+rise}u {src})"
            net = network(
                copper,
                src=ramp,
                cc1=1.31,
                cable=0.25,
                stale=resistive,
                load="Rload pmic 0 .001",
                lamp_short=True,
            )
            yield f"attach_{src}_{rise}us_{'force_on' if resistive else 'normal'}", net, ".tran .01u 300u 0 .02u", [
                metric("port_peak", "MAX v(port)", "A", 0, 0.100),
                metric("charge", "INTEG v(port) FROM=5u TO=250u", "C", 0, 50e-6),
            ]
    for short_output in (False, True):
        # Stuck FETs with a zero-ohm conducting path exercise the passive bound
        # independent of thresholds, level-one models, controls or firmware.
        fixture = "Rload pmic 0 " + (".001" if short_output else "10meg")
        net = network(
            copper,
            src="PWL(0 0 5u 0 6u 5.5)",
            cc2=0,
            cable=0.0001,
            load=fixture,
            lamp_short=True,
        )
        net += "Rweld ballast pout .001\nBexcess ex 0 V=max(0,v(port)-.100)\n"
        yield f"cold_attach_welded_{'short' if short_output else 'cap_only'}", net, ".tran .1u 20m 0 .5u", [
            metric("peak", "MAX v(port)", "A", 0, 0.100),
            metric("excess_charge", "INTEG v(ex) FROM=5u TO=20m", "C", 0, 50e-6),
            metric("all_charge", "INTEG v(port) FROM=5u TO=20m", "C"),
        ]
    for label, pins, limit in (
        ("both_default", (0.61, 0.61), 0.0025),
        ("both_advanced", (2.04, 2.04), 0.100),
    ):
        net = network(
            copper,
            src=5.5,
            cc1=pins[0],
            cc2=pins[1],
            lamp_short=True,
            load="Rload pmic 0 .001",
        )
        yield "both_CC_" + label, net, static, [
            metric("source_and_cc", "MAX v(total)", "A", 0, limit)
        ]
    # A synthetic open factory Rd under a forced-live legacy supply exposes the
    # upper-range limitation of two threshold comparators versus a full CC PHY.
    net = network(copper, src=5.25, cc1=5, load="Rload pmic 0 .001").replace(
        "R26 vcc1 0 5049", "R26 vcc1 0 1e12"
    )
    yield "absent_Rd_forced_live_overscale", net, static, [
        metric("ceiling", "MAX v(port)", "A", 0, 0.100),
        metric("suspend", "MAX v(total)", "A", 0, 0.0025, "CONTROL_FAIL"),
    ]
    for i, lead in enumerate(("0.1u", "1u")):
        # 0.1-ohm abrupt load from a previously charged output. All charge from
        # the upstream port follows R2/R9; downstream capacitor discharge is local.
        fixture = "Vshort cmd 0 PWL(0 0 100u 0 100.02u 3.3)\nVsense outload 0 0\nRidle pmic 0 1meg\nSload pmic outload cmd 0 LOAD\n.model LOAD SW(RON=.10 ROFF=1e12 VT=1.6 VH=.05)"
        net = network(
            copper, src=5.5, cc1=2.04, cable=0.25, load=fixture, lamp_short=True
        )
        net = net.replace(
            "Rcable host j5 .25", f"Rcable host lead .25\nLcable lead j5 {lead}"
        ).replace("Rcable host j5 0.25", f"Rcable host lead .25\nLcable lead j5 {lead}")
        yield f"hot_short_{i}", net, ".tran .01u 500u 0 .05u", [
            metric("port_peak", "MAX v(port) FROM=99u TO=500u", "A", 0, 0.100),
            metric("output_cap_discharge", "MAX i(Vsense) FROM=99u TO=500u", "A"),
            metric("settled", "MAX v(port) FROM=450u TO=500u", "A", 0, 0.100),
        ]
    for src, vreg in product((4.75, 5, 5.5), (4.2292, 4.4908)):
        net = network(
            copper,
            src=src,
            cc2=0.70,
            drop=True,
            cable=0.65,
            load=f"Vpmic pmic 0 {vreg}",
        )
        yield f"available_at_{src}V_{vreg}V", net, static, [
            metric("available", "MAX i(Vpmic)", "A", 0.001, 0.030),
            metric("source", "MAX v(port)", "A", 0, 0.100),
        ]
    net = network(
        copper,
        cc1="PWL(0 .61 1m .61 1.01m 2.04 12m 2.04 12.01m .61)",
        ref=1.209,
        offset=-0.021,
        load="Rload pmic 0 .01",
    )
    yield "advertise_upgrade_then_downgrade", net, ".tran 2u 30m 0 2u", [
        metric("before", "MAX v(port) FROM=0 TO=.9m", "A", 0, 0.0025),
        metric("granted", "MIN v(port) FROM=6m TO=11m", "A", 0.050, 0.100),
        metric("transition_peak", "MAX v(port)", "A", 0, 0.100),
        metric("suspend", "MAX v(total) FROM=25m TO=30m", "A", 0, 0.0025),
    ]
    for fault, bypass in (("corrected", False), ("LRC4_refitted", True)):
        yield "same_15ohm_" + fault, network(copper, cc1=0.70, bridge=bypass), static, [
            metric(
                "port",
                "MAX v(port)",
                "A",
                0,
                0.100,
                "CONTROL_FAIL" if bypass else "PASS",
            )
        ]
    yield "historical_factory", "Vsrc j5 0 5.25\nRf j5 pmic .05\nRload pmic 0 15\nBport port 0 V=-i(Vsrc)", static, [
        metric("port", "MAX v(port)", "A", 0, 0.100, "CONTROL_FAIL")
    ]
    yield "missing_R2_bridge", network(
        copper, cc1=2.04, shorted_ballast=True
    ), static, [metric("port", "MAX v(port)", "A", 0, 0.100, "CONTROL_FAIL")]
    yield "stuck_low_grant_default", network(
        copper, cc1=0.61, stale=True, load="Rload pmic 0 .01"
    ), static, [
        metric("current_ceiling", "MAX v(port)", "A", 0, 0.100),
        metric("suspend", "MAX v(total)", "A", 0, 0.0025, "CONTROL_FAIL"),
    ]
    yield "sense_wire_open", network(
        copper, cc1=0.70, wire1="1e12", load="Rload pmic 0 .01"
    ), static, [metric("port", "MAX v(port)", "A", 0, 0.0025)]
    yield "prelimit_insulation_fault", network(
        copper, cc1=0.61, load="Rload pmic 0 15\nRshort j5 0 .1"
    ), static, [metric("port", "MAX v(port)", "A", 0, 0.100, "CONTROL_FAIL")]
    yield "excess_raw_capacitance", network(
        copper, src="PWL(0 0 5u 0 6u 5.25)", cc1=0.61, stray="20u"
    ), ".tran .01u 200u 0 .05u", [
        metric("charge", "INTEG v(port) FROM=5u TO=200u", "C", 0, 50e-6, "CONTROL_FAIL")
    ]
    yield "fast_edge_stray_sensitivity", network(
        copper, src="PWL(0 0 5u 0 5.001u 5.5)", cc1=0.61, stray="500p"
    ), ".tran .05n 5.02u 4.99u .1n", [
        metric("connector_peak", "MAX v(port)", "A"),
        metric("charge", "INTEG v(port) FROM=5u TO=5.02u", "C", 0, 50e-6),
    ]
    for cc in (0.61, 2.04):
        yield f"unsupported_no_cell_330mA_{cc}", network(
            copper, src=4.75, cc1=cc, drop=True, cable=0.65, load="Rload pmic 0 11.818"
        ), static, [
            metric("port", "MAX v(port)", "A", 0, 0.100),
            metric("input", "MAX v(pmic)", "V", 3.9, 5.5, "OPEN_FAIL"),
        ]
    for stale in (False, True):
        net = (
            network(copper, src=0, cc1=0, stale=stale, load="Vout pmic 0 4.2")
            + "Brev rev 0 V=i(Vhost)\n"
        )
        yield f"reverse_unplug_{stale}", net, static, [
            metric("backfeed", "MAX v(rev)", "A", 0, 5e-6)
        ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    engine.HERE = HERE
    engine.cases = cases
    engine.run(parser.parse_args().engine.resolve())
