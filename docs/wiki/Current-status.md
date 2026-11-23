# Project status

Reviewed 2026-11-23

## Engineering revision

TW-A-0001-R0014 integrates the two A3 haptic-board supports into the housing floor. TW-A-0002-R0006 remains the electrical configuration. The 2.10 mm rails locate the underside at its previous height. During the modeled 8.25 mm haptic-plug withdrawal, the rigid moving parts stay at least 3.25 mm from the new rails and the flexible leads stay at least 4.26 mm away. [R0014 housing and fit evidence](../../hardware/mechanical/TW-A-0001-R0014/README.md)

[Assembly and USB evidence](../../quality/seated-connector-review.md) · [Interactive seated connector motion](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0013-seated-service-review-1/TW-A-0001-R0013-motion-review.html) · [Placed boards and circuit checks](../../hardware/verification/r0013/README.md) · [Revision register](../../hardware/revisions/README.md)

## First physical print

The owner confirmed that the R20 four-post carrier fits the printed floor sample. The parts came off the plate intact with heavy stringing. A physical A2 sensor board was unavailable. Board seating, printed dimensions and repeatability still need a specimen check.

[Photos and illustrated fit check](../../hardware/mechanical/pocket-reel-r19b-removal-trial/QA/R20-first-print/README.md)

## Next fit check

Let the R0013 plate 7 finish. For the new case, print plate 1 from the R0014 project. Reuse all eight PCB gauges and the six square A4/A5 spacers. Set aside both long A3 strips. In the new case, dry-fit A3 directly onto the printed rail tops with J1 toward the lower service edge. Check for rocking, contact under the board and display closure before any bonding.

[Download the standalone 3D PCB assembly guide](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0014-integral-rails-1/R0014-PCB-assembly.html) · [Download the handbook with the offline PCB assembly tab](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0014-integral-rails-1/Thai-Waters-handbook.html) · [Housing identification and A3 fit instructions](../../hardware/mechanical/TW-A-0001-R0014/README.md)

With an older flat-floor R0013 housing, its two loose strips still establish the correct height. The R20 carrier trial is independent of the housing change. In the R0014 project plate 7 contains the same eight PCB gauges and six loose A4/A5 spacers. The four thin A2 shims in the full housing remain separate measured stock.

[Download the R0014 X1C project](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0014-integral-rails-1/Thai-Waters-R0014-PCB-Fit-X1C.3mf) · [R0014 gauge map](../../hardware/mechanical/TW-A-0001-R0014/Printing/plate-7.png) · [Older R0013 plate map for the print in progress](../../hardware/mechanical/pcb-fit-r0013/plate-7.png)

The R0013 print project corrected the earlier one-layer fault in the optical and flexible parts. The X1 Carbon slice estimates 2 h 6 min and 53.9 g for plate 1 on the saved SuperTack PETG profile. Both A3 rails have continuous perimeter paths and open grooves, with no generated support in the A3 bay. The existing USB-end detail uses removable support. Physical A3 seating and real-board retention remain open.

[R0014 print preparation and native checks](../../hardware/mechanical/TW-A-0001-R0014/Printing/README.md) · [Earlier R0013 native results](../../hardware/mechanical/pcb-fit-r0013/QA/project-check.json)

## Qualification and software

Powered assembly and production are on hold. Incoming-controller checks, measured USB behavior and physical latch and wire tests remain open. The software record tracks the phone playtest separately. The historical handbook tabs retain the embedded simulator, exploded assembly, circuits and costing from the R0011/R0004 review.

[Hardware gate](../../quality/hardware-gate.md) · [Current software and build evidence](Software-and-tests.md#current-release) · [BOM and costing](BOM-and-business.md) · [Product tracker](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1) · [Product wiki](Home.md)
