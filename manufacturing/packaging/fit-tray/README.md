# Inert packout trial

Print the [floor layout](floor-layout.svg) and [three divider blanks](divider-dieline.svg) at 100% on landscape A4. Check the 50 mm scale before cutting. This trial sizes the PK1 carton and PK2 dividers for the handheld with its reel folded and its rod grip removed. Use a dummy device or empty case for the first sample.

| What goes in the carton | Placement and retained fit evidence |
|---|---|
| Handheld | Screen up, folded reel clear of the wall. Installed CAD gives 110.72 × 75.40 × 33.20 mm. The device bay leaves 8.28 × 12.60 × 17.30 mm **in total** for protection and tolerance. |
| Rod grip and captive hardware | Rotate the removed grip by 90° in plan. Allow 130.40 × 31.00 × 38.94 mm including the screw and keeper. Keep the narrow locking features clear of the divider. |
| USB cable | Use the BOM’s 1 m Tensility 10-03675. Measure its naturally tied coil with both plugs before accepting the 101.5 × 88 mm bay. |
| Hex key | Fully sleeve the Wera 05021015001, close the sleeve and measure it against the 77.5 × 52.5 mm bay. Verify it stays captive when inverted. |

**Carton proof.** Start with a finished internal 222 × 142 × 52 mm sample, 1.5 mm measured divider stock and a 48 mm divider height. Cut the three rectangles, fold and glue their 8 mm feet as shown. Trim overlapping feet at the junctions to one thickness. Recheck all clear dimensions after folding and adhesive cure. The CAD fit uses one board thickness at the floor. The other 4 mm above the dividers is available for a loose top pad secured by the lid. The sample assumes that pad bridges the perimeter and dividers. Measure the loaded deflection above the glass.

**Restraint proof.** Fit side pads against broad housing corners. Relieve the pads at the reel, USB port, button and receiver. Support the back shell on broad areas, keeping the projecting receiver out of the load path. Restrain the grip by its thick body. Pack the cable and key in closed sleeves. Mark contact with transfer paper on an inert print. Close and invert the sample over the bench in six orientations. Inspect for accessory migration, shell movement, marks on the display, button actuation and load on the reel. Record the board caliper, pad material, pad thickness, final bay dimensions, damage and photos alongside the sample ID. Change the relief or restraints and repeat if there is contact.

[Calculated dimensions and source revision](dimensions.json) · [Rebuild from installed component bounds](build.py) · [Existing PK1 and PK2 BOM allocations](../../../sourcing/production-intent/R0009-cutstock.md#pk1)

The packout is a layout for a hand sample. It still needs a converter proof, transport testing, delivered cable and key measurements, and a decision on packaging costs. Pack compliance and shipping release remain in the [manufacturing gates](../../gates.md).
