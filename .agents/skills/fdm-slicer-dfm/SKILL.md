---
name: fdm-slicer-dfm
description: Use for FDM CAD design, native slicer setup, supports, failed or missing toolpaths, and ready-to-print project verification.
---

# FDM design and slicer verification

Deliver a usable native project for the specified printer and intended fit trial. A valid mesh, an empty warning list, and a colored preview are not evidence that all parts or features will print. Fix every reproducible issue that affects the intended use, rerun the affected checks, and explicitly hold unresolved issues. Never promise print success or authorize a physical action from digital evidence alone.

## Baseline and print intent

- Identify the exact source CAD, printable mesh and native project by digest. Map every expected part/quantity to stable part and slicer instance IDs, plate, orientation and intended bed contact. Preserve unrelated project objects; do not let auto-arrange or auto-orient silently move them.
- Verify the selected printer, nozzle, layer height, process profile, plate, temperatures, material compatibility, logical filament/AMS mapping, brims, supports and seams on each plate. Separate incompatible print conditions and preserve material intent. Record physical spool/plate preparation separately, not as a simulated result.
- Mark controlled mating dimensions, seal/flatness regions, functional bores and keepouts, screw paths, stops, mask boundaries and any known failure coordinates. Define acceptance and local witness regions against the drawing or a checked reference **before** tuning. Map the model and installed axes to build/G-code coordinates; never guess the registration.

## Fix the cause, not the preview

1. Compare actual native paths and settings against exact part geometry. Check first-layer area and connected components; every elevated island or wall start; wall count, bridges and overhangs; same-part backing or correct support/transition; removal/access without blocking bores or damaging functional surfaces.
2. First try a reversible change that addresses evidence: orientation, contact area, intended support/bead width, local blockers/enforcers or compatible bed/profile. Show the affected path before and after. Do not hide missing thin walls with a generic “thin walls” toggle or suppress support globally to clear one channel.
3. If the geometry is not printable within that envelope, change the CAD: continuous walls, supported ramps/ribs, teardrops outside protected bore gauges, reachable supports, or separable positively located parts. Preserve fit datums/clearances and original functional geometry unless separately agreed. Recheck interference, strength assumptions, fasteners, accessible installation and support removal after any change.
4. Separate optical plausibility from measurements. Use the [offline extrusion guard](../../../manufacturing/digital-extrusion-guard.md) to compare deposited model bottom/top versus placed mesh and require positive model paths inside independently chosen local feature witnesses. It does not certify connectedness, local fill, material behavior, support adequacy, gauge clearance, or actual printing. Audit those independently and keep failures open.

## Native reopen gate and handoff

Reopen the exact delivered editable project in the appropriate native slicer, retain placement and settings, and slice every expected plate without silently dropping objects. Independently reopen and reslice the critical plate/feature in a clean session. Check hashes, plate/object mapping, warning output and actual deposited paths. Keep scoped witnesses, input revisions, failures and reproducible results. A quiet slice is strictly digital evidence; tool-less assembly, as-printed fit, thermal behavior, wear, and any energized or production tests remain separate gates. Preserve any existing hardware hold and never send to or operate a printer solely because this checklist passed.

For a PCB fit plate, register each inert board, spacer and mounted height to the current installed assembly. Keep the printed R20 carrier trial separate from the full shell's integral mount. Compare artwork, pin spacing, locating-hole toolpaths and seated-case collisions. Verify the project has a filament color entry for every material slot. Missing color entries silently truncated the R0011 optical and flexible plates at the first layer despite a successful native slice. [Worked example and acceptance records](../../../hardware/mechanical/pcb-fit-r0013/README.md)

For small dry-fit spacers, state which product material or bond stack each gauge represents. If seats can be built into a dummy board, compare their installed footprints and heights, verify the native toolpaths at every joint, and check stability of any loose board resting on them. Record an observation from an animation separately from an observed print failure. [Display gauge example](../../../hardware/mechanical/pcb-fit-display-r0002/README.md)

When a moving pocket thins the rim, section the actual mesh through the marked end and bevel. Compare a transverse swept-bead witness before and after at matched build heights. Check the added material through the full folding and rotation envelope. Audit every active native instance, including small optics and flexible parts, for thickness, bed contact and islands. Identify which starts rely on support and give them physical removal checks. [Seven-plate worked example](../../../hardware/mechanical/reel-dfm-r0001/README.md)

For an enclosure closure trial, include package height, lead exits, gaskets and the mated connector in interchangeable inert gauges. Compare the printed board envelope to each component solid. Slice every instance, then reopen changed plates independently. Sweep the shelf, plug, display and actual tool envelope with the other installed parts in their stated positions. Record screw-tip relief, glass clearance, support removal and real wire access separately. [Enclosure fit example](../../../hardware/mechanical/enclosure-fit-r0003/README.md)

For new native print projects, inspect the exported outer skin for the agreed aperture count, bezel outline and hidden closure. Reopen in Bambu Studio and check deposited material, color, bed surface and body orientation for every instance. Separate one-color plates when the job does not require multicolor printing.

When changing materials or the physical bed, check actual heater commands and verify toolpath cross-sections inside service channels and blind fastener access passages. Where supports could become trapped, use local exclusions and check both the open passage and the roof backing. Document rigid and opaque substitutes as fit gauges. [All-PLA example](../../../hardware/mechanical/polyterra-fit-r0001/README.md)

For angled designs, recover the intended bearing face from CAD, test the unsupported receiver edge, check support contacts beneath any new starts, and map keepouts into the inclined machine frame. Check the center-of-mass projection against the actual bed footprint, then inspect support access and stability physically. [Worked example](../../../hardware/mechanical/polyterra-fit-r0002/README.md)

When retiring an optical path, check the interior collector, the buried bore, and the exterior skin in both the installed CAD and the delivered print mesh. Count exterior apertures and recheck the live diffuser and connector against the updated solid. [Single-light correction](../../../hardware/mechanical/polyterra-fit-r0003/README.md)
