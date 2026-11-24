# Project status

Reviewed 2026-11-24

## Engineering revision

TW-A-0003-R0004 is the current unpowered fit kit. One RGB status window sits below USB-C. The smooth bezel engages two hidden hooks and fastens from the rear. All 27 objects on eight X1C plates were sliced in their assigned materials. Powered RGB, batteryless startup and physical fit remain open. [Bambu Studio project](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/enclosure-fit-r0004-1/Thai-Waters-R0004-X1C-Color-Fit.3mf) · [Offline 3D fit guide](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/enclosure-fit-r0004-1/Enclosure-fit-guide.html) · [Print sequence and measurements](../../hardware/mechanical/enclosure-print-r0004/README.md)

TW-A-0001-R0017 fits a keyed power cap into the existing R0016 housing. Reprint only the cap. Both its pressing face and the inner flange follow the single square corner in the existing opening. [Cap-only X1C plate](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0017-keyed-cap-fit-2/R0017-keyed-power-cap-X1C.3mf) · [Profile and fit evidence](../../hardware/mechanical/TW-A-0001-R0017/README.md)

TW-A-0001-R0016 provides a side-loading channel for the USB indicator and includes the power-key relief and A3 board rails. [R0016 housing and dry fit](../../hardware/mechanical/TW-A-0001-R0016/README.md)

TW-A-0001-R0015 adds clearance for the power-switch rim during assembly. The R0016 plate 1 housing carries that power-key change forward. [Housing change and fit procedure](../../hardware/mechanical/TW-A-0001-R0015/README.md)

TW-A-0001-R0014 integrates the two A3 haptic-board supports into the housing floor. TW-A-0002-R0006 remains the electrical configuration. The 2.10 mm rails locate the underside at its previous height. During the modeled 8.25 mm haptic-plug withdrawal, the rigid moving parts stay at least 3.25 mm from the new rails and the flexible leads stay at least 4.26 mm away. [R0014 housing and fit evidence](../../hardware/mechanical/TW-A-0001-R0014/README.md)

[Assembly and USB evidence](../../quality/seated-connector-review.md) · [Interactive seated connector motion](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0013-seated-service-review-1/TW-A-0001-R0013-motion-review.html) · [Placed boards and circuit checks](../../hardware/verification/r0013/README.md) · [Revision register](../../hardware/revisions/README.md)

## Case-mounted PCB fit kit

TW-A-0003-R0001 replaces both display-mounted daughterboards with one routed case-mounted board in the new fit kit. The housing has two screw posts and an integral end rest. Print plate 1 for the housing and plate 2 for the combined outline gauge. Use the independent display mounts. [Download the X1C project](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/case-board-r0001-fit-1/Case-board-R0001-X1C-fit.3mf) · [Interactive board and support views](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/case-board-r0001-fit-1/Case-board-R0001-view.html) · [Assembly and test results](../../hardware/electronics/case-board-r0001/README.md)

The populated board and three revised power lead jackets clear in the seated model. CAD includes the 8.25 mm haptic-connector stroke and an 18 mm rigid screen lift with the leads disconnected. Both fit plates sliced. Physical fit, a complete detachable display loom and charging measurements are pending. The 330 mA batteryless startup simulations missed the required voltage. [Mount qualification #100](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/100)

## Earlier R0017 display gauge

The earlier inert PETG display has all six test seats built in. Reuse the A4 and A5 board gauges. Step 19 highlights A5’s fixed seats. The original six loose PETG blocks belong to the plain Plate 7 display. The owner observed the spacers in the animation and has not printed them. These blocks belong to the R0017 stack. [One-piece display gauge for X1C](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/display-gauge-r0002/Display-gauge-with-seats-X1C.3mf) · [R0016 guide matching the pictured housing](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/display-gauge-r0002/R0016-PCB-assembly.html) · [Board functions, real mount and small parts](../../hardware/mechanical/pcb-fit-display-r0002/README.md) · [Mount qualification #100](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/100)

## First physical print

The owner confirmed that the R20 four-post carrier fits the printed floor sample. The parts came off the plate intact with heavy stringing. A physical A2 sensor board was unavailable. Board seating, printed dimensions and repeatability still need a specimen check.

[Photos and illustrated fit check](../../hardware/mechanical/pocket-reel-r19b-removal-trial/QA/R20-first-print/README.md)

## Earlier R0016 USB indicator dry fit

R0013 through R0015 have a roof above USB1. Skip the lamp placement on those prints. In R0016, point the LED toward the USB wall, lower the upright gauge 15 mm toward the service end from the U mark, then slide it parallel to the wall toward the mark until it seats. Use the supplied Bambu project for plate 1 (estimated 2 h 7 min and 53.91 g). Its native slice left 0.10 mm of vertical clearance for the leadless gauge. The installed lamp leads cannot accommodate the guide’s 18 mm vertical display motion and need a separate wired assembly trial.

[Physical and wired fit record #99](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/99) · [Corrected R0015 guide](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0016-usb-indicator-fit-1/R0015-PCB-assembly.html) · [Motion evidence](../../hardware/mechanical/TW-A-0001-R0015/QA/usb-indicator/R0016.json) · [R0016 print and slice checks](../../hardware/mechanical/TW-A-0001-R0016/Printing/README.md)

## R0017 power cap dry fit

Align the squared corner on the cap with the matching corner in the hole. The R0017 guide opens at the alignment point. After fitting the real switch and keeper, check a centre press and an edge press for return and twist. The solid printed switch gauge checks alignment only.

With the display off the case and the switch board and its west retainer set aside, lower the cap through the open display side. Keep the pressing face pointed toward the top edge and the broad flange inside. Start 2.50 mm inboard of its seated position. When the face lines up with the opening, slide it outward into the recessed seat. Hold the flange there while preparing the board. Check for strings around the seat and stop if the cap binds. On an R0013 or R0014 print, remove the cap after this check and set the board and keeper aside. The board catches the wall during insertion. On the R0015 or R0016 housing, hold the cap seated, lower the board with its switch facing the button, then lower the west retainer. Physical fit and press/return are pending.

[Original R0016 round-cap guide](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0016-usb-indicator-fit-1/R0016-PCB-assembly.html) · [Corrected R0013 guide for the flat-floor case](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0016-usb-indicator-fit-1/R0013-PCB-assembly-corrected.html) · [Corrected R0014 guide for the integral-rail case](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0016-usb-indicator-fit-1/R0014-PCB-assembly.html) · [Measured cap motion and exterior interference](../../hardware/mechanical/TW-A-0001-R0014/QA/power-key/cap-path.json)

## Next fit check

Print plates 1, 2, 4 and 7 first. Test the clear lens under USB-C, then engage the hidden bezel hooks and install two rear screws. [First-article record](../../hardware/mechanical/enclosure-print-r0004/first-article.csv)

## Qualification and software

Powered assembly and production are on hold. Incoming-controller checks, measured USB behavior and physical latch and wire tests remain open. The software record tracks the phone playtest separately. The historical handbook tabs retain the embedded simulator, exploded assembly, circuits and costing from the R0011/R0004 review.

[Hardware gate](../../quality/hardware-gate.md) · [Current software and build evidence](Software-and-tests.md#current-release) · [BOM and costing](BOM-and-business.md) · [Product tracker](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1) · [Product wiki](Home.md)
