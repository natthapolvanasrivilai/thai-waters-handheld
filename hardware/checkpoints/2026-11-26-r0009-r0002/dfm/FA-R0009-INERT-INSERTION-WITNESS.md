# FA-R0009 inert gauge | insertion witness (blank, not a result)

**Run only after separately authorized native plate/first article.** R0009 exact housing and inert PCB gauge. Remove both screws; do not use a screw or lever to pull the gauge into position. No assembled electronics or battery. Photograph actual orientation, both pads and the printed edges before the run. Nominals below are in housing CAD coordinates, not automatically measurements.

| Register | Exact nominal mm | Bench use |
|---|---:|---|
| X outer edges | 6.50 / 38.90 | See the straight portions, not R1.50 corners |
| Y outer edges | −16.80 / 19.00 | Use full-width opposing edges |
| Outer-profile center | X22.70 / Y1.10 | Optical/stage tracking origin |
| Substrate top at seat | Z18.54 | Take both ends; lost travel is not seating |
| Pilot A at seated target | X36.00 / Y−14.40 | From the minimum gauge edges: 29.50 / 2.40 |
| Pilot B at seated target | X10.50 / Y3.90 | From the minimum gauge edges: 4.00 / 20.70 |
| Pilot spacing | 31.38694 | Check scale and distinguish common shift from pitch error |

1. **Calibrate the view/fixture.** Clamp the housing without squeezing it. Register the stage axes to the as-built housing using the two pilot centers (non-force optical/probe methods) and check handedness against the exact shell key/port orientation. Keep the housing datum independent of the moving gauge. Check XY calibration against a scale or setting block, at both Z endpoints; validate the measurement with a known lateral shift. Record resolution and estimated lateral error. If one camera moves with Z or its scale varies, use a calibrated Z-dependent mapping or two fixed orthogonal views. Mark the top-face edges or non-protruding fiducials; no tape wrapped over edges.
2. **Witness the descent.** Zero at the registered gauge outer center (X22.70/Y1.10) and lower from +32 mm without lateral forcing. Log XY and pitch/roll throughout, retaining any frame of drag; grab calibrated readings at +32/+24/+16/+8/+4/+2/+1/seat for the sheet. Static check points alone do not establish between-point behavior. Compare indicated radial offset plus uncertainty with the CAD witness radius of **0.70 mm**. This is a classifier for whether the observed *level path* is comparable with the CAD run, not a print tolerance. If tilting or yaw is detected beyond measurement uncertainty, mark 'outside CAD witness' regardless of offset; do not treat near-level as a mathematically guaranteed fit. Inspect around X39.68–39.90, Y9.23–11.09, Z20.22–22.08 if a +X rub appears.
3. **Check seat separately.** At true seat, check top Z and repeatable height at both ends, with no rocking under alternate light pressure. An offset path may clear but finish off register; return to actual pilot registration for seating. Measure/report any discrepancy rather than declaring fit from passage alone.
4. **Witness the two M2 shank passages out of the shell.** Record actual screw lot and maximum shank/thread crest diameter with a calibrated micrometer; use a calibrated clean GO pin no smaller than the maximum measured active screw diameter, or document separately that the actual intended screws pass both bores freely without rotating them as a tap. Insert from the assembly side through the entire board thickness and withdraw; no push, cutting or reaming. Also record actual clearance/GO increment where available (a bare handwritten “M2 passed” is not evidence). Test shell pilot engagement and torque separately, using the approved hardware/material procedure; do not push a full Ø2 mm GO pin into the nominal Ø1.640 mm shell pilot. Existing native Ø1.70 mm witness is not a GO result.

**Do not enter PASS without actual results:** source hashes, equipment IDs, calibration shift measured, descent record, seated two-end Z and rock observations, both GO pins or actual screws verified, both separate pilot observations, technician/date and evidence paths. No native slice or physical fit is asserted by this sheet.
