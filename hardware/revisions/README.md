# Hardware revision register

**Current engineering configuration.** TW-A-0001-R0015 pairs the relieved key bay with TW-A-0002-R0006 electronics. [Key installation and physical checks](../mechanical/TW-A-0001-R0015/README.md)

TW-A-0001-R0014 carries A3 directly on two integral floor rails, with TW-A-0002-R0006 electronics. The R20 carrier remains a separate sensor fixture. [R0014 build and fit checks](../mechanical/TW-A-0001-R0014/README.md) · [Prior R0013 seated service review](../../quality/seated-connector-review.md)

Record the exact enclosure and electrical integration IDs on each build traveler. The historical R0008 fit baseline paired **TW-A-0001-R0008** with **TW-A-0002-R0002** (Rev F wiring). Record the firmware version and binary SHA-256 separately. An assembly ID identifies a design configuration. Each physical unit still needs its own serial, option set, incoming part lots and test results.

[R0011 receiver-down fit print](../mechanical/TW-A-0001-R0011/README.md) pairs the existing installed housing surfaces with the revised print definition **TW-P-0001-R0010**. The register keeps a new part revision for the changed print orientation. P17 remains fitted. Physical rail strength, grip fit and support cleanup require an inert print.

[R0010 engineering review](../mechanical/TW-A-0001-R0010/README.md) adds the removable P17 service cover. Its parent enclosure has 17 device print positions and pairs with R0003 electrical integration. The historical [R0009 engineering review, paired with R0003 electrical integration](../mechanical/TW-A-0001-R0009/README.md) includes the dressed cable verification. The register identifies the engineering configuration separately from first-article approval.

## Find a baseline

| Historical label | Enclosure print set | Design evidence |
|---|---|---|
| Rev A | TW-A-0001-R0001 | [Five-part lengthwise mockup](../mechanical/history/Riffle-prototype-A.zip) |
| Rev B | TW-A-0001-R0002 | [Landscape enclosure and edge reel](../mechanical/history/Riffle-Wide-B.zip) |
| Rev C | TW-A-0001-R0003 | [Rear folding reel](../mechanical/history/Riffle-Pocket-C-prototype.zip) |
| Rev D | TW-A-0001-R0004 | [Right-side folding reel](../mechanical/history/Riffle-Pocket-D-mechanical.zip) |
| Rev E | TW-A-0001-R0005 | [Populated controller and encoder fit](../mechanical/rev-E/Readme.md) |
| Rev F | TW-A-0001-R0006 | [Top-edge power key and slide-lock rod grip](../mechanical/rev-F/README.md) |
| Rev G | TW-A-0001-R0007 | [Revised battery pocket, retainer and removable bridge](../mechanical/rev-G/README.md) |
| Numeric baseline | TW-A-0001-R0008 | [Oriented FDM set, two inert gauges and fit checks](../mechanical/TW-A-0001-R0008/PRINT-GUIDE.md) |

All twelve R0008 device print definitions have new STL hashes and revision IDs. Seven installed solids changed shape. Five retain their installed geometry and carry a new controlled print export. The two shop gauges are covered by the print manifest and sit outside the unit assembly membership.

The electrical register includes the R0004 [controller ECO](../electronics/integration-r0004/README.md) and [installed A3 harness definition](../electronics/harness-r0004/installed.json). The R0011 dressed model represents the revised harness on the original controller. Controller ECO layout and powered qualification remain open. [R0003](../electronics/harness-r0003/README.md) documents the preceding connectors and indicator changes. **TW-A-0002-R0001** identifies the [base wiring drawing](../electronics/Riffle-D-wiring.pdf). **TW-A-0002-R0002** includes that drawing, the [top-edge key carrier fabrication files](../electronics/Rev-F-power-key-carrier-Gerber.zip) and the [switch and W3 wiring specification](../electronics/rev-f-power-key.md). The OEM controller's silkscreen revision, purchased part numbers and supplier lots are separate identifiers.

The enclosure register covers the supplied prints, including the detachable grip when supplied. Gauges, fasteners, tapes, bought electronics and optional motor fitment are recorded through the [R0009 prototype BOM](../../sourcing/production-intent/R0009-prototype-budget.csv) for current design review. Historical records include the [fit BOM](../mechanical/rev-G/fit-bom.csv), [production-intent BOM](../../sourcing/production-intent/rev-f-buy-make-bom.csv) and [as-built record](../../manufacturing/rev-F-review/as-built-record.csv). Historical entries identify the files that survive in this repository. Design maturity, fit results and physical acceptance come from the linked evidence.

## Identify an item

`TW-P-0001` identifies the housing family. `TW-P-0001-R0007` identifies the exact Rev G housing definition. `TW-A-0001-R0007` identifies the entire matched print set. The family number and revision counter use decimal integers with a minimum of four digits. After R9999 comes R10000. Each family advances independently and the A in TW-A means assembly. A shared family name describes a function across design changes. Use the exact revision specified by the assembly when selecting replacement parts.

The [assembly register](assemblies.csv) names each configuration, its historical alias, evidence and change records. The [part register](parts.csv) identifies the controlling artifact and SHA-256 for each exact part revision. The [membership register](members.csv) ties an assembly to each part, quantity and actual supplied file, including individual ZIP members. For example, the Rev G housing is TW-P-0001-R0007, the west key retainer is TW-P-0012-R0002 and the bridge is TW-P-0016-R0001. The other nine prints retain their earlier revision IDs. Comparing SHA-256 against both source locations verifies each carry-forward.

Run these commands from the checkout with Python 3.9 or later.

~~~sh
python hardware/revisions/revision.py show "Rev G"
python hardware/revisions/revision.py show TW-P-0012-R0002
python hardware/revisions/revision.py check
~~~

## Allocate the next revision

1. Start from the current register on the target branch. For a new family run `python hardware/revisions/revision.py next part` or `next assembly`. For a changed item use its family, for example `python hardware/revisions/revision.py next TW-P-0012`. This prints a candidate ID. The reviewed registry change allocates it. If another branch merges first, refresh the register and resolve duplicate IDs before merging.
2. Save the changed definition under a new versioned path. Append a row to `parts.csv` with the candidate ID, functional name, source path, optional ZIP member and SHA-256. Hash binary files as supplied, and Markdown with CRLF normalized to LF. An unchanged artifact can be referenced by every assembly using it. Define a new part revision for changes to controlled geometry, material, fabrication or interface requirements. Use a new family for a separately selected item.
3. Allocate a new assembly revision when a constituent revision, quantity or configuration changes. Append its row to `assemblies.csv` and its complete membership to `members.csv`, with exact child revisions and quantities. Provide the design evidence path and applicable IDs from the [change register](../../quality/changes.csv). Leave the historical alias empty for new numeric baselines. Keep published rows and files in place, including withdrawn configurations.
4. Run `python hardware/revisions/revision.py check`. On changes after this register's introduction, add `--against origin/main` or another reviewed commit containing the register to verify that prior records and membership were preserved. Tag the reviewed commit when publishing its engineering release. Record applicable test results, unresolved gates, firmware compatibility and serial/lot effectivity in the [release record](../../releases/README.md).
5. A production approval or field rework needs the engineering decision and its affected units. Record actual components, old and new IDs, disposition and retest against the serial. Follow the [manufacturing gates](../../manufacturing/gates.md) and [service record](../../service/README.md).

[Current playtest, preview firmware and engineering milestone](../../docs/wiki/Software-and-tests.md#current-release)
