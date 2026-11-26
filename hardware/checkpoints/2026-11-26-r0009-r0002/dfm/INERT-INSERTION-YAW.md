# R0009 inert gauge: combined level yaw and lateral motion

**First-article and production status: HOLD.** Both exact sources are hash-checked. Over full +32 mm to seat vertical range, angle and lateral offset may each vary arbitrarily within the stated limits. Pitch and roll must remain zero in the geometric model.

Proof construction: rotate the exact 31-face reconstruction around the substrate center X22.70, Y1.10. Express the rounded substrate as a rectangular core expanded by a 1.50 mm disk. For each rectangle corner bound both projected coordinates analytically over the full yaw interval, including interior stationary angles. The planar rounded-rectangle envelope then expands by the sum of the original corner radius and the allowed lateral disk radius. Apply analogous conservative boxes to all underside steps, each at its true bottom elevation. The envelope therefore covers intermediate yaw values, not just angle samples. All candidates are screened against the exact shell with an OCC BRep Boolean; contact surfaces alone have no volume.

| Maximum yaw each side | Lateral disk radius | Conservative result |
|---:|---:|---|
| 0° | 0.70 mm | Clears |
| 0.50° | 0.50 mm | Clears |
| 1.00° | 0.50 mm | Not certified; 0.010816 mm³ substrate envelope common |
| 1.50° | 0.40 mm | Not certified; 0.120274 mm³ substrate envelope common |
| 2.00° | 0.20 mm | Clears |
| 3.00° | 0.00 mm | Not certified; 0.158041 mm³ substrate envelope common |

The exact spot checks are separate and should not be extrapolated to any untested combination. For a future witnessed first article, prefer ±0.50° yaw and 0.50 mm disk; assess measured maxima plus tool uncertainty before comparison. Confirm as-printed no-drag/no-rock and screw registration separately. This report covers neither PCB populated geometry nor connector, fixture or fastening/tilt tolerance. No geometry, slicer settings or hardware altered.
