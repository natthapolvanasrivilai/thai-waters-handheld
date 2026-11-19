---
name: thai-waters-hardware-verification
description: Change the physical Thai Waters handheld, select prototype components or verify mechanical and electrical revisions.
---

Start with the [revision register](../../../hardware/revisions/) and the current assembly's [hardware handbook](../../../docs/wiki/Hardware-and-3D.md). Use the controlled numeric revision for new work and retain legacy labels for traceability. Confirm purchased part number, vendor CAD, source dimensions and maximum envelope before declaring fit. Identify unresolved model or tolerance gaps.

Check the battery at its maximum specified dimensions, wire exits, bend space, connector access, screws, reel deployment, grip retention and power key in the assembled and exploded views. Check build orientation, teardrop horizontal bores, underside angles, clearance and support needs against the actual print configuration. Link fit results to the print files they exercised.

For electrical changes, start from [electrical verification](../../../docs/wiki/Electrical-verification.md). Retain the circuit deck, component model assumptions, test corners, limits and results with the revision. Distinguish simulation from measured bench performance. Update impacted BOM rows, assembly steps and [validation evidence](../../../docs/wiki/Validation-and-compliance.md) when a change alters them.

For wired assemblies, validate installed cable solids through the mating contact, document cavity orientation and distinguish a nominal solder joint from unintended interference. Inspect the closed case, adjacent loom and service stroke. Publish the CAD clearance report alongside the [harness assembly instructions](../../../hardware/electronics/harness-r0003/README.md). Price the exact cable and terminated pigtails shown.

For a closed-case opening, identify its function on the assembled STEP and measure both wall faces. Check closure over the full aperture and at allowed fit offsets. Verify snap retention, neighboring components, open service-tool travel and any separate acoustic path. Render the installed and removed part from the same exterior view and slice the exact released mesh. The [lower-edge service cover](../../../hardware/mechanical/TW-A-0001-R0010/README.md) records the procedure and physical fit checks.
