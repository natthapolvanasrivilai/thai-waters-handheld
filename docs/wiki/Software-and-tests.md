# Firmware, simulator and software verification

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Archived interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-hardware-review-1/Thai-Waters-handbook.html)

Open **Software** in the archived R0011 handbook for that engineering snapshot. Filter by feature to see its implementation, automated coverage and remaining on-device acceptance. Select **Test plan** to follow a validation item to its stage and acceptance criteria.

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

The verified [private phone playtest](https://thai-waters-pocket-angler.shoung0690.chatgpt.site) serves the game from exact source commit `cf0d4d262e966444d070495352d80750607c4fb3`. Its game HTML matches the [standalone browser download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/engineering-2026-11-20-large-reel-cf0d4d2/Thai-Waters-play.html) in the [engineering prerelease](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/engineering-2026-11-20-large-reel-cf0d4d2). Game HTML SHA-256: `620609d7c67de439f7e080c2c8a22bd6c881c2cc65b4ff2371953c8042aa3d9d`. [Exact-source verification](https://github.com/natthapolvanasrivilai/thai-waters-handheld/actions/runs/44733552963).

This version-controlled product wiki is the canonical documentation. The [archived interactive handbook](../index.html) has its own embedded simulator and is not the current phone build. A documentation-only Site update can change the Site's version without changing the game HTML.

The [USB engineering preview for this release](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/engineering-2026-11-20-large-reel-cf0d4d2/Thai-Waters-controller-cf0d4d2.zip) compiles for the Waveshare 31137, Rev F sensor pinout, with Arduino-ESP32 3.3.10. The offline integrity check passed for the four ESP32-S3 images and the SD art file. The USB package SHA-256 is `898a51c4647215fcd7ad112ab18fd808c3d8117710245fb36d84273971f28672`. The [earlier 0.9.4 package](../../releases/prototypes/Thai-Waters-controller-0.9.4.zip) remains an archive, not the matching build. The browser includes 2,545 individual fish portraits; the controller uses a resident selection and a checked microSD bank for the full catalog. See the [board setup and card instructions](../../firmware/Phone-controller.md).

The [portrait regression](../../verification/browser-tests/specimen-art.cjs) renders the entire catalog, checks transparency and uniqueness, and compares the reported *Labeo dyocheilus* catch with its journal entry after reloading. The [per-species comparison ledger](../../game/art-source/reference-dispositions.csv) records a non-random sample of 277 illustrations with identified references. All 29 flagged discrepancies have credited corrections. The other 2,268 entries remain outside this visual review. [Artwork assignments and identity-review status](../../game/art-source/coverage.csv) · [Sources and preparing the artwork](../../game/art-source/README.md) · [Recovered-object rendering](../../verification/browser-tests/recovered-items.cjs). On-board card and memory behavior, physical reel feel and phone pairing still require a bench run.

The current inert print is [TW-A-0001-R0011](../../hardware/mechanical/TW-A-0001-R0011/PRINT-GUIDE.md). The [hardware gate](../../quality/hardware-gate.md) tracks electrical limits, harness mating, housing strength and first-article acceptance. The engineering playtest does not clear the production hardware hold. The current firmware has not been flashed or physically accepted as part of this release.
