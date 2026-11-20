# R0011 fit print and service

## Published R0011 X1C baseline

Download [Pocket-Reel-R0011-X1C.3mf](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-receiver-toolpaths-2/Pocket-Reel-R0011-X1C.3mf) from the [private R0011 fit-print release](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0011-receiver-toolpaths-2). Verify SHA-256:

```text
510fe8e2f1930c18298fb90d9a3b1edf74ac57c71bcb89fc985bed1fc49af50f
```

**Scope:** This is the already-published R0011 baseline, not the next fit test with the newest geometry. It does not include later design revisions; use a separately versioned project after those replacement meshes and their toolpaths have been verified.

Open it as a project in **Bambu Studio 02.08.02.61**, not as separately imported geometry. The saved profile is **Bambu Lab X1 Carbon, 0.4 mm hardened-steel nozzle, 0.20 mm Standard @BBL X1C**. The six plates have **19 objects: 17 device positions and two optional inert gauges**. Keep the saved positions, scale and orientations.

| Plate | Contents | Saved material and surface |
| --- | --- | --- |
| 1 | Receiver-down housing, 1 part | Opaque PolyLite PETG @BBL X1C; SuperTack |
| 2 | Bezel, rotor and other small rigid parts, 10 parts | Opaque PolyLite PETG @BBL X1C; SuperTack |
| 3 | Removable rod grip, 1 part | Opaque PolyLite PETG @BBL X1C; SuperTack |
| 4 | C/U/P light guides, 3 parts | Transparent PETG for fit, saved as Generic PETG; SuperTack |
| 5 | Single-colour USB shield and P17 service cover, 2 parts | Opaque TPU 95A, saved as Generic TPU; Textured PEI. Load from the external spool with AMS disabled. |
| 6 | PKCELL and Adafruit cell-envelope gauges, 2 optional inert parts | PolyLite PETG @BBL X1C; SuperTack. Not device parts or batteries. |

Supports are enabled only for the housing and rotor (automatic normal, 30°; support on the model allowed). The housing has no brim. Outer brims are 5 mm for the rotor and folding stem, 8 mm for the rod grip, 3 mm for each light guide, and 5 mm for the Adafruit gauge. The saved seam setting is Aligned and fuzzy skin is off. Manual filament mapping keeps the three material slots on the single physical nozzle; each plate uses just one slot. Confirm the actual spool and surface match before printing, especially the transparent PETG and externally fed TPU 95A.

The project completed all six plates in two native slicing passes, including a separate reopen and re-slice of the saved release file. Both passed without slicing warnings, out-of-bed objects or material changes on any plate. This is slicer evidence, not a physical first article. The printer firmware and exact spools have not been verified through this check. No print was started, and no device was powered.

## Separate seven-plate Cap29 inert fit trial

Download [Pocket-Reel-R0011-X1C-Cap29-Inert-Trial.3mf](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-receiver-toolpaths-2/Pocket-Reel-R0011-X1C-Cap29-Inert-Trial.3mf) for the [#29 power-cap fit trial](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/29). Verify SHA-256:

```text
c1d969df235f458e269a065e16eeefd1f8d796a381204efff695b37a41484429
```

This separate R0011-derived project retains plates 1–6 unchanged, including their toolpaths. Nothing is substituted in the baseline, this is **not R0012**, and it does not include replacements for the other open geometry issues. The saved project was reopened and all seven plates re-sliced in Bambu Studio; it has not been physically printed or fit-tested.

Print only plate 7 for this trial. Confirm opaque PETG and SuperTack on the actual X1C. Keep the caps identified as removed: left +0.30 mm, **center +0.40 mm (try first)**, right +0.50 mm. Dry-fit only in an **empty, undamaged, unpowered R0011 housing without PCB or battery**. Check seating, capture and free travel without forcing, sanding, drilling or gluing. Stop if the stock opening is damaged. Powered fit and use remain unverified.

## Physical first-article checks still open

1. In Preview, inspect the first-layer U-shaped housing contact (both receiver lips joined by the closed end), support-only starts, seam positions and dimensional surfaces on the affected plates. Save screenshots with the checked profile. Before a full kit, run small adhesion/stringing coupons or the affected parts on the actual X1C. Record its firmware, actual filament and drying, plate prep and settings. Change one factor at a time. Do not sand the device exterior.
2. Let the plate cool before releasing the housing. Remove support below the broad rear floor, at the reel and from the receiver channel. Start at the open slide entrance and work in sections toward the stop. Avoid levering against the dovetail edges. Clear the separate speaker grille and USB-end details. Inspect for layer separation at both rail roots and for a widened first layer or support residue on the sliding faces.
3. Slide the inert grip fully to the stop by hand, engage the captive fastener and check insertion, retention, play and smooth removal. Record grip-tip deflection at the intended test load, layer cracking, permanent set and wear through repeated attachment cycles. Confirm bezel fit, clear C/U/P openings and reel travel. Check the optional inert gauges, covered lower edge, service-probe access and speaker grille. Keep the assembly unpowered; powered operation is a separate qualification gate.
4. Follow the service-cover and component assembly instructions below. Use P17 during normal operation after qualification; peel from the relieved USB end for bench access to the board PWR, RESET and BOOT switches.

[Service cover and installation](../TW-A-0001-R0010/PRINT-GUIDE.md) · [Other print materials and assembly sequence](../TW-A-0001-R0009/PRINT-GUIDE.md) · [First-article tracking](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/19)

## Historical A1 toolpath check

The oriented STL fit kit and [A1 housing toolpath audit](QA/housing-toolpaths.json) are separate historical evidence. That audit used Generic PETG and Textured PEI on a Bambu A1 with 0.4 mm nozzle, 0.20 mm Standard, 30° automatic normal support (support on model enabled) and no housing brim. The housing measures 110.72 × 74.25 × 31.00 mm in the supplied receiver-down pose. Do not send A1 G-code to the X1C.

From this revision directory in a repository checkout, use Python with NumPy, trimesh, SciPy, Shapely, Pillow and matplotlib and a Bambu Studio installation with the A1 profiles. Supply a fresh scratch folder. The report records both exact STL and G-code hashes.

```text
python build.py
python check_print.py --work <scratch> --slicer <bambu-studio-executable>
python QA/draw_toolpaths.py <scratch>
python package_prints.py --exports <exports>
```
