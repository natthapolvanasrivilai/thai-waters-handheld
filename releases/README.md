# Prototype and production releases

Use the [per-revision constitution and gate](../quality/revision-gates/README.md) for prototype promotion, production promotion and production orders. Engineering checkpoints do not assert readiness.

For new hardware releases, record the numeric assembly IDs, reviewed commit or tag, exact BOM and artifact digests. The [hardware revision register](../hardware/revisions/README.md) resolves a historical label or a part revision to its source. The current inert fit print pairs enclosure **TW-A-0001-R0008** with electrical integration **TW-A-0002-R0002**. Record firmware version and digest, actual accessory fitment, lot/serial effectivity, engineering disposition, evidence and approval alongside those IDs.

Historical builds are in prototypes. Firmware 0.7 is an engineering candidate for PCB 31137 and the Rev E or Rev F enclosure. No production release has been approved. For each promoted build record the Git commit, PCB silkscreen revision, partition layout, binary SHA-256, hardware/API compatibility, tested accessory combinations, regulatory evidence and approver. The populated STEP is gzip-compressed losslessly in the mechanical package.

See the [interactive product documentation](../docs/wiki/Home.md) for aimed casting, snag recovery, moving scenery, build evidence and the Rev F mechanical hold.

[Rev G battery fit print](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/rev-g-fit-print) superseded Rev F for the historical battery fit print. The [print instructions](../hardware/mechanical/rev-G/README.md) identify the three changed STLs, fasteners and inert-gauge checks. That historical release paired Rev F electronics with firmware 0.7.

[TW-A-0001-R0008](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/TW-A-0001-R0008) supplies the current matched 12-part device set, two inert gauges, a 79-component drawing-maximum STEP and the interactive assembly. [Shop setup](../hardware/mechanical/TW-A-0001-R0008/PRINT-GUIDE.md) · [CAD and slicer verification](../hardware/mechanical/TW-A-0001-R0008/QA/README.md). Physical first-article fit, strength and production release remain open.

[Firmware 0.8 prototype](prototypes/Thai-Waters-firmware-0.8.zip) adds manual catch filing, daily specimen tournaments, seasonal weather and the updated LCD. Hardware configuration identifiers are tracked separately in the [hardware revision register](../hardware/revisions/README.md).

[0.9.2 USB controller preview](prototypes/Thai-Waters-controller-0.9.2.zip) · [Compatible board and setup](../firmware/Phone-controller.md) · [Clock and collection recovery](../docs/wiki/Clock-and-saves.md). Internal engineering build for Waveshare 31137 with Rev F sensor wiring. The package includes the firmware, source and verification records.

[0.9.3 USB controller preview](prototypes/Thai-Waters-controller-0.9.3.zip) preserves the earlier software baseline.

[0.9.4 USB controller and field-art card](prototypes/Thai-Waters-controller-0.9.4.zip) includes the complete illustrated catalog. [Current software, hosted deployment and hardware disposition](../docs/wiki/Software-and-tests.md#current-release)

[R0009 / R0003 dressed design review](../hardware/mechanical/TW-A-0001-R0009/README.md) includes the latest candidate viewer, harness checks and one-unit cost. Production approval is pending.
