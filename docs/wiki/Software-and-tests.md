# Firmware, simulator and software verification

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/firmware-v0.8/Thai-Waters-0.8-handbook.html)

Open **Software** in the handbook. Filter by feature to see its implementation, automated coverage and remaining on-device acceptance. Select **Test plan** to follow a validation item to its stage and acceptance criteria.

| Area | Implementation or evidence |
|---|---|
| Physical device I/O, signed OTA, clock and connectivity | [Hardware API contract](../../firmware/Interfaces.md) and [sketch](../../firmware/WillowCreek) |
| Fish behavior, aim, snags, salvage and journal | [C++ phase machine](../../firmware/WillowCreek/Creek.h), [native fixtures](../../firmware/tests), [WASM tests](../../verification/browser-tests/cast-water.cjs) |
| Scenery and period-specific movement | [Shared native animation](../../firmware/WillowCreek/Ambient.h) and [468-scene verification](../../verification/browser-tests/ambient.cjs) |
| Browser, touch, audio and phone motion | [Simulator build](../../game/BUILD.md) and [browser regressions](../../verification/browser-tests) |
| Physical board, flashing and recovery | [Firmware instructions](../../firmware/README.md), [bench guide](../../verification/bench-guide.md) and [build archives](../../releases/prototypes) |

For a bench run, record controller revision, firmware digest, sensor calibration, magnet orientation, motor option and power source. Compare signed forward/backward turns, cast versus lift, touch targets, speaker and bite levels before closing the shell. Native compilation and browser replay cannot establish physical motor feel or power behavior.

[← Read a circuit trace](Electrical-verification.md) · [Test evidence and market readiness →](Validation-and-compliance.md)
