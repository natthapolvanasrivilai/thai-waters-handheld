# R0012 electrical review

The R0012 fit candidate combines a revised haptic board, an audio/key/bus interposer and a USB power daughterboard. These form only part of the proposed R0004 controller changes. The A1 supplier or an identified incoming unit must still establish the VBUS interruption, native USB/recovery routing, hardware grant and inhibit signals, battery thermal protection, wire landings and service access. The [system implementation gate](../../electronics/integration-r0004/implementation-gate.md) and [eleven open first-article gates](../../electronics/integration-r0004/first-article.csv) remain applicable.

| Board | ERC / unconnected / parity | DRC | Independent plotted copper |
|---|---|---|---|
| [A3 CIE haptic](../../electronics/pcb-haptic-cie-r0001/README.md) | 0 / 0 / 0 | 3 open J1 courtyard overlaps | 7 nets, 25 pads, 14 plated holes |
| [A4 audio, key, I²C](../../electronics/pcb-r0004/README.md) | 0 / 0 / 0 | 0 | 14 nets, 34 pads, 2 plated vias |
| [A5 USB power](../../electronics/pcb-power-r0004/README.md) | 0 / 0 / 0 | 0 | 10 nets, 35 pads, 20 plated holes |

A3 uses a 1.40 mm shim to elevate J1 above C1 and U1. R1 is DNP. Nominal distances in the installed CAD are recorded in [courtyard measurements](courtyard-measurements.json). Each contact, tolerance, kink insertion and solder-tail projection still needs physical evidence. None of the three DRC errors has been suppressed.

## Solver evidence

The pinned ngspice-33 replay ran all **60 historical cases** and compared their decks and recorded scalar results with the immutable suites. The **85 original candidate and control cases** reproduced all 170 measurements, including the original five out-of-range results. Those consist of three no-cell operating conditions and two superseded circuits. The previous electrical exceptions remain individually documented in the [exception register](../../electronics/integration-r0004/exceptions.csv) and [original results](../../electronics/integration-r0004/results.csv).

The **38 post-layout cases** yielded 75 measurements within limits, 15 characterization measurements and two expected failures. The unchanged factory VBUS bypass drew 348.837 mA against a 100 mA limit. Repopulating an A3 2.2 kΩ pull-up drove 3.961 mA against a 3 mA sink limit. The A4 remote-key sweep separately exercised **85 cases**, with 84 passing and one deliberately open USB-supply lead leaving PWRON at 3.30 V while pressed. In all, 268 cases were exercised across these groups. [Summary](replay.json) · [Post-layout measurements](measurements.csv) · [Solver decks and logs](postlayout-logs.zip) · [Remote-key measurements](../../electronics/pcb-r0004/key-corners.csv)

The copper model sums routed segment resistance across each named network using assumed finished copper of 25 µm at 70 °C and 18 µm via-wall plating. Via length is taken from each PCB's thickness. The far-end bus fixture includes the longer A3/A4 signal-trace path, seated W4 jacket length, 4 mm of stripped-end allowance, nominal 26 AWG copper and 25 mΩ for an aged contact plus crimp. The fixture retains the specified 100/200 pF load and characterizes one branch. It does not characterize complete A1/W1 copper, tee resistance, real distributed parasitics, mode-change logic or installed thermal response. The USB and driver models retain the assumptions of the source decks. [Per-board copper](copper.json) · [Installed route lengths](../../electronics/harness-r0005/routing.json) · [CviLux electrical limits](https://www.cvilux.com/uploads/spec/101/753/SPCI172.pdf)

## Reproduce the checks

Run the following from this directory. KiCad 10.0.8 needs its stock libraries. The artwork checks use Python, Gerbonara 1.5.0 and Shapely 2.1.1. The housing-distance check uses CadQuery and the locally prepared supplier models.

```text
kicad-cli sch erc --format json --exit-code-violations -o <board-folder>/erc.json <board>.kicad_sch
kicad-cli pcb drc --schematic-parity --all-track-errors --format json --exit-code-violations -o <board-folder>/drc.json <board>.kicad_pcb
kicad-cli sch export netlist --format kicadxml -o ../../electronics/pcb-haptic-cie-r0001/connectivity.xml ../../electronics/pcb-haptic-cie-r0001/A3-CIE-R0001.kicad_sch
python plot_review.py --kicad kicad-cli A3 A4 A5
python ../../electronics/pcb-haptic-cie-r0001/check_artwork.py
python ../../electronics/pcb-r0004/verify_artwork.py
python ../../electronics/pcb-power-r0004/check_artwork.py
<KiCad Python> extract_copper.py
python replay.py --engine <ngspice-33>
python ../../electronics/pcb-r0004/key_corners.py --engine <ngspice-33>
<CadQuery Python> verify_courtyards.py
<CadQuery Python> verify_model_rebuild.py <local-supplier-download-folder> --kicad kicad-cli
```

Repeat the first two commands for each project. A3's DRC exit is 5 with the three courtyard errors listed above. A fresh Excellon parse emits a Gerbonara syntax warning for KiCad's G90 absolute-mode declaration after the header. The coordinate-based checks independently verified the plotted hole positions. Rule clearance, nominal geometry and solver reproduction are digital evidence only. Fabrication, purchase, powered tests and physical acceptance remain open.
