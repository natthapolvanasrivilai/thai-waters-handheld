# Clock retention and collection recovery

| Resource | Owner and current behavior |
| --- | --- |
| Civil clock | The 31137 board has a PCF85063 and an AXP2101. Use the dedicated SH1.0 RTC backup connection for a rechargeable backup cell. The normal pack supplies the clock while available. The board stores UTC. The display converts to Bangkok time. |
| Clock validity | Firmware checks the oscillator-stop flag and initialized marker at boot. When invalid it shows **Clock needs sync** until Wi-Fi SNTP succeeds. A manually selected fishing period is a gameplay condition, independent of civil time. Preserve unknown capture times explicitly. |
| Handheld progress | The original collection and upgrade ranks live in ESP32 nonvolatile storage. Extended fish entries use alternating checksummed flash pages with generation numbers and read-back checks. Powering down requires no battery to retain committed flash. A full-chip erase removes locally stored saves. |
| Private phone playtest | A browser save contains the journal, counts, gear and pending catch. The browser commits them together under the existing save key. A landed fish waits for confirmation even after reload. New confirmed history records have a stable ID, UTC epoch milliseconds, water, period, weather and bait/depth. A browser-profile reset can erase this copy. |

## RTC backup production requirement

BT2 is a required second energy source for the shipping design. The Waveshare board guide identifies resource 17 as the SH1.0 rechargeable RTC battery connection. Confirm the populated connector or pads, pin 1 and reference voltage on the delivered board revision. Qualify one insulated, keyed, removable assembly against the charger voltage/current limits of its cell, including with USB attached and with the main cell disconnected. Keep it retained inside the screwed enclosure and route its lead outside the reel path and main pouch compression envelope. Obtain the exact part's 3D model, STEP envelope and maximum wire length before releasing its pocket or ordering the production lot. Purchasing status is **engineering hold** pending these records. A primary CR cell is unsuitable for this rechargeable connection. [Waveshare board guide](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B)

| Prototype check | Acceptance evidence to record |
| --- | --- |
| Clock rail | Identify backup polarity with a meter. Measure normal, charge, pack-absent and RTC-only voltages and currents. Compare with the exact cell and board specifications. |
| Main pack depleted or removed | Set UTC by SNTP, turn Wi-Fi off, disconnect USB and the main pack. Compare the RTC with an external clock at one hour, 24 hours and seven days. Proposed room-temperature prototype target is seven days with drift under 60 seconds. Record temperature, oscillator-stop flag, and applied supply transitions. |
| Both power sources removed | Restore main power offline. The firmware must declare clock loss or demonstrate valid holdover. Reconnect Wi-Fi and confirm UTC/Bangkok day rollover. Journal contents and gear must match the pre-test snapshot. |
| Save interruption | On a sacrificial fixture cut main power before, during and after confirmation. Retry, reconnect and power-cycle again. Check the same catch appears once, earlier entries remain readable, and a storage failure is reported. Repeat with an extended species and nearly full flash. |
| Fit and service | Check lead retention, charge/discharge temperature range, protection against shorting, service instructions, cell transport documentation and applicable battery safety requirements for both cells. |

## Future cloud restore

Cloud backup is a planned opt-in service. It will associate an authenticated owner with a versioned journal independent of device addresses, Bluetooth bonds and browser cookies. A catch has an immutable origin ID. Retried uploads and restores must deduplicate on that ID. Preserve UTC and the separate simulated period, retain stable species and location identifiers across content revisions, and represent a missing historic value explicitly.

A new device will download and validate a complete staged snapshot before switching the active save. Keep the previous local copy until verification passes. Merging two offline devices unions catches by ID and recomputes counts and bests. Legacy aggregate snapshots need a distinct migration baseline to avoid double credit. Version and resolve gear preferences separately. Pairing credentials, Wi-Fi passwords and update signing secrets are outside the backup payload. Acceptance requires restoring to a fresh device, duplicate/reordered upload, offline changes from two devices, an interrupted restore, older firmware and a legacy journal with no timestamps.

[Game and demo](Game-and-demo.md) · [Assembly and battery pocket](Hardware-and-3D.md)
