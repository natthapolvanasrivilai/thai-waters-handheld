# Project status

Reviewed 2026-11-23

## Engineering revision

The seated-display assembly pairs TW-A-0001-R0013 mechanics with TW-A-0002-R0006 electronics. The modeled haptic plug withdraws 8.25 mm with the display seated. The R20 print trial tests the carrier and floor sample separately.

[Assembly and USB evidence](../../quality/seated-connector-review.md) · [Interactive seated connector motion](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0013-seated-service-review-1/TW-A-0001-R0013-motion-review.html) · [Placed boards and circuit checks](../../hardware/verification/r0013/README.md) · [Revision register](../../hardware/revisions/README.md)

## First physical print

The owner confirmed that the R20 four-post carrier fits the printed floor sample. The parts came off the plate intact with heavy stringing. A physical A2 sensor board was unavailable. Board seating, printed dimensions and repeatability still need a specimen check.

[Photos and illustrated fit check](../../hardware/mechanical/pocket-reel-r19b-removal-trial/QA/R20-first-print/README.md)

## Next fit check

Select only plate 7 of the R0013 X1C project to print eight inert PCB gauges and eight loose spacers for A3, A4 and A5. Bambu Studio estimates about 65 minutes and 26.8 g of PETG on the Engineering Plate. Check whether all four corners of the A2 gauge seat on the printed R20 carrier. This checks nominal fit. Actual connector motion, solder clearance, fastener load and powered operation need physical parts.

[Illustrated plate map](../../hardware/mechanical/pcb-fit-r0013/plate-7.png) · [Gauge dimensions and print instructions](../../hardware/mechanical/pcb-fit-r0013/README.md) · [Download the seven-plate X1C project](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0013-pcb-fit-1/Thai-Waters-R0013-PCB-Fit-X1C.3mf)

In the older R0011 enclosure project, the slicer silently produced just one model layer for each of the five parts on plates 4 and 5. In the corrected download, each of the three light guides slices to six layers, the USB shield mask to three and the service cover to 23. All 35 objects across seven plates passed the model-height toolpath check. Plate 7 also passed after reopening and slicing it separately. Physical fit of these gauges still needs a print.

[Native slicer and layer-height evidence](../../hardware/mechanical/pcb-fit-r0013/QA/project-check.json)

## Qualification and software

Powered assembly and production are on hold. Incoming-controller checks, measured USB behavior and physical latch and wire tests remain open. The software record tracks the phone playtest separately. The historical handbook tabs retain the embedded simulator, exploded assembly, circuits and costing from the R0011/R0004 review.

[Hardware gate](../../quality/hardware-gate.md) · [Current software and build evidence](Software-and-tests.md#current-release) · [BOM and costing](BOM-and-business.md) · [Product tracker](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1) · [Product wiki](Home.md)
