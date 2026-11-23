# Inspect the assembly and battery pocket

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-hardware-review-1/Thai-Waters-handbook.html)

## R0013 seated-display service

[Plug motion, installed harness, full assembly and measured clearance](../../quality/seated-connector-review.md)

## Connector service and failed-print investigation

[Open the R0012 service review, circuits, R19b print investigation and packaging trial](../../quality/hardware-review-2026-11-23.md). R0012 identifies the dressed STEP engineering branch. R19b identifies the physical X1C trial. Their housing, reel and light features differ.

## Earlier R0011 print and inspection checkpoints

The R0011 engineering model includes the receiver-down housing, lower service cover and revised haptic harness. Inspect purchased and drawing-derived geometry through the part register. Source fit, retention, tolerances and the unplaced controller power changes have open hardware gates. [Interactive private handbook and dressed STEP](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0011-hardware-review-1) · [Terminal selection, routes and clearances](../../hardware/electronics/harness-r0004/README.md) · [STEP round-trip checks](../../hardware/mechanical/TW-A-0001-R0011/export-verification.json)

The R0011 print puts the two dovetail lips and their closed stop on the bed. Evaluate it with inert gauges. The R0010 dressed STEP includes the lower service cover. Bench and powered checks remain open. [R0011 print files](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0011-receiver-toolpaths-2) · [Receiver toolpaths](../../hardware/mechanical/TW-A-0001-R0011/QA/receiver-toolpaths.png) · [R0010 inspection STEP](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0010-cover-checkpoint) · [Hardware tracker](../../quality/hardware-gate.md)

## Historical R0009 harness review

The archived engineering viewer shows **TW-A-0001-R0009 / TW-A-0002-R0003**. Use the [new assembly and CAD evidence](../../hardware/mechanical/TW-A-0001-R0009/README.md) and [connector-by-connector routing guide](../../hardware/electronics/harness-r0003/README.md). R0008 records an earlier inert fit print.

[Download the R0009 dressed STEP](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/design-review-r0009-1/TW-A-0001-R0009-dressed.step.gz) · [Candidate print and gauge pack](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/design-review-r0009-1/TW-A-0001-R0009-fit-print.zip) · [STEP round-trip evidence](../../hardware/mechanical/TW-A-0001-R0009/export-verification.json)

Choose **3D assembly** in the handbook. Drag to orbit. Select a wire, screw or board to see its part record, isolate a group, move the explode slider and step through the seven installation stages. Use the section plane at the battery fences and the reel sensor. The detachable grip uses a 35 mm slide with captive M3 retention. The top-left power cap operates a separate switch carrier.

## Released R0008 inert-fit baseline

The **TW-A-0001-R0008** viewer has 86 selectable records. Select **Battery bay** to compare the catalog pack, maximum drawing and supplier CAD with their wires. The R0008 printed set keeps 0.65 mm between the maximum pack and wire bridge. Use both inert gauges before powered closure.

Keep the supplied STL orientations. Five parts use outer brims. The A1 PETG slice generates 4.410 g of support for the housing and 0.414 g for the rotor. The other twelve prints, including both shop gauges, slice without support. The lowest elevated downward surface measures 32.37° above the plate.

- [R0008 print kit](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/TW-A-0001-R0008/TW-A-0001-R0008-fit-print.zip) · [Exploded model](../models/TW-A-0001-R0008-exploded.html)
- [Print orientation, brims, support removal and fit order](../../hardware/mechanical/TW-A-0001-R0008/PRINT-GUIDE.md)
- [Sliced layer comparison, fits and remaining first-article gates](../../hardware/mechanical/TW-A-0001-R0008/QA/README.md)
- [Hardware revisions and matched part IDs](../../hardware/revisions/README.md)
- [Historical Rev G battery housing and wire routing](../../hardware/mechanical/rev-G/README.md)
- [Previous Rev F fit study](../../hardware/mechanical/rev-F/review/README.md) and [power-key wiring](../../hardware/electronics/rev-f-power-key.md)
- [Optional reel brake experiment](../../hardware/mechanical/experiments/reel-brake)

[← Play and evaluate a cast](Game-and-demo.md) · [Read a circuit trace →](Electrical-verification.md)

[Current paired hardware revisions, firmware and first-article status](Software-and-tests.md#current-release)
