# Inspect the assembly and battery pocket

**Current PLA test print.** TW-A-0003-R0006 adds an exterior ramp to the rod receiver. The housing and grip print at 45° with localized supports. All 27 parts use PolyTerra PLA on the X1 Carbon, 0.4 mm nozzle and Cool Plate SuperTack. Twelve toolpath checks cover the status aperture, access passages, key opening and bezel pockets. Physical fit and powered verification remain open. [PolyTerra PLA X1C project](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0006-angled-polyterra-1/Thai-Waters-R0006-PolyTerra-SuperTack-X1C.3mf) · [PLA print sequence and checks](../../hardware/mechanical/polyterra-fit-r0002/README.md) · [Offline 3D assembly](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0006-angled-polyterra-1/Enclosure-fit-guide.html)

[Case-mounted board fit kit and interactive 3D inspection](../../hardware/electronics/case-board-r0001/README.md). The combined A4/A5 circuit now has a populated PCB, its own housing mounts, a two-plate X1C project and motion checks. The R0017 spacer walkthrough below is for the earlier fit kit.

[R0017 keyed cap and cap-only fit plate](../../hardware/mechanical/TW-A-0001-R0017/README.md) follows the existing power-button opening. Use it with the R0016 housing. [Archived R0017 assembly guide](../models/R0017-PCB-assembly.html)

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Download the live handbook](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0006-angled-polyterra-1/Thai-Waters-handbook.html)

[A4 and A5 explained, physical mounting and small-part review](../../hardware/mechanical/pcb-fit-display-r0002/README.md)

## USB indicator entry

The R0016 handbook shows the side slot in section. The three older guides show where the attempted insertion meets the USB-C well. The finished lamp is tethered to the display. [R0016 procedure](../../hardware/mechanical/TW-A-0001-R0016/README.md) · [Current 3D guide](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/reel-dfm-r0001-fit-1/R0017-PCB-assembly.html)

## R0015 power key

Open the PCB assembly guide and select the cap step to follow its two movements. The switch board slides in afterward and the west retainer goes in last. Use R0015 plate 1 to clear the switch rim. [Procedure and evidence](../../hardware/mechanical/TW-A-0001-R0015/README.md) · [R0015 3D guide](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0016-usb-indicator-fit-1/R0015-PCB-assembly.html)

## R0014 integral haptic-board rails

For an existing R0014 case use its corrected standalone sequence. The power board step stops at the obstructed insertion. The plate-1 floor carries A3 directly on two hard lands with open-ended adhesive grooves. The plate-7 PCB gauges also fit the preceding project. [R0014 dry fit and housing](../../hardware/mechanical/TW-A-0001-R0014/README.md) · [Download the 3D guide](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0016-usb-indicator-fit-1/R0014-PCB-assembly.html)

[Current revision and open physical checks](Current-status.md) · [R0014 plate map](../../hardware/mechanical/TW-A-0001-R0014/Printing/plate-7.png) · [Plug motion, installed harness, full assembly and measured clearance](../../quality/seated-connector-review.md)

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
