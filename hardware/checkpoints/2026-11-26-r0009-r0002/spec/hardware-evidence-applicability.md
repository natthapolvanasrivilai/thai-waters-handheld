# Pocket Reel hardware evidence applicability
26 November 2026 · Engineering verification control; HWS-001 rev 0.3 unchanged

| Evidence | Configuration and scope | Current disposition |
|---|---|---|
| PR #98 seated service | `9abc5096fec9e24ba23b13151e6d650588ba1d20`; TW-A-0001-R0013 + TW-A-0002-R0006, with then-fitted separate A4 and A5 | Historical exact CAD shows at least 0.500 mm nominal clearance for all four moving W4 jackets over 8.25 mm. The 0.615 mm sampled SDA witness and 0.040 mm nominal terminal-lock clearance are not transferable to the combined PCB. |
| R20 first article | Inert carrier print from the separate print track | Intact removal and dry floor fit reported; heavy stringing remains. No populated fit or mechanical strength qualification. |
| Current combined-board assembled proof | TW-A-0003-R0009 + TW-A-0004-R0002, moving W4 VCC against populated PCB | Conservative prior bound 0.441383675 mm is below 0.500 mm. It does not prove actual contact, but does not pass. W2 is a stationary USB-power lead and not this witness. |
| Current combined-board proxy | Same nominal registration, inert R0002 gauge only | Refined continuous VCC lower bound 0.550099049 mm; only 0.050099049 mm remains above the gate. A bare proxy cannot sign off the populated board; do not combine this row with R0013 clearance. |
| Current mechanical and electrical acceptance | Native KiCad/STEP and printed enclosure, actual installed or trial components | Keep #12/#13 and print gates open. Do not claim ready to print, fabricate, power or flash. |

## Frozen comparison before geometry changes

1. Verify exact populated PCB STEP and installed parent BREP identifiers, active component and solder envelope, mounted transformation, drawing-max intact jacket, full seated restraints, and measured or bounded assembly tolerance. Reject missing provenance rather than substituting the inert gauge.
2. Run the same conservative interval and margin rules on the populated geometry over the entire 0–8.25 mm travel, on all four moving jackets against fixed parts and each other. Retain the guard band and all separate rigid-plug, rocker, crimp and terminal-lock checks. Capture limiting moving/fixed pair, interval, geometry, near-surface witness and bounded minimum.
3. Require digital clearance ≥0.500 mm after all applicable closure terms; if any leaf is below or unbound, keep HOLD and use the witness to decide whether proof refinement or a route change is justified. Attach a deliberate encroachment control that fails.
4. Separately record received-part identification, print tolerance, real conductor dress, rub/latch/retention and repeated withdrawal on the assembled unpowered first article. Historical geometry or a passing digital proxy is not physical acceptance.
