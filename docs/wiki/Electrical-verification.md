# Read a circuit trace

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/firmware-v0.9.4/Thai-Waters-handbook.html)

## Current R0004 engineering review

R0004 ran 85 candidate and control cases with 170 numerical results. The report retains historical out-of-range cases, input-current faults and the load behavior when a cell is missing or host power is revoked. The proposed power circuitry and recovery path need a placed PCB, a populated sample and measured verification. [Circuit changes, limits and reproduction](../../hardware/electronics/integration-r0004/README.md) · [All measurement rows](../../hardware/electronics/integration-r0004/results.csv) · [Original exceptions](../../hardware/electronics/integration-r0004/exceptions.csv) · [First-article matrix](../../hardware/electronics/integration-r0004/first-article.csv) · [Private electrical issue](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/4)

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
