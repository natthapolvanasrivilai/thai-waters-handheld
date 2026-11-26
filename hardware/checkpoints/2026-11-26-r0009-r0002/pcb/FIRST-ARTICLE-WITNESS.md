# FA-01 | Pocket Reel paired hardware fit witness | NOT RUN

Gate: TW-A-0003-R0009 shell/kit plus TW-A-0004-R0002 populated board only. Registered shell STEP SHA-256 `dbea143bbe452069f60fbcec954038f8abf357c15469f1030fbab4adc392f0ce`; populated board STEP `123265be74fc5d84e8817ae4a1db8584747d31dea9e75454d0bd53beed9024ac`. Match the route/loop register for W4 (do not substitute W2). This record is a future witness instruction, not a request to print, build, energize or move hardware now.

## Before the witness

- Record serial/lot or trace ID for each mating part, populated board revision, plug/terminal and cable lots, shell plate file hash and print lot, actual fastener/driver identity, operator, date and evidence folder. Record cable dressing, solder fillets and any deviations as photographs before moving anything.
- Use battery physically absent and USB unplugged. No live continuity/power tests in this sheet. Do not force a plug, wire, boss, driver, or shell.
- Match the CAD hard datums: board seat plane plus both mount axes (123.0,99.6 and 97.5,117.9 mm in KiCad, NOT shell coordinates). Use the registered assembly transform and confirm orientation against the USB opening. Record physical seating and both axis positions before any clearance run.
- Record each instrument ID/calibration date, reference standard and before/after reference readings. Use calibrated pin/optical metrology appropriate to each feature; record repeatability, alignment and instrument uncertainty. Unresolved calibration or occluded line of sight is HOLD, not zero. Capture the assembly and setup in every image series.

## Witness order and evidence

| ID | Action | Required record and decision |
|---|---|---|
| FA-01A | Measure first article before closure | Board seating and axes; retained hole GO by accepted M2 plan; measure mounted protrusions absent from STEP (solder, strain relief, actual fastener). Log sign/direction toward W4. Do not reclassify a nominal STEP feature as extra closure. |
| FA-01B | Verify registered travel unloaded | Observe W4 VCC/SCL/SDA/GND at rest, during full modeled 8.25 mm withdrawal and re-insertion. Resolve the 0.125–0.1875 mm early-window region specifically but do not assume it is the physical minimum. Record calibrated travel and non-contact measurements where visible, min candidate + pose + video frames; repeat in both directions without redressing and record hysteresis. Assess plug body/latch, other harnesses and covers separately. |
| FA-01C | Check tool and closure sequence | Inspect both mount positions using the actual driver and fastener envelopes and documented assembly/service order. Log hand/tool access and any interference; observe cover-insertion and closure with all fixed wires dressed and record any displacement/imprint. Where closed geometry is inaccessible, use approved registered measurement access or retain HOLD; a successful click or video alone does not measure clearance. |
| FA-01D | Compute and retain interval and uncertainty ledger | Log max jacket OD per net, unknown populated protrusion, datum shift, extra harness motion/springback, readout uncertainty, source/photo/calibration refs and sign conventions. Replay native full sweep with measured bounds and registered populated assembly; retain all minimum pairs and unresolved intervals. If measuring gap directly, lower bound is observed gap minus expanded measurement uncertainty; do not combine a direct gap and model closure debits as though independent measurements of the same gap. |

### Decision rule

For the **W4-to-board only** registered continuous replay, reserves above 0.500 mm are VCC 0.087969, SCL 0.276390, SDA 0.577751, GND 0.548712 mm. Per net, debit half the positive excess of maximum jacket OD above 1.42 mm, relevant nonnegative extra protrusion, datum shift, extra harness movement and independent uncertainty exactly once. The modeled numerical allowance of 0.050 mm is already included. Unknown, failed registration, unobserved continuous intervals or inability to verify an independent closure contributor are HOLD. An interference is FAIL; do not force or waive it. A per-pair measured/replayed lower bound below 0.500 mm does not pass. Do not extend the W4 budget to the actual plug, other wiring, covers, or driver interfaces. A nominal first article is not a production tolerance qualification.

Retain `01_trace/`, `02_calibration/`, `03_unpowered_fit/`, `04_motion_and_closure/`, `05_raw_measurements/` and `06_decision/`. Record overall HOLD until metrology, full affected pairs, native electrical checks and any separately authorized physical electrical validation are complete.
