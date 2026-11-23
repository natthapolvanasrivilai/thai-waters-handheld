# R0013 hardware review · 23 November 2026

The CviLux plug withdraws 8.25 mm along its header axis with the display stack seated and the main loom clamped at J8. The engineering configuration pairs enclosure **TW-A-0001-R0013** with electrical installation **TW-A-0002-R0006**. The owner's R20 print is the inert carrier first article on the separate print track. Powered assembly and production release remain open. [Motion viewer download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0013-seated-service-review-1/TW-A-0001-R0013-motion-review.html) · [R20 print and inspection](hardware-review-2026-11-23.md)

## What clears through withdrawal

| Interface | Nominal result | Interpretation |
|---|---:|---|
| Four moving W4 jackets to stationary parts and to one another | ≥0.500 mm throughout | Tested against the final fitted A3, A5, adhesives and modeled fixed leads. Native geometry checked at 133 positions, with motion bounds between positions. |
| Moving SDA jacket to fixed USB lamp conductor | 0.615 mm measured | Closest external wire witness at 4.25 mm of withdrawal. |
| Rigid plug to main W1 bundle | ≥3.156 mm throughout | Lowest measured gap 3.240 mm. The main bundle stays fixed. |
| Rigid plug to other seated surroundings | ≥0.387 mm in the mesh study | A4 is the closest sampled board. The mating header is checked separately. |
| Straight jacket through the plug's terminal lock | 0.040 mm nominal | The 1.42 mm jacket represents the contact drawing's upper diameter. Tooling variation or wire dress can consume the whole gap. |
| Stationary W2 jacket to lamp ground, W7 jacket to spacer | 0.067 mm and 0.090 mm | Keep these points visible during dressing and check for rub before powering the assembly. |

Each lead now has a 5.60 mm straight exit and a controlled bend between the crimp and its stationary tap. The previous SCL dress contacted A5 within the first 0.50 mm of travel. The release includes jacket lengths, fixture coordinates, native contact witnesses and an independent 264-interval mesh study. [Wire forms and native verification](../hardware/electronics/harness-r0006/README.md) · [Motion and negative controls](../hardware/mechanical/TW-A-0001-R0013/README.md) · [USB solder joints and wire fit](../hardware/electronics/usb-entry-r0006/installed-leads/README.md)

In the full viewer, select **Play motion** or drag from **Seated** through **Rocker held** to **Withdrawn**. Hiding the display changes visibility only. The full local file includes the supplier solids. The public viewer ships with the project-owned wire geometry and accepts the matching full file locally. The supplier's connector model omits internal catch detail and shows two small plastic overlaps at the seated position. Actual rocker travel, latch force, access to grip the plug, rubbing, and repeated crimp flex require a complete de-energized sample. [Mating geometry and limits](../hardware/electronics/harness-r0006/connector-clearance.json)

## Board placement and USB

A3 keeps the original mounting datums and connector position. The revised two-layer board moves the driver and passives and corrects the motor polarity marking. J1 clears C1 by 0.230 mm, U1 by 0.860 mm and R1 by 2.530 mm in the placement-rule envelopes. The prior board reproduces the three violations. A3, A4 and A5 report zero schematic, copper, unrouted and parity errors. [A3 layout and plotted copper](../hardware/electronics/pcb-haptic-cie-r0002/README.md) · [Verification and solver traces](../hardware/verification/r0013/README.md)

On an identified Waveshare 3.5B V2, removing LRC4 interrupts the factory bypass. The fitted A5 enables a resistor-limited PMIC path when either USB-C orientation advertises 1.5 A or 3 A. The same 15 Ω load draws **63.529 mA** in simulation, versus **348.837 mA** through the stock path. The two resistor-limited VBUS branches together have a **91.29 mA sustained upper bound** under the specified voltage and tolerance corners. A separate edge test records displacement current from modeled stray capacitance; thermal rise, attach transients, USB compliance and actual pack charging still need measurement. [A5 schematic, BOM, assumptions and test cases](../hardware/electronics/usb-entry-r0006/README.md)

**Charging capability is limited.** An ordinary default-current host can carry battery-assisted USB data. With a qualifying USB-C source, calculated current available at a valid PMIC voltage is approximately 4–20 mA. Real pack current depends on system load and PMIC operation. No-cell startup at the 330 mA test load fails. The VBUS input and two USB-C sense leads still need physical landing coordinates on the incoming controller. Connector-motion clearance applies to the modeled installation. Keep those three new routes out of the service volume and repeat the sweep once measured. [Incoming-board cut and taps](../hardware/electronics/usb-entry-r0006/boundary.json)

The 65 fitted USB simulations produced 189 measurements. Of these, 175 met their limits, five characterize behavior, seven detect deliberately introduced faults and two record the unsupported no-cell startup. An abrupt output short reached 68.04 mA at the host. The 500 pF, 1 ns edge sensitivity reached 2.814 A for a total 3.50 nC in 20 ns. This transient is sensitive to the actual connector, cable and assembly. [Measurements](../hardware/electronics/usb-entry-r0006/measurements.csv)

## First-article record

The owner reports that the R20 parts released intact, with heavy stringing. The carrier-to-floor fit and powered assembly remain open. [First print photographs and illustrated fit check](../hardware/mechanical/pocket-reel-r19b-removal-trial/QA/R20-first-print/README.md)

The R20 carrier check covered 31 component groups with zero positive intersection volumes and zero unresolved solids. The A2 board touches its seat as designed; its populated components clear the carrier by 0.283 mm in the registered model. Both pack envelopes in the R0013 STEP have a closest measured gap of 0.500 mm to the housing. Physical support removal, retention and printed tolerances remain first-article observations.

Record the actual pack and board markings, conductor diameter and dressing against the fixture. Measure the narrow gaps, check the crimp and latch through repeated withdrawal with the display seated, and verify continuity after cycling. Compare the printed carrier to its own fit record. Use a current-limited supply and pack emulator for subsequent electrical qualification after the input cut and cable routes have been verified. [Carrier clearance](../hardware/mechanical/TW-A-0001-R0013/QA/r20-carrier-fit.json) · [Seated STEP and maximum pack](../hardware/mechanical/TW-A-0001-R0013/QA/installed-fit.json) · [Open hardware work](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/13)
