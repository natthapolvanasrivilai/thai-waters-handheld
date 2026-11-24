# Read a circuit trace

**R0004 RGB status.** Carrier routing, three current-limit paths, off-state charging indication and bench verification remain open. [Current electrical and optical interface](../../hardware/mechanical/enclosure-print-r0004/README.md#optical-and-electrical-interface)

**R0003 electrical baseline.** Both custom layouts passed the current ERC and routing checks. Two 330 mA batteryless starts failed the 3.9 V acceptance threshold. The proposed Waveshare V2 rework and populated measurements are open. [Current circuit results and hardware review](../../hardware/mechanical/enclosure-fit-r0003/README.md#review-of-the-hardware)

R0016 keeps the R0006 electronics. The five USB lamp simulation cases reproduced their registered measurements. The soldered display and lamp still require a workable assembly sequence and bench validation. [Lamp fit and wiring limits](../../hardware/mechanical/TW-A-0001-R0016/README.md) · [Hardware issue #99](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/99)


[Handbook contents](Home.md) · [Repository home](../../README.md) · [Download the live handbook](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/case-board-r0002-guide-2/Thai-Waters-handbook.html)

## R0013 fitted electronics

[Rerouted A3, USB entry topology and circuit checks](../../quality/seated-connector-review.md)

## Routed-board verification

[Read the A3, A4 and A5 layout checks and 268 circuit cases](../../hardware/verification/r0012/README.md). The daughterboards implement the haptic, audio, key, bus and part of the USB input circuits. The untouched supplier controller still bypasses the current limiter. The complete controller integration and first powered article remain open.

## R0004 controller baseline

**Engineering hold.** R0004 is a proposed revision, not an installed or released controller. The reference route is a revision-controlled supplier spin of the A1 USB/power controller PCB. Consider an interposer only if the identified incoming board allows interception of raw USB power, both USB data lines and hardware load controls, with verified isolation, service access and fit. A cable harness, audio bench coupon or status-light PCB does not implement those functions. The controller schematic and layout are not released for fabrication.

### Evidence reproduced

An independent offline replay of all **85 candidate and control cases** with ngspice 44.2 reproduced all **170** numerical results at the logged precision of the archived ngspice-33 run: **140 within limits, 25 characterization only and five intentionally out of range**. The latter are three unsupported no-cell loads below the 3.9 V input floor, a superseded USB-plus-lamp case above 500 mA, and a superseded data-termination case above 20 ns. The expected failures remain in the regression suite. The separate historical decks were checked against their recorded hashes, not re-simulated in that independent pass. Simulated recovery and charge/load behavior do not demonstrate boot, flashing, safe charging or thermal protection on an actual device.

- [Circuit design, measured quantities and canonical replay command](../../hardware/electronics/integration-r0004/README.md)
- [Candidate deck generator](../../hardware/electronics/integration-r0004/corners.py), [exact-archive replay tool](../../hardware/electronics/integration-r0004/verify.py), and [archived engine, deck and evidence hashes](../../hardware/electronics/integration-r0004/verification.json)
- [All numerical results](../../hardware/electronics/integration-r0004/results.csv), [solver decks and logs](../../hardware/electronics/integration-r0004/solver-evidence.zip), and [historical exceptions](../../hardware/electronics/integration-r0004/exceptions.csv)

### Remaining electrical gates

First identify the received A1 and battery lot, reconcile their revision and populated parts, and record the unpowered connector/polarity and continuity checks in the [controller implementation gate](../../hardware/electronics/integration-r0004/implementation-gate.md). Then finish the editable schematic, PCB layout and electrical-rule/design-rule checks for that exact design. Close all eleven [first-article gates](../../hardware/electronics/integration-r0004/first-article.csv) on an identified article, including both USB orientations and grants, rail stability, protected power-off charging and actual cell-temperature sensing, and no-cell recovery. No simulation or this page authorizes powering a prototype, building boards, or substituting a battery.

## Historical circuit baseline

[R0003 indicators and electrical design](../../hardware/electronics/usb-status-r0003/README.md) · [Installed connections and unpowered checks](../../hardware/electronics/harness-r0003/README.md)

Open **Circuits**, select a case and inspect its trace, limit and disposition. Start with the derated 3.3 V rail transient and the long I²C rise. Compare nominal and stressed conditions, then use the bench matrix to choose probe points on an actual sample.

| Interface | Recorded model result | Next measurement |
|---|---|---|
| 3.3 V rail | 2.836 V at the derated load step | Capture startup and combined Wi-Fi, backlight, audio and rumble demand. |
| Shared I²C | 424 ns rise for 5 kΩ and 100 pF | Check effective pull-ups and capacitance for each assembled variant. |
| Speaker | 1.408 W in the overdrive corner | Measure differential RMS at the real speaker, then constrain gain. |
| Cell charging | Firmware commands 4.20 V and 300 mA after boot | Verify autonomous behavior before firmware starts and cell-temperature protection. |

The primary suite contains 42 ngspice cases and 55 metrics. Eleven metrics exceed their bounds and eleven are characterization only. The [circuit report](../../hardware/verification/circuits/README.md), [raw solver output](../../hardware/verification/circuits/raw-ngspice.zip), [decks](../../hardware/verification/circuits/decks), [results](../../hardware/verification/circuits/results.csv) and [bench matrix](../../hardware/verification/circuits/bench-matrix.csv) preserve the evidence. The separate [brake driver study](../../hardware/mechanical/experiments/reel-brake) has its own assumptions and tests. No Altium installation is required to inspect the results.

[← Inspect the assembly and battery pocket](Hardware-and-3D.md) · [Firmware, simulator and software verification →](Software-and-tests.md)
