# Display gauge with six integral board seats

The orange squares in step 19 of the original R0016 animation represent the **dry-fit fixture**. The owner spotted these parts in the viewer and has not printed or handled the A5 spacers. In the original PETG kit, the six individual pieces each have a 3 × 3 mm footprint. The new [single-piece display gauge](Display-gauge-with-seats-X1C.3mf) integrates all six seats into the dummy display. This fixture works with the R0016 housing and R0017 keyed-cap assembly. It does not change the product hardware revision.

## What is behind the screen?

A1 is the purchased Waveshare display/controller. Its four existing mounting points locate the display in the enclosure. The six proposed contact patches under A4/A5 are elsewhere on the back. No matching screw holes are identified at these coordinates. A4 has no mounting holes. The small holes on A5 are wire connections. Keep the actual display unmodified. [A1 gauge geometry](../pcb-fit-r0013/GAUGE-DATUMS.md) · [Manufacturer documentation and drawings](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-3.5B)

| Board | Why the prototype has it | Dry PETG seat | Proposed powered assembly |
|---|---|---|---|
| A4, 23 × 13 mm | Connects the remote power key, speaker-level resistors and I²C pull-ups to A1 and the harness. | Three seats, 2.465 mm tall | Three 3 × 3 × 2.00 mm insulating blocks, with a nominal 0.25 mm adhesive layer on each face |
| A5, 23 × 16 mm | Detects the USB-C source advertisement and limits input to the controller’s existing power-management chip. Charging performance still needs bench measurement. | Three seats, 3.160 mm tall | Three 3 × 3 × 2.70 mm insulating blocks, with a nominal 0.25 mm adhesive layer on each face |

The project uses daughterboards to prototype custom circuits alongside the purchased controller. The electrical architecture does not require these functions to remain on separate boards in a production redesign. The two boards sit side by side with a nominal 2.00 mm edge gap. Printed seat heights include the entire gap to the gauge’s flattened copper envelope. The production BOM still lacks a chosen block material, adhesive and qualified mounting process. [A4 circuit](../../electronics/pcb-r0004/README.md) · [A5 circuit](../../electronics/usb-entry-r0006/README.md) · [Mount BOM](../../../sourcing/production-intent/R0012-interconnect-delta.csv) · [A5 copper and bondline](../TW-A-0001-R0013/QA/A5-bond.json)

## On the bench

Print this one-piece opaque PETG gauge only if you want the fixed seats. The X1C native estimate including startup is 53 minutes and 23 g. Reuse the existing A4 and A5 board gauges. If you already have a plain Plate 7 A1 and the six loose blocks, that earlier kit can still check the original stack heights.

1. Lay the dummy A1 glass-face down. Find the three short seats toward the service edge and the three tall ones toward the power key. Leave all six loose blocks off the new gauge.
2. Place the A4 and A5 gauges flat-back-down on their respective seats, with the component shapes facing you. Hold the free edge of A5. Its uniform-density solid model’s centre of mass projects **2.37 mm outside the support polygon**. This calculation concerns the loose gauge. Real PCB mass distribution and bond retention need measurement.
3. Support both boards and the resistor gauge when turning the assembly over. Record actual seat heights, rocking and closure. These posts locate the gauges vertically only. No adhesive is called for during this check.

The released STL is a single connected body. Its added volume matches the six original pads on the registered display, with 9 mm² nominal bearing area at every board contact. Two independent Bambu slices show material through the six joints, with 10.00 and 10.60 mm final bearing layers versus CAD heights of 9.965 and 10.660 mm above the bed. Print and removal still require a physical trial. [Fit measurements](fit.json) · [Native print and balance checks](native-check.json) · [Print STL](display-gauge-with-seats.stl)

## Other small parts under review

The seven-plate project’s native object dimensions distinguish the following concerns. Dimensions are extents of the printed models. They do not establish break strength or bed-removal force.

| Item | Printed dimensions, mm | Next physical check |
|---|---|---|
| Plate 7 USB1 lamp gauge | 4.80 × 3.20 × 0.85 | Handling during side insertion. Keep this gauge removable to test the actual service path. |
| Plate 7 USB2 resistor gauge | 3.20 × 2.00 × 1.05 | Pickup and orientation. Review a removable handling fixture. |
| Plate 4 USB light guide | 7.32 × 1.20 × 1.20 | Survival on removal and optical alignment. Review captured optics before enlarging the stem. |
| Plate 2 receiver nut keeper | 7.70 × 7.70 × 0.83 | Edge lifting and retention with the actual nut. |
| Plate 5 USB-C mask | 8.01 × 13.88 × 0.51 | TPU removal and tear resistance around the opening. |

[Seven-plate native results](../TW-A-0001-R0016/Printing/QA/native-all.json) · [Small print defects #17](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/17) · [A4/A5 mounting qualification #100](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/100)
