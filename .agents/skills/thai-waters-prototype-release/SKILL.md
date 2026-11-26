---
name: thai-waters-prototype-release
description: Package and verify private Thai Waters simulator and ESP32 prototype releases and record their evidence.
---

The browser engine shares C++ gameplay with firmware. After changing shared gameplay, rebuild via [build-engine.py](../../../game/build-engine.py) and [build.py](../../../game/build.py). Check actual input, game state, rendered pixels or PCM in the relevant browser and host fixtures. Preserve save compatibility. For physical builds, use the board profile and flash layout documented in the [controller guide](../../../firmware/Phone-controller.md).

Use the existing [USB packager](../../../firmware/tools/package-controller-preview.py) to verify compiled-source fingerprints and image offsets. Distinguish host simulation, ESP32 compilation and physical bench results in release notes. Retain previous packages needed by existing hardware. For art expansions, record the compiled application size against the target OTA slot. The nominal flash capacity also holds the second application slot and the collection filesystem.

Publish engineering work to the owner’s designated personal repository under its currently authorized visibility. Keep the hardware, sourcing and commercial handbook in that project. The phone playtest has its own audience. Verify the owner, remote, audience, uploaded revision and asset digests before reporting a release. Keep credentials out of the repository.

For a hardware or software status change, update the [current project record](../../../docs/wiki/Current-status.md) and keep the live handbook download reachable. Follow the [handbook release procedure](../../../docs/handbook/README.md) when changing its reader or packaging a new offline edition. Verify the downloaded copy opens the designated GitHub revision and displays its saved release date when offline.

When releasing a 3D assembly guide, build the standalone HTML before embedding it in the offline handbook. Link the release asset from the current project record so earlier live readers can find it. Compare the embedded bytes with the released standalone file, exercise the guide offline, and check the archived controls through the same handbook.

For a joint release, compare the SHA-256 of the standalone game with the Sites checkout. Verify the deployed version and source commit, released firmware package, and registered hardware baseline. Verify an archived handbook simulator against the historical build identified in its tab. Update the [software milestone](../../../docs/wiki/Software-and-tests.md#current-release) and check current download links.

For location audio, keep the stable destination ID, not the fishing pool or menu index, as the score key. Use [the shared renderer](../../../firmware/WillowCreek/LocationAudio.h) on both platforms. Finish the outgoing score's release before starting the new score; never overlap music. Keep water ambience secondary and fishing cues independently controlled. Run [the native PCM check](../../../firmware/tests/location_audio.cpp) and audition representative waters before changing a release. Differentiate actual-renderer auditions from source reference mixes.

For catch music, Bite and Fight feed one continuous action score. A live catch edge may trigger a single rarity cadence, then return to the current location or action. Never replay a restored or already filed catch. Preserve independent bite and reel feedback, visual-only cues, and the legacy landing tone when music is off. Run the [catch music PCM check](../../../firmware/tests/catch_music.cpp) and [native adapter interruption check](../../../firmware/tests/catch_music_adapter.cpp) alongside the location check.

### Optional Windows Solo package

Use [the Solo packager](../../../verification/solo/pack.py) with the approved browser ZIP, its trusted SHA-256 and the exact full release commit. Run `python -B -m unittest discover -s verification/solo -p test_pack.py`, then `python -B verification/solo/pack.py build --browser BROWSER.zip --browser-sha256 BROWSER_SHA256 --source FULL_RELEASE_SHA --output Pocket-Reel-Solo.zip`; use the same arguments with `verify` to check the output before Windows testing. Package verification is not release approval. Require the existing exact-source release gates and supplemental disposable Windows proof of fixed-origin restarts, backup/explicit restore, collision refusal, and separate direct-file Recovery. Follow [the launcher instructions](../../../verification/solo/README.txt); never migrate or replace a career automatically.
