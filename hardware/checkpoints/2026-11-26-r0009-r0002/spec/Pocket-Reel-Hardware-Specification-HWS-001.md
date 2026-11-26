# Pocket Reel hardware specification
**HWS-001 · Revision 0.3 · 26 November 2026 · Engineering hold**

Use the matched **TW-A-0003-R0009 enclosure** and **TW-A-0004-R0002 rectangular combined control/USB board** as the baseline for the next engineering iteration, not as a fabrication release. Freeze electrical and mechanical interfaces together. Software development is paused; a pinned firmware image is only a future bench fixture.

## 1. Controlled configuration

| Assembly | Baseline | Evidence and disposition |
|---|---|---|
| Handheld system | 480 × 320 display, reel/encoder, controls, haptics, speaker, protected rechargeable pack, USB-C and one RGB window | Preserve the single active diffuser; do not reintroduce obsolete light pipes. The window does not prove RGB electronics work. |
| Enclosure | TW-A-0003-R0009; registered editable STEP, direct tessellation, eight X1C plates/27 objects | Reopen and slice evidence is digital only. Baseline X1C 0.4 mm, PolyTerra PLA/SuperTack. Material-specific future profiles must be separately qualified. Preserve approved rod profile, 45° housing orientation and mating datums unless requalified. |
| Combined board | TW-A-0004-R0002, A4/A5 combined; 32.4 × 35.8 mm, R1.5 corners, two Ø2.30 mm mounting holes | Routed native KiCad exists. Original KiCad 10.0.8 reports zero configured errors with some checks ignored; independently repeat with exact libraries/version and disposition ignored checks. |
| Main controller | Waveshare 31137 A1 family; exact installed variant, copper lands and accessible nets pending | The stock board does not implement the power ECO. Identify the real populated variant and ground the choice of supplier revision or interposer. No assumptions about accessible nets. |
| Other boards, harness, battery | Pin exact A2/A3, B1, plugs, terminals, crimp, wire and retention to the matched manifest | Capture manufacturer source/alternate, drawings and as-installed geometry; prove accessible routing, strain relief, removal and fullest allowable battery envelope. |
| Prior print evidence | R19b withdrawn; R20 and earlier R0011–R0017 independent evidence only | R20 reported intact removal and carrier dry fit, but stringing remained. It does not qualify the R0009 kit, complete fit, board retention or cosmetics. Do not mix old geometry/projects or resend rejected files. |

### Baseline verification

The exact combined-board review found the same non-outline PCB primitives in R0001 and R0002: 50 footprints, 298 tracks and 34 vias. R0002 changes the board edge and mounts, not the electrical topology. The two mounting apertures and closed edge were independently checked against the PCB. The PCB has 30 component STEP models, seven generic wire models and 13 bare solder lands. W106 is a spare land: verify that the populated STEP excludes its generic wire body or represents it explicitly as a keepout.

The first electrical design decision is whether to use an identified supplier variant or a qualified interposer. Establish that with actual A1 revision and measured land access. The first mechanical decision is which support changes avoid visible scars and fractured small features without moving the registered fit. Neither decision is final.

## 2. Electrical and PCB gates

| Gate | Requirement and evidence to close |
|---|---|
| E01 · System inputs | Confirm physical A1 board revision, PMIC and connections; exact keyed B1 pack/terminal and approved battery states. Capture unpowered continuity, polarity and switchable/always-on rail map. Record BOM and DNP variants. Never trace-cut an unverified board. |
| E02 · Power and charging | Preserve verified source-current, cell/thermal, off-state and reverse-feed bounds; test both USB-C orientations and approved source classes. Existing simulations fail the 3.9 V no-battery input floor at the 330 mA request. Batteryless startup or programming is not qualified. Test bounded faults with a battery emulator under supervision, not a live pouch. |
| E03 · Routing and recovery | Qualify USB pair routing/return and impedance against actual stackup; programming entry, preboot grant-loss behavior, straps, rail isolation and connector orientation. Verify installed cable envelope and service movement, then record enumeration/flash checksum only in an approved bench run. |
| E04 · Rails and peripherals | Verify Fast-mode I²C rise ≤300 ns on the populated assembly, with valid VOL/sink current and both bus-end captures. Cover cold start, charge/radio/audio/haptics, encoder coexistence and rail droop under worst intended simultaneous load. |
| E05 · User hardware | Specify measured display/optical alignment, speaker and haptic loads, encoder and key/reset timing, diffuser/LED drive, acoustic and thermal performance. Validate fitted unit rather than attributing simulation or visual animation to hardware. |
| E06 · Release PCB | Freeze the schematic, netlist, routing and placement with exact MPNs, footprints, measured component heights and assembly keepouts. Run same-version ERC/DRC with zero unwaived findings; sign intentional waivers and check pin parity. Deliver KiCad sources, exact STEP, fabrication/assembly outputs, BOM, placement file and test plan only after digital review. |

