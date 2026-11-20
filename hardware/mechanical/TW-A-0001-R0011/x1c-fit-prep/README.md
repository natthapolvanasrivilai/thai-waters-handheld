# R0011 X1 Carbon geometry layouts

[Download the six geometry layouts](Pocket-Reel-R0011-X1C-geometry-plates.zip) · [Placement CSV](part-placement.csv) · [Track native Bambu Studio validation](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/19)

Geometry-only preparation for the existing R0011 **unpowered fit kit**. The ZIP contains six numbered 3MF layouts, a placement CSV, and a quick-start guide. The 19 archived meshes (17 device parts and two optional inert gauges; 243,922 triangles) retain their source geometry, orientation, and 100% scale. Only XY placement was added. The layouts were checked geometrically on a nominal 256 mm plate using older A1 brim envelopes as reference, **not** as X1C slicer settings.

| Plate | Parts | Material intent |
| --- | ---: | --- |
| 01 | 1 | Opaque PETG housing |
| 02 | 10 | Opaque PETG fit parts |
| 03 | 1 | Opaque PETG rod grip |
| 04 | 3 | Clear PETG guides |
| 05 | 2 | TPU, direct external feed |
| 06 | 2 | Optional inert gauges |

## Before printing

1. Import each numbered 3MF **as geometry** in its own native X1 Carbon project plate. Match the physical filament, build plate, nozzle, and process. If Studio recenters objects, restore the footprint centres in the CSV. Do not rotate or rescale.
2. Set the opaque PETG process separately from clear PETG and ordinary TPU. Use a compatible physical plate and confirm an external-spool TPU feed and the actual material. Keep bores and mating surfaces untextured.
3. Save and reopen a native Bambu Studio project. Slice offline and inspect first-layer contact, supports and removal access, brim clearances, plate exclusion zones, guide apertures, and tall grip stability. Start with an unpowered aperture/receiver/fastener fit test before selecting a complete print run.

These files contain **no slicer profiles or G-code**. Native Studio import, slicing, support preview, and physical fit have not yet been verified. The [controller screw access conflict](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/27) stays open. Inert gauges are not batteries; do not connect them or power the prototype. The [hardware gate](../../../../quality/hardware-gate.md) is unchanged.

## Provenance

- Source: [R0011 receiver-down fit-kit release](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0011-receiver-toolpaths-2).
- Source ZIP SHA-256: `ab54511990df19cd2f868bc1724643f136454fa95ab031690cd789873bbf06ce`.
- X1C geometry ZIP SHA-256: `1ca2e0155478427aebfb5f853f90df212678d21fc5abc5c5e386b08f30bc17ba`.
- [Existing R0011 print guide](../PRINT-GUIDE.md).
