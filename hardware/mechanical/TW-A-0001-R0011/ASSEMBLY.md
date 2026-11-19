# Dressed R0011 engineering assembly

The R0011 dressed STEP installs the covered enclosure, receiver-down housing geometry and R0004 A3 haptic wiring. The printed housing uses the same installed surfaces as the R0009 design. The print pose lives in the separate fit kit. Units in the assembly are millimetres. Display is +Z, the USB side is −X and the service cover is on the −Y wall.

The STEP retains the original populated controller. The R0004 controller ECO is a circuit design candidate. The recovery bridge and mux, independent control supply, audio attenuation, power-path changes and extra capacitors still require circuit-board placement, closed-case clearance checks and thermal measurements. Consult the [controlled electrical specification and first-article gates](../../electronics/integration-r0004/README.md).

Open the [standalone engineering viewer](../../../docs/models/TW-A-0001-R0011-exploded.html) and select **Harness**. Search for **J1** to inspect the five-way socket, terminals and right-angle header. Select a part and choose **Isolate** to inspect its geometry and source note. Use **Slide lock** to inspect the printed rod receiver. Use the STEP in a CAD application for measurements.

A3 uses the native Würth 61900519521 right-angle header model. The 61900511621 female housing and formed crimp terminals are drawing-derived fit models. Final spring contact, crimp dimensions, latch force and pull retention require the physical parts.

Each revised solid has a source path, hash, installed bounds, solid count and volume in the [STEP component ledger](installed-step.json). The [export check](export-verification.json) compares the reimported compressed STEP with each registered component and records the geometry source notes. The [lower cover check](QA/service-cover.json) measures latch engagement, speaker clearance, rod slide and service-probe reach in the reimported assembly. Manufacturer STEP, drawing-based fit studies and workshop wire routes are identified separately in the [harness manifest](../../electronics/harness-r0004/installed.json).

## Rebuild from the registered components

Use the project CadQuery environment and the R0010 dressed compressed STEP with the hash recorded in its export report. Run in this revision directory.

```text
python assembly.py --reference <R0010-dressed.step.gz> --work <scratch> --exports <exports>
python viewer.py --exports <exports>
```

The viewer uses the R0009 engineering scene, R0010 service-cover BREP and the current harness manifest. The STEP importer verifies the cover, the harness component hashes and each component's geometry after export. Historical battery comparison configurations are available in the viewer. The STEP includes only the registered supplier-cell configuration.
