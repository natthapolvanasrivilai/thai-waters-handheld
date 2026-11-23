# R0015 power-key housing and dry fit

This issue affects two separate fitting operations. The cap’s wide flange enters through the open display side. The populated switch board then needs room for the metal rim of its switch while sliding down the guides. The former R0013 animation showed the flange entering from outside after the board was in place. The R0013 and R0014 walls also foul the rim during a straight board insertion. The old guide is withdrawn for that operation.

**Print only plate 1 for the revised housing.** Reuse the cap, west retainer, PCB gauges, bezel and other fit-kit parts. R0015 includes the two raised A3 rails. Keep the two loose A3 strips from an R0013 gauge plate aside. [Bambu Studio project](Printing/Thai-Waters-R0015-PCB-Fit-X1C.3mf) · [Interactive R0015 assembly guide](../../../docs/models/R0015-PCB-assembly.html)

## Fit the key before the display

1. Lay the empty housing display-side up, with the reel to the right. Keep the board, retainer and display out. Pick up the cap by its rim and face the narrow pressing end toward the top-left button opening. The wide flange faces the case interior.
2. Lower the cap inside the top wall, **2.50 mm inboard** of its final seat. When aligned with the opening, slide it outward and hold it in the recess. The 24 mm vertical movement in the guide begins with the entire cap above the housing. Check that the small face is visible in the opening and the flange stays inside. The cap face sits 0.18 mm below the outer wall and the flange overlaps the opening by 0.85 mm radially.
3. In an **R0015 housing**, hold the cap seated and slide the upright KEY gauge down the board guides. Its long edge runs left to right and its plunger faces the cap. Verify that the switch rim clears the wall and the board reaches its seat under light finger pressure. Lower the west retainer last. Inspect that the cap remains captured.
4. Keep the unit unpowered for this trial. Clear strings from the guides and the cap seat. If anything binds, stop and record the location. Use the rigid gauge to check fit and alignment. Check click, return and accidental preload with a real switch and record the result before closing the bezel.

**If you already printed an R0013 or R0014 housing**, you can try step 2 on that print. Lift the cap back out before continuing other closure trials. Set the switch board and retainer aside. Use the corrected guide for your housing. [R0013 flat-floor guide](../../../docs/models/R0013-PCB-assembly-corrected.html) · [R0014 integral-rail guide](../../../docs/models/R0014-PCB-assembly.html)

## What changed

Housing **TW-P-0001-R0012** has a shallow open-top relief behind the button opening. The CAD comparison measured **8.887644 mm³ removed** inside the key bay. The protected outer bore and cap seating shoulder are preserved. The board, switch, cap and keeper retain their installed positions. The electronics configuration is **TW-A-0002-R0006**. [Housing CAD](CAD/housing-battery-bay.step) · [Print mesh](Print/housing-battery-bay.stl) · [Slice and toolpath checks](Printing/README.md) · [Housing comparison](QA/housing-geometry.json) · [Installed assembly](installed-step.json)

The cap’s two-leg path in the parent housing clears the wall by at least 0.55 mm during lowering. It ends 0.01 mm from the flange stop; that is an axial seating dimension. The former outside approach already overlaps the housing by 8.095 mm³ at 0.50 mm outside the seated position. The R0015 motion check gives the fixed switch rim at least 0.249 mm to the relieved wall. The actuator passes the held cap with at least 0.049 mm clearance. The keeper clears the gauge by 0.100 mm. A separate 0.046461 mm³ overlap between the undeformed switch terminal and PCB hole remains to be checked with a real switch before soldering. Physical seating, component tolerances and switch actuation are pending. [R0015 cap motion and rejected exterior path](QA/power-key/cap-path.json) · [Existing housing board obstruction](../TW-A-0001-R0014/QA/power-key/key-path.json) · [R0015 board and retainer sweeps](QA/power-key/key-path.json)

## Reproduce the fit record

Regenerate the revised solid and its print mesh with [the housing builder](build_key_housing.py). The [installation exporter](assemble.py) accepts the registered R0014 dressed STEP and a local output directory. It replaces the housing, reopens the entire assembly and compares every installed member. The full supplier assembly is retained locally. [Export verification](export-verification.json)
