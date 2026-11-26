# R0013 circuit evidence

Use the matching [A3 layout](../../electronics/pcb-haptic-cie-r0002/README.md), [A5 USB entry](../../electronics/usb-entry-r0006/README.md) and [seated assembly](../../mechanical/TW-A-0001-R0013/README.md). Board checks and simulated electrical limits apply to the identified layouts, mounted parts and source conditions. The project has no measurements from a powered prototype.

| Circuit | Evidence |
|---|---|
| A3 haptics | [PCB rule report](../../electronics/pcb-haptic-cie-r0002/drc.json), [schematic](../../electronics/pcb-haptic-cie-r0002/circuit.pdf), [independent reconstruction from plotted copper](../../electronics/pcb-haptic-cie-r0002/artwork-verification.json) |
| A4 audio, bus and key | [Board rules](a4-drc.json), [electrical rules](a4-erc.json), [85 power-key corner and fault cases](key/key-corners.csv) |
| Routed bus/audio and historical regression | [Resistance extracted from native copper](copper.json), [solver replay and board hashes](replay.json), [measurements](measurements.csv), [decks and solver logs](postlayout-logs.zip) |
| A5 fitted USB circuit | [Routed board rules](../../electronics/usb-entry-r0006/drc.json), [native schematic](../../electronics/usb-entry-r0006/circuit.pdf), [fitted-board study](../../electronics/usb-entry-r0006/README.md) |
| Prior USB alternatives | [R0005 dual-path fault and load results](../../electronics/usb-entry-r0005/measurements.csv), [original factory bypass](../r0012/measurements.csv) |

The 268 regression cases cover 60 historical cases, 85 former controller candidate cases, 38 post-layout cases and 85 key cases. The post-layout bus and audio use the revised routing and lead lengths. Its USB cases specifically reproduce the earlier dual-path circuit. Use the dedicated A5 study for the fitted prototype's USB behavior. Each report retains failing controls, characterization measurements and unresolved conditions.

From this folder use the KiCad Python environment for copper extraction and a Python installation with ngspice available for replay:

```text
<KiCad Python> routed.py copper
python routed.py replay PATH_TO_NGSPICE
python ../../electronics/pcb-r0004/key_corners.py --engine PATH_TO_NGSPICE --output key
python review.py
```
