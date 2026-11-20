# R0004 controller implementation gate (issue #13)

**Disposition: engineering review only.** This review does not change the R0004 circuit, the R0011 enclosure model, or the powered-prototype hold. It does not approve rework, fabrication, buying parts, or applying power.

## Decision to make before PCB layout

Use a **revision-controlled A1 supplier spin as the reference route**. Keep an **interposer as a conditional fallback**, not a drop-in connector board. The native USB path and the PMIC input are both part of the stock controller. The proposed fallback is viable only if it can independently isolate both without sacrificing reset/BOOT access, protection, or fit. If either path cannot be cleanly intercepted on the identified board, reject the interposer route rather than designing around an assumed test pad.

Waveshare lists SKU 31137 for the 3.5B. Its [hardware compatibility note](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B#esp32-s3-touch-lcd-35b) describes newer board changes to the power-button circuit, VBUS filtering, backlight driver and layer stack. The [public schematic](https://files.waveshare.com/wiki/ESP32-S3-Touch-LCD-3.5B/ESP32-S3-Touch-LCD-3.5B-Schematic.pdf) is useful for topology, not proof of pad placement, rework access, or stuffing on the received lot. Match the exact SKU, silkscreen, assembly photos and supplier schematic/layout revision. Do not transfer net or designator assumptions from the non-B 3.5 board. Do not assume a firmware-compatible board is hardware-equivalent for this change.

## Signal-access worksheet

“Open” means physical access and behavior on the received assembly are not verified. The location column identifies functional points, not validated solder pads. EC IDs refer to [first-article.csv](first-article.csv); their existing acceptance limits are unchanged.

| Interface | Functional points to document | Evidence needed before layout or disposition | Gate |
|---|---|---|---|
| Board identity and native bus | A1 SKU, revision and stuffing; switched 3.3 V, SDA/SCL and returns across A1/A2/A3 | Matched drawing, lot photo, pull-up inventory, branch capacitance assumptions and evidence that the removable harness does not own the only pull-ups | Open, EC-01/09 |
| Raw versus limited USB power | Receptacle VBUS, blue indicator feed, first filter/protection parts, PMIC VBUS and every other raw load | Revision-specific connector-to-PMIC net map plus proof of a complete path break with no parallel bypass or backfeed. Record whether an intercept exists without destructive modification | Open, EC-03/04/09 |
| USB data and connector orientation | Both physical CC contacts, connector D+/D−, protection and series network, native USB pair, recovery mux | Matched schematic/PCB and pair access; independent CC paths and return reference. Sketch cable and pair stack-up; no unterminated branch assumed acceptable. Capture both orientations in bench plan | Open, EC-02/03/09/11 |
| ROM recovery and inhibit | Service BOOT, GPIO0/GPIO46 strap state, ESP_EN/reset, UART0 RX/TX, bridge grant and target isolation | Verify physical access and default strap state with stock hardware. Document state table across no pack, no grant, reset, suspend and grant loss, including absence of UART back-power | Open, EC-03/04/11 |
| Key and always-on domain | W3, K3 raw, PMIC PWRON and source/reference for the proposed buffer | Match pull-up and stock key behavior on this revision. Identify the candidate domain with USB only and battery only; unknown power-off behavior blocks release | Open, EC-07 |
| Pack, rail and load gating | Protected J7, regulator output, distributed loads and individually interruptible enable or feed paths | Identify which loads are truly independent of firmware. Document off-state defaults, isolation, regulator capacitance limits, thermal/inrush assumptions and evidence that charging is independent of the run latch | Open, EC-05/06/10 |
| Speaker | Two floating amplifier legs and J9 connector | Verify which series points can be added without altering ground or I²S, and reserve copper/volume for the resistor pad. Sound level and heat must still be measured | Open, EC-08/09 |
| Mechanical and service fit | PCB/connector stack, display underside, closed cover, actual wire exits and antenna boundary | Matched populated STEP or measured maximum envelope, enclosure clearance and plug/tool travel; R0011 does not contain the controller ECO. Do not use nominal empty volume as release evidence | Open, EC-09 and issue #2 |

## Cloud work package and handoff

1. Populate the worksheet with revision, source drawing page, schematic net and physical reference for each path. Label each entry **documented**, **unpowered measurement required** or **not accessible**. Capture exact material gaps in the supplier request; this document is not a sent request.
2. Choose the supplier spin only after a matching interface package is available. Evaluate the interposer only if complete raw power and native pair isolation plus hardware inhibit can be documented, and the assembled envelope is plausible. An unknown is not a pass.
3. On the chosen route, complete the [candidate BOM](bom-delta.csv), including exact logic, isolation/buffer parts, footprints, tolerance and placement evidence. The `U_GRANT and load controls` and recovery-mode latch/UART isolation rows are not orderable BOM selections. Review with the existing R0004 [design record](README.md) before generating any PCB or fabrication files.
4. After actual net and layout evidence, rerun the [verification](verify.py) on the fitted network. Preserve historical failure cases and thresholds. Correlate with [issue #4](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/4) and the [first-article gates](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/12); no model output is a bench pass.

**Current gate:** no identified A1 lot/layout, no proven interposer access, and no verified exact control-logic package or closed-case fit. Proceedings remain limited to engineering review and unpowered identification by qualified personnel. No firmware, BOM, CAD, or simulation evidence is changed by this worksheet.