### Immediate electrical blocker

At the 4.75 V source corner, the present 62 Ω ±1% protected path can supply at most **13.85 mA** above a 3.9 V input floor, even before other voltage drops. The 330 mA condition would require no more than **2.58 Ω** on that simplified budget and therefore cannot be solved by calling the current input path finished. Do not remove the protection resistor to force a pass. Review a separate protected, battery-independent recovery path after actual A1 landmarks, component heights, access and topology are confirmed. Qualification still requires measured behavior under approved source conditions.

## 3. Assembly/FDM gates

| Gate | Requirement and evidence to close |
|---|---|
| M01 · Exact geometry | Use shared datums for PCB, shell, grip/reel, display and closure. Use supplier/received models for plug bodies, populated heights, fasteners, including all protrusions, and dressed wire/battery envelopes. Measure continuous insertion and removal in the occupied assembly; include tolerance-expanded sweeps. |
| M02 · Retention and service | Prove lid lateral location, bezel and cover retention, reel lock and release, glass clearance and all driver corridors including H1-3 beside rod receiver. Moving CviLux VCC (not stationary W2) bounds: original PCB 0.441 mm vs a 0.500 mm gate; exact inert-gauge 8.25 mm sweep ≥0.550 mm. Populated sweep with tolerances remains open. |
| M03 · Tiny and thin features | Audit each load-bearing hole, hook, key, boss and wall against actual per-layer X1C extrusion. Target two continuous lines where a critical wall must carry load; require a separate coupon for any intentional single line. Long or thin parts need self-supporting geometry, controlled orientation and repeated handling tests. |
| M04 · Overhangs and supports | Replace unnecessary supports with verified backing/fillets/ramps where fit allows. Inspect support-dependent starts, bridge backing, detached islands and physically reachable removal. Prioritize rod grip, housing shelf, rotor lip and crank stem. Compare alternative native slices against exact R0009 baseline before dropping supports. |
| M05 · Cosmetic finish | Define customer-facing surfaces. Keep seams and supports off them where possible. Verify unaltered as-printed close-ups for scars, stringing, hollow/closed holes, curl and visible defects under consistent lighting. No sanding or retouching as proof. |
| M06 · Native project and fit | Hash source CAD and editable 3MF, reopen and slice all critical plates. The native inert gauge has a Ø1.70 mm clear core, not M2 passage proof. Entry-relief trial keeps Ø2.30 mm and 1.25 mm web; coupon spans Ø2.30–2.60 mm. Both await native slice and screw trials. Keep shell pilots separate. |

### First measured DFM priorities

R0009 retained native slice: rod grip support **5,822.958 mm³** (35.44% of model volume); housing support **3,731.207 mm³** with eight support-dependent starts, and a **256.687 mm² first-layer bed footprint**; rotor **908.2 mm³** (44.33%); crank stem **78.579 mm³** (39.32%). Use these recorded baselines when testing less support without weakening details or moving mating geometry. Support-to-surface contact is not measured. Prioritize the housing USB flanks, receiver and status opening for visual and removal checks.

## 4. Release gates and handoff

1. **Lock inputs:** reconcile exact board/controller/connector/pack variants and same-assembly BOM. Mark unmeasured interfaces open.
2. **Digital verification:** close E01 design evidence, E02–E06 simulation and CAD checks, M01–M05 tolerance and toolpath checks. Independently verify one matching release manifest: native KiCad and STEP, BOM, 3MF, assembly and verification notes.
3. **Unpowered first article:** compare intended geometry with received/printed measurements. Photograph every critical interface, connector and tool clearance and check print/removal/retention. Keep physical evidence separate from simulation or animation.
4. **Controlled bench:** use the pinned EV matrix and an authorized trained operator, current-limited supply and calibrated instruments. Record exact board serial/revision, conditions, raw waveforms, uncertainties and dispositions. No power, battery connection, flash or fabrication until expressly approved and prerequisites are met.
5. **Release:** close all acceptance rows with evidence and independent review. Ship no production or print-ready claim from a paper specification, a digital pass, or one fit result.

**Primary records:** [hardware review #98](https://github.com/natthapolvanasrivilai/thai-waters-handheld/pull/98), [controller implementation #13](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/13), [first article #12](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/12), [print defects #17](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/17) and [bench matrix](https://github.com/natthapolvanasrivilai/thai-waters-handheld/blob/1ad2acfc12e6e26c4460f49fdc806f7193284330/hardware/verification/circuits/bench-matrix.csv).
