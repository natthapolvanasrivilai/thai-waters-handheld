# Firmware, simulator and software verification

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-hardware-review-1/Thai-Waters-handbook.html)

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

The private [phone playtest](https://thai-waters-pocket-angler.shoung0690.chatgpt.site) is Sites version 15, source commit `ebb52eacd05361657ea6013c8f81e641148697fb`. The [standalone simulator](../../game/Thai-Waters-play.html), the hosted game and the [interactive handbook](../index.html) contain the same playable HTML. SHA-256 is `92b1f9f1108c7b42b70128dd875699a44cd5dfabae67dce8ac72d26d156348a6`.

The [0.9.4 USB engineering preview](../../releases/prototypes/Thai-Waters-controller-0.9.4.zip) targets Waveshare 31137. The browser includes all 2,545 individual fish portraits. The hardware package supplies a resident selection and a microSD bank for the full catalog. The game verifies the bank at startup. Read the [board setup and card instructions](../../firmware/Phone-controller.md). The USB package SHA-256 is `75a162efb834e44c53a10159eb66a3f266fe2c4467a5734531a8a5958f18140d` and the matching card bank SHA-256 is `443b7332de79b57a48791ae31def92792fed1c5317274e84ee2dcd6df2c6c4fa`.

The [portrait regression](../../verification/browser-tests/specimen-art.cjs) renders the entire catalog, checks transparency and uniqueness, and compares the reported *Labeo dyocheilus* catch with its journal entry after reloading. The [per-species comparison ledger](../../game/art-source/reference-dispositions.csv) records a non-random sample of 277 illustrations with identified references. All 29 flagged discrepancies have credited corrections. The other 2,268 entries remain outside this visual review. [Artwork assignments and identity-review status](../../game/art-source/coverage.csv) · [Sources and preparing the artwork](../../game/art-source/README.md) · [Recovered-object rendering](../../verification/browser-tests/recovered-items.cjs). On-board card and memory behavior, physical reel feel and phone pairing still require a bench run.

The current inert print is [TW-A-0001-R0011](../../hardware/mechanical/TW-A-0001-R0011/PRINT-GUIDE.md). The [hardware gate](../../quality/hardware-gate.md) tracks electrical limits, harness mating, housing strength and first-article acceptance. Software development resumes after hardware closure.
