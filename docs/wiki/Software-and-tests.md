# Firmware, simulator and software verification

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/design-review-r0009-1/Thai-Waters-handbook.html)

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

## Current release

The private [phone playtest](https://thai-waters-pocket-angler.shoung0690.chatgpt.site) is Sites version 14, source commit `186567eca779eaeec25cd4d8ac07b5a844808120`. Its game, the [standalone simulator](../../game/Thai-Waters-play.html) and the [interactive handbook](../index.html) embed the same playable build. SHA-256 of the standalone HTML is `b9cb3e9a6089be83bc7bf3db700fc07e1b6545768ca8978b7cac78849e4fafeb`.

The [0.9.3 USB engineering preview](../../releases/prototypes/Thai-Waters-controller-0.9.3.zip) targets Waveshare 31137. The simulator and firmware share the habitat rules and the twelve recovered-object portraits. See the [rendered-image regression](../../verification/browser-tests/recovered-items.cjs), [engine coverage](../../firmware/tests/cast_water.cpp), and [fish artwork status](../../game/art-source/coverage.csv). Actual board, phone pairing and physical feel remain bench milestones.

The released inert print is [TW-A-0001-R0008 with TW-A-0002-R0002 electrical integration](../../hardware/revisions/README.md). The [R0009 engineering viewer and R0003 wiring](../../hardware/mechanical/TW-A-0001-R0009/README.md) are registered for design review. The dressed harness has been checked in CAD; physical checks remain open. Use the [published print and gauges](../../hardware/mechanical/TW-A-0001-R0008/PRINT-GUIDE.md) for the first article. Physical fit and production qualification remain open.
