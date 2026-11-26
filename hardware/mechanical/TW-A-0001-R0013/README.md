# CviLux withdrawal with the display installed

This assembly uses the covered R0012 housing, the same plug, latch, contacts, fixed W1 branches and J8 location. Only the electrical installation and its flexible service leads are revised. The R20 X1C first article is a separately controlled fit trial.

Use **Play motion** to depress the rocker and withdraw the plug. The **Show seated display boards** control changes their visibility. The clearance readout always includes their installed geometry. The blue curve measures the rigid connector against W1. The brown curve follows the closest W4 lead to its surroundings or another lead. No enclosure access opening or tool path for pulling the assembled unit is implied by this motion.

- [Release report and engineering disposition](../../../quality/seated-connector-review.md)
- [Station-by-station seated clearances](QA/service-path.csv) · [Native measurements and model exceptions](clearance.json)
- [Continuous external lead clearance](QA/interval-clearance.json) · [Earlier routing tested against the same stroke](QA/installed-negative-control.json)
- [STEP export and reimport](export-verification.json) · [Seated assembly and pack fit](QA/installed-fit.json) · [Lower cover](QA/service-cover.json)
- [W4 cut and form definition](../../electronics/harness-r0006/routing.json) · [A3 layout and sourcing](../../electronics/pcb-haptic-cie-r0002/README.md) · [USB integration](../../electronics/usb-entry-r0006/README.md)
- [R20 carrier comparison](QA/r20-carrier-fit.json) · [Archived R19b shell registration](QA/r19b-shell-fit.json). The moving leads clear the archived shell by 0.858 mm or more at the 67 sampled stations. Two fixed ground parts have positive mesh surface gaps to the archived shell and an unresolved volume check. The seated R0013 STEP is tested separately.

## Reproduction

Use the CadQuery, OpenCascade, FCL, SciPy, NumPy and browser tools from the [R0012 service work](../TW-A-0001-R0012/README.md). Prepare its verified installed BRep cache, supplier files, full local viewer and compressed STEP. Build the new A3, USB and harness geometry as described in each design directory. Use an empty scratch and export directory for the new assembly. From this directory run:

```text
python support.py
python assemble.py --reference R0012-dressed.step.gz --work SCRATCH --exports EXPORTS --a3-parts ../../electronics/pcb-haptic-cie-r0002/placed --fixed-leads ../../electronics/usb-entry-r0006/installed-leads/installed.json
python stroke.py R0011_CACHE
python intervals.py R0011_CACHE
python regression.py
python check_installed.py EXPORTS/TW-A-0001-R0013-dressed.step.gz SCRATCH
esbuild ../TW-A-0001-R0012/service-viewer.js --bundle --format=iife --minify --outfile=SCRATCH/renderer.js
python views.py R0011_CACHE SCRATCH/renderer.js EXPORTS
python ../TW-A-0001-R0012/share_view.py EXPORTS/TW-A-0001-R0013-connector-motion.html
```

The full local views incorporate the CviLux geometry. The public download contains the wire mesh, motion and dimensional evidence. A locally generated full viewer can supply the exact supplemental meshes. [Supplier sources and checksums](../../electronics/harness-r0005/source-cad/source-manifest.json)
