# R0010 print and service guide

One handheld uses 17 printed parts. P17 is the opaque case-colour lower service cover. The sixteen R0009 parts retain their registered files and part revisions. Use the paint-free TPU diaphragm, clear light guides, PETG parts and two battery gauges as described in the [R0009 assembly guide](../TW-A-0001-R0009/PRINT-GUIDE.md). In the downloadable ZIP this guide is under `R0009/PRINT-GUIDE.md`. The two gauges are shop tools. The monochrome USB mask STL is an alternative to the two-material 3MF. Fit one mask per unit.

## Print P17

Load `Print/service-cover.stl` at 100% scale in millimetres. The flat 28.8 × 8.8 mm exterior face sits on the bed. The four hooks and two shorter centering ribs point up. Use opaque, case-colour TPU 95A. A 0.4 mm nozzle and 0.20 mm Standard on textured PEI produced a single watertight body in the Bambu A1 toolpath. The simulation used 0.55 g and 4 min 1 s with zero brim and support extrusion. Keep the hook flanks, gaps between hooks and west thumbnail relief clear of strings. Inspect all four for continuous perimeter lines. The retention ramps need to flex. Rigid PETG changes that behavior.

## Fit and service

1. Close the housing and inspect the 26 × 6 mm opening at the lower edge left of the rod. Confirm its back edges are clean and the internal loom remains on the registered route.
2. Orient the cover with the smooth face out and thumbnail relief toward the USB end. Insert the centering ribs, then press along both long edges. Each pair of hooks can flex toward the centre and recover behind the wall. Run a fingertip around the perimeter to confirm the flange seats flat. Check normal top-key operation and that the retained cover stays clear of the rod during fitting and removal.
3. To reach the service switches, lift the relieved short edge with a thumbnail or a blunt plastic pick and peel the cover away progressively. With the display facing you and the reel on the right, the switches run PWR, RESET and BOOT from left to right. Use a blunt insulated 2 mm probe perpendicular to the wall. The switch tips are 7.65 mm behind the outer wall. Refit P17 after service.
4. On the first article, measure seating and peel forces, check retention after repeated servicing, and inspect for hook wear or permanent set. Confirm that the switches release freely after refitting, that the loom stays out of the opening, and that a speaker sweep produces no cover rattle. Record material, print profile, measured dimensions and observations against the unit serial. This is an engineering fit release.

## Files and rebuild

The print ZIP collects the 17 device positions, the alternate USB mask and both gauges under `Print/`. It includes installed part CAD, print datums, the print manifest, fit results and a SHA-256 inventory. The separate dressed STEP places the 135 product components, including the supplier-shape battery and the fitted cover, on the assembly datum. The cover’s printed Z points into the case along assembly +Y.

From a repository checkout, use Python 3.11 with the project CadQuery, NumPy, trimesh and VTK environment. Run the following commands in the R0010 directory. Use the published R0009 compressed STEP that matches the digest in its export verification. The cover and print rebuild can run independently of the STEP build.

```text
python build.py --work <scratch>
python check_print.py --work <scratch>/slice --slicer <bambu-studio-executable>
python assembly.py --reference <R0009-dressed.step.gz> --work <scratch> --exports <exports>
python render_cover.py --work <scratch>
python package_prints.py --exports <exports>
```

The packaged print files and STEP are ready for use. The [fit report](QA/service-cover.json) records exact CAD checks. The [print report](QA/print-audit.json) contains the support, mass, time, slopes and mesh result for each plate.

