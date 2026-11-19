# Thai Waters product wiki

[Hardware closure and playtest issues](../../quality/hardware-gate.md) · [Open the private tracker](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1)

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/firmware-v0.9.4/Thai-Waters-handbook.html)

This handbook follows a unit from a cast on the simulator through component selection, enclosure fit, programming, factory acceptance and sale. Start with the activity below, or [download the interactive handbook](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/firmware-v0.9.4/Thai-Waters-handbook.html). Open the downloaded HTML in a browser. The playable game, 3D meshes, circuit traces and costing data are embedded. A local copy is also available at [docs/index.html](../index.html) in your checkout.

**Current design review.** [R0009 dressed assembly and R0003 harness](Hardware-and-3D.md) · [One-unit BOM and selling price](BOM-and-business.md)

**Build disposition · TW-A-0001-R0008 is the next inert fit print.** The print set preserves both maximum battery envelopes. Follow the [R0008 orientation, support and gauge procedure](../../hardware/mechanical/TW-A-0001-R0008/PRINT-GUIDE.md) before powered closure. The rail transient, shared I²C bus, speaker drive and charger behavior have outstanding measurements. Check [electrical verification](Electrical-verification.md) and [mechanical fit](Hardware-and-3D.md) before closing a powered case.

[Current software release, playtest and hardware milestone](Software-and-tests.md#current-release)

## Table of contents

1. [Play and evaluate a cast](Game-and-demo.md)
2. [Inspect the assembly and battery pocket](Hardware-and-3D.md)
3. [Read a circuit trace](Electrical-verification.md)
4. [Firmware, simulator and software verification](Software-and-tests.md)
5. [Test evidence and market readiness](Validation-and-compliance.md)
6. [Build, record and service a unit](Factory-and-service.md)
7. [Source parts, cost a batch and plan the launch](BOM-and-business.md)

[Clock retention and collection recovery](Clock-and-saves.md)
