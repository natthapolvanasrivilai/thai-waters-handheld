# PolyTerra PLA fit print on SuperTack

Open [the editable Bambu Studio project](Thai-Waters-R0004-PolyTerra-PLA-SuperTack-X1C.3mf) for the next unpowered print. TW-A-0003-R0005 is the PLA print configuration of the R0004 enclosure. It carries the single status window, rear-fastened smooth bezel, case-mounted board, diffuser shelf, corrected component clearances and revised reel/handle orientations. The assembly steps and positions are in the [offline 3D guide](../enclosure-print-r0004/Enclosure-fit-guide.html).

Select the **X1 Carbon, 0.4 mm standard-flow nozzle and Bambu Cool Plate SuperTack**. Every part, brim and support uses Polymaker PolyTerra PLA. The plate sequence preserves the product colors. With a single spool, assign each selected plate to the loaded PolyTerra spool. Each individual plate uses one filament.

| Plate | Parts | Color | PLA | Time |
|---|---|---|---:|---:|
| 1 | Housing and indicator shelf | Sage | 59.64 g | 2 h 47 min |
| 2 | Bezel, rotor and retainers | Charcoal | 10.88 g | 40 min |
| 3 | Rod handle | Sage | 26.91 g | 1 h 12 min |
| 4 | Diffuser fit gauge | White | 0.38 g | 9 min |
| 5 | USB mask and service cover fit gauges | Black | 0.87 g | 11 min |
| 6 | Interchangeable battery gauges | Gray | 14.35 g | 34 min |
| 7 | Boards, speaker, motor and connector gauges | Gray | 32.54 g | 1 h 22 min |
| 8 | Reel controls and keyed power cap | Amber | 1.10 g | 15 min |

The complete set takes approximately **146.7 g and 7 h 10 min** in the native estimate. Plate times are rounded individually. Plate 4 gives a quick first print. Follow with plates 1, 2 and 7 for the enclosure check. The profile requests **220 °C nozzle and 45 °C bed**. Volumetric flow is capped at 12 mm³/s, first-layer speed at 25 mm/s, outer-wall speed at 55 mm/s and top-surface speed at 45 mm/s.

[View the eight native plate previews](plate-key.png)

## Cleanup and fit

- Lift small parts by flexing the plate and supporting the body of the part. Take particular care with the 0.51 mm USB mask, the bezel hooks and the folding-stem hinge. If a print holds too firmly, Bambu's SuperTack guidance allows warming the bed to 50 °C to aid release. [Plate care](https://bambu-lab-uk.myshopify.com/products/bambu-cool-plate-supertack)
- The housing, rotor, handle and folding stem use local sacrificial support. Remove exposed supports in small sections while supporting the nearby wall. Inspect the status window and six rear access passages with a light before assembly. Check the remaining parts against the [per-part first-article sheet](first-article.csv).
- Install the diffuser gauge and shelf before the display. Inspect the single window and check that the RGB board gauge seats. Fit the bezel level, engage both hooks, and hand-start the two screws from the rear. The matte diffuser tests its physical fit. The rigid mask and service cover test their outlines and seats. Use production materials to evaluate light transmission, sealing and flex.
- Record fit, bridge finish, support release and any fracture on the first-article sheet. This exact PLA print has no physical result yet. Powered hardware qualification remains open.

## Digital checks

The native project preserves every deposited part mesh and its placement from R0004. Changes to the 3D resources are confined to the nonprinting housing support blocker. The first PLA slice put breakaway support inside the status channel and rear access holes. Local exclusions cleared the status window, the two rear driver bores and four controller screw passages. Positive witnesses show material around the openings and deposited roof/shoulder material anchored to the previous model layer. This is a toolpath check. Bridge sag, as-printed clearance and extraction force require a sample. [Housing passage measurements](housing-features.json) · [Roof and shoulder backing](roof-paths.json)

All 27 objects deposited through their intended height during the full slice and a separate reopen of each plate. First-layer contact, material, actual heater commands, islands and supports were checked. One 1.65 mm² ledge on the handle starts above support at 5.6 mm build height; support overlaps 56.8% of that patch at the designed separation. Independent slices can vary in support line routing, with support volumes recorded for both runs. [Native slice review](slice-review.json)

The review sampled wall thickness in the saved print orientation for all 27 meshes. The six small-part witnesses additionally compare the nominal cross-section to actual beads on each layer. They cover the mask, diffuser flange, screw keeper, nut keeper, RGB carrier and keyed power cap, including open holes where present. [All-part thickness samples](thickness.json) · [Small-feature deposition](fine-features.json)

Build with `project.py FILAMENT_PROFILE_DIRECTORY` using the installed X1C profile. Run Bambu Studio against the issued project with all plates, then with each plate individually. `audit.py SLICE_ROOT --replay` expects each output in plate0 through plate8 with sliced.3mf, result.json and the plate G-code. Run `fine_features.py SLICE_ROOT/plate0`, `housing_features.py PLATE_1_GCODE` and `roof_paths.py PLATE_1_GCODE` for the feature checks.
