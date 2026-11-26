# R0009 complete enclosure fit print

[Download the complete Bambu Studio project](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0009-complete-fit-1/Thai-Waters-R0009-Complete-Fit-PolyTerra-SuperTack-X1C.3mf) · [Interactive assembly guide](../../electronics/case-board-r0002/Mount-review.html) · [27-part inventory](inventory.csv) · [First-article checklist](first-article.csv)

TW-A-0003-R0009 pairs the rectangular control PCB with its matching housing. Open the project in Bambu Studio and select the numbered plate. All eight plates use Polymaker PolyTerra PLA, the X1 Carbon 0.4 mm nozzle and Cool Plate SuperTack. The saved housing and handle orientations are 45°. The complete slice estimates 144.64 g and 8 h 30 min.

| Plate | Color | Printed fit parts |
|---|---|---|
| 1 | Sage | Housing with integral PCB posts and corner support, removable status shelf |
| 2 | Charcoal | Front bezel, reel rotor, collar, grip screw keeper, receiver nut keeper, power-board retainer, battery wire bridge |
| 3 | Sage | Detachable rod handle |
| 4 | White | Single status diffuser shape gauge |
| 5 | Black | USB mask and service cover shape gauges |
| 6 | Gray | Two alternative battery pack envelopes, PKCELL maximum and Adafruit 258 |
| 7 | Gray | Display and controller, reel sensor, haptic PCB, combined rectangular control/USB PCB with package heights, top power-switch PCB, RGB indicator PCB, speaker, motor and a second haptic gauge with the plug seated |
| 8 | Amber | Folding crank arm, reel knob, keyed power cap |

## Fit sequence

1. Start with plates 1 and 7. After cooling and removing supports, inspect the two control-board screw posts and the corner bearing. Lower the rectangular gauge with its raised component blocks toward the floor. Start both real M2 × 4 screws by hand and check that all three supports bear without rocking. Install the bare and plugged haptic gauges in separate trials.
2. Follow the interactive guide for the status shelf, switch and other gauge orientations. Trial-fit each plate-6 pack separately with the wire bridge. Offer the unpowered display into its seat. Check for pressure on the component blocks and pinched cable space.
3. With plates 2, 4, 5 and 8, check bezel closure from the rear, button travel, status-window alignment, cover fit and folding crank clearance. Slide the plate-3 handle fully into its receiver and try the screw lock. Record each result on the first-article checklist.

Use actual assembly fasteners for retention tests. Printed parts stand in for bought electronics and batteries. White PLA checks the diffuser fit. Rigid black PLA checks the cover and mask outlines. Light transmission, elastomer behavior, live electrical operation and physical connector withdrawal require the intended hardware.

## Verification

Both the complete project and eight separate plate reopens produced toolpaths for all 27 objects. Plate 1 was compared face for face with the reopened [editable housing](../../electronics/case-board-r0002/housing.step). Plate 7 contains the checked [PCB gauge](../../electronics/case-board-r0002/pcb-gauge.step). Both gauge holes have a 1.70 mm clear core across all four substrate layers. Twelve housing opening checks cover model and support deposition. The mount probes measure local deposited material and pilot clearance. Strength, printed tolerances and support removal await the physical trial.

[Native slice and mesh checks](slice-review.json) · [Board mount probes](mount-paths.json) · [Opening checks, complete slice](channels-full.json) · [Opening checks, independent slice](channels-single.json) · [Electrical and installed-fit evidence](../../electronics/case-board-r0002/README.md)
