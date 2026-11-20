---
name: thai-waters-prototype-release
description: Package and verify private Thai Waters simulator and ESP32 prototype releases and record their evidence.
---

The browser engine shares C++ gameplay with firmware. After changing shared gameplay, rebuild via [build-engine.py](../../../game/build-engine.py) and [build.py](../../../game/build.py). Check actual input, game state, rendered pixels or PCM in the relevant browser and host fixtures. Preserve save compatibility. For physical builds, use the board profile and flash layout documented in the [controller guide](../../../firmware/Phone-controller.md).

Use the existing [USB packager](../../../firmware/tools/package-controller-preview.py) to verify compiled-source fingerprints and image offsets. Distinguish host simulation, ESP32 compilation and physical bench results in release notes. Retain previous packages needed by existing hardware. For art expansions, record the compiled application size against the target OTA slot. The nominal flash capacity also holds the second application slot and the collection filesystem.

The canonical repository is the owner's personal private project. The phone playtest is owner-private. Keep the hardware, sourcing and commercial handbook exclusively in the private project. Check the intended remote and audience before an authorized release. A local build or a staged artifact does not establish deployment. Keep release credentials out of the repository.

For a joint release, compare the SHA-256 of the standalone game with the Sites checkout and embedded handbook. Verify the deployed version and source commit, released firmware package, and registered hardware baseline. Update the [software milestone](../../../docs/wiki/Software-and-tests.md#current-release) and check current download links.

For location audio, keep the stable destination ID, not the fishing pool or menu index, as the score key. Use [the shared renderer](../../../firmware/WillowCreek/LocationAudio.h) on both platforms. Finish the outgoing score's release before starting the new score; never overlap music. Keep water ambience secondary and fishing cues independently controlled. Run [the native PCM check](../../../firmware/tests/location_audio.cpp) and audition representative waters before changing a release. Differentiate actual-renderer auditions from source reference mixes.
