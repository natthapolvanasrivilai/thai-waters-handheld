# Firmware, simulator and software verification

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Download the live handbook](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0013-pcb-assembly-1/Thai-Waters-handbook.html)

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

Open the [private playtest](https://thai-waters-pocket-angler.shoung0690.chatgpt.site) for the hosted game. The signed-in handbook’s build record identifies the deployed source revision, game HTML SHA-256, and successful exact-source workflow. It also distinguishes the tested browser build from the unflashed hardware preview. Use that workflow’s source-matched artifacts and checksums when evaluating an available offline browser or USB controller package; a historical download is not a substitute. Exact workflow evidence does not establish reliable saves in every browser or physical device acceptance.

### Historical builds

The historical [standalone browser download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/engineering-2026-11-20-rayong-thai-90d5c37/Thai-Waters-play.html) in the [engineering prerelease](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/engineering-2026-11-20-rayong-thai-90d5c37) was built from exact source commit `90d5c37e162c118df6563f7836f41cff363edab8`. Game HTML SHA-256: `c0d3904c24587ab0c01dd54400e8857f5e91c213e3b3dd86bae5d83f1d78765b`. [Exact-source verification](https://github.com/natthapolvanasrivilai/thai-waters-handheld/actions/runs/44756393230). This is not a record of the current hosted game.

This version-controlled product wiki is the canonical documentation. The [live handbook](../index.html) opens on current project status. Its playable demo preserves the R0011 engineering snapshot. A documentation-only Site update can change the Site's version without changing the game HTML.

The [USB engineering preview for that historical release](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/engineering-2026-11-20-rayong-thai-90d5c37/Thai-Waters-controller-90d5c37.zip) compiles for the Waveshare 31137, Rev F sensor pinout, with Arduino-ESP32 3.3.10. The offline integrity check passed for the four ESP32-S3 images and the SD art file. The USB package SHA-256 is `25bb91275b186bf3e09b800be4c705003a3d054400ee649a74f8a59ae3bf54d9`. The [earlier 0.9.4 package](../../releases/prototypes/Thai-Waters-controller-0.9.4.zip) remains an archive, not the matching build. The browser includes 2,545 individual fish portraits; the controller uses a resident selection and a checked microSD bank for the full catalog. See the [board setup and card instructions](../../firmware/Phone-controller.md).

### Browser feature reference

- **Thai Rayong ray label:** in Thai browser mode, specimen 1433 (*Taeniura lymma*) displays as **ปลากระเบนทอง**. After it has been collected, **ปลากระเบนหางพัดจุดฟ้า** also finds it in the collection. This is a [source-backed label and search alias](https://github.com/natthapolvanasrivilai/thai-waters-handheld/blob/90d5c37e162c118df6563f7836f41cff363edab8/game/content/thai-specimen-labels.md#rayong-pilot-label-50), not a change to specimen ID, art, encounter odds, save data, or controller firmware.
- **Local career and backups:** the browser keeps one local angler career. From **Menu → Rod workshop → Career & backups**, export a backup before changing devices or clearing browser data. Choose a backup file to preview it, then use **Replace career from backup** only if you mean to replace the current browser save. No cloud sync or controller save transfer.
- **Fish collection:** swipe left or right within an open fish detail to move between entries. **Back** still returns to the collection.
- **Optional HQ pilot:** add `?fishArt=hq` to the browser game URL to try five source-resolution portraits in eligible details and catch cards. The ordinary portraits remain the default. This does not change controller or microSD artwork.

The [portrait regression](../../verification/browser-tests/specimen-art.cjs) renders the entire catalog, checks transparency and uniqueness, and compares the reported *Labeo dyocheilus* catch with its journal entry after reloading. The [per-species comparison ledger](../../game/art-source/reference-dispositions.csv) records a non-random sample of 277 illustrations with identified references. All 29 flagged discrepancies have credited corrections. The other 2,268 entries remain outside this visual review. [Artwork assignments and identity-review status](../../game/art-source/coverage.csv) · [Sources and preparing the artwork](../../game/art-source/README.md) · [Recovered-object rendering](../../verification/browser-tests/recovered-items.cjs). On-board card and memory behavior, physical reel feel and phone pairing still require a bench run.

The current hardware engineering study pairs R0013 mechanics with R0006 electronics. It covers the seated-display harness, A3 haptics and USB source limits. R20 is the separate inert carrier print trial. Hardware acceptance awaits physical fit and powered measurements. [Hardware review](../../quality/seated-connector-review.md) · [R20 first-article print procedure](../../hardware/mechanical/pocket-reel-r19b-removal-trial/README.md) · [Hardware gate](../../quality/hardware-gate.md)
