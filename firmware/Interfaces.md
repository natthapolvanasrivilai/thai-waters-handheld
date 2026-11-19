# Rev E hardware and update interfaces

The USB data port exposes the ESP32-S3 ROM programming path. Release 0.6 runs on controller 31137 with 16 MB flash, OPI PSRAM and the original two 3 MiB OTA slots. The archive contains editable Arduino source and its board dependencies. Reserve these boundaries for compatible incremental releases. A change to the bootloader, partition table, radio architecture, pinout or physical sensor range requires separate migration or a board variant.

## Native drivers and USB API v1

Open USB serial at 115200. Send one ASCII line terminated by LF. Consumers read JSON lines and ignore ordinary boot/game diagnostics. Begin with `api1 caps`. Compatible additions may append fields. A changed field unit or meaning requires another major API version.

| Command or native entry | Result |
|---|---|
| `api1 sample` | Monotonic milliseconds, XYZ accelerometer counts and g, gyro counts and degrees/s, validity flags, raw reel angle and magnetic field state |
| `api1 gyro on` / `api1 gyro off` | Enables or disables QMI8658 angular velocity. Default off. Configured ±256°/s and nominal 112.1 Hz. Accelerometer is ±4 g at nominal 125 Hz. |
| `api1 stream on` / `api1 stream off` | 10 Hz diagnostic snapshots, best effort. This protocol is a bench sampler. High-rate capture belongs in firmware against the native driver and FIFO. |
| Reel | AS5600 absolute angle 0–4095 per turn, field enumeration Missing=0, Weak=1, Strong=2, NoMagnet=3, Good=4. The gameplay wheel handles wrap and direction. |
| `HardwareAPI.h` | Native QMI8658, XPowersPMU and shared Wire handles, raw/physical units and combined sensor sample |
| Display, touch, speaker audio and haptics | Board.h exports the canvas and touch point. Sound.h controls ES8311 speaker output. Rumble.h supplies strength and pattern for the optional DRV2605L. |
| Additional installed peripherals | The RTC is PCF85063 on shared I²C. The board vendor supplies microphone, SD and optional camera examples. Integrate these in firmware with the actual SKU pinout and bus ownership. The current USB protocol exposes the listed diagnostics. |
| `api1 forget` | Deletes the saved network, closes phone setup and switches Wi-Fi off. |

On the board open **Menu → Wi-Fi + clock → Phone setup**. Join the displayed temporary WPA-protected network from a phone and visit the displayed local address. Submit the home 2.4 GHz SSID and password. A successful join saves the tested network. Failed entries can be retried. Back or the five-minute timeout closes setup. Wi-Fi can be switched off after sync. Stored credentials are in device NVS. Production provisioning should evaluate encrypted storage and debug/recovery policy against the ownership model.

**Live** uses Bangkok civil time, UTC+7. Dawn is 05:00–07:59, day 08:00–16:59, dusk 17:00–19:59 and night 20:00–04:59. SNTP sets UTC and the PCF85063 retains it if its supply remains present. The firmware checks the oscillator-stop flag and a previously initialized UTC marker. An unsynchronized unit displays *Clock needs sync* and uses dawn as a playable fallback. A live-time change takes effect between casts. Test an actual power interruption with the chosen RTC backup configuration.

## Owner-managed signed releases

1. Keep the owner's P-256 private key outside Git and the firmware. For an engineering key, OpenSSL supports `openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:prime256v1 -out owner.pem`. Back it up under the owner's control.
2. Increment `releaseNumber` in UpdateFeed.h for each release. Compile the application. Package the binary using `node tools/sign-release.mjs owner.pem firmware.bin 4 update.twup`, with the release number matching the compiled build. Record the SHA-256 in the release record.
3. Provision the printed **public** key using USB, then send `api1 feed https://your-owned-host.example/releases/rev-e.twup` with the real URL. Host the package directly with a publicly trusted TLS certificate and no redirects. Provision these settings during manufacture. The prototype ships without an enrolled owner or a production feed.
4. Connect Wi-Fi, synchronize time, open **Menu → Wi-Fi + clock → Online update**. The device verifies target model, increasing release number, length and ECDSA signature, hashes the streamed image, then selects the inactive slot for boot. Candidate firmware checks panel, IMU, charger setup and audio startup before marking it valid. A failed boot validation requests rollback. USB remains the recovery path.
5. Qualify the physical device with an interrupted transfer, wrong-model package, failed signature, corrupted payload, low battery, restart during flash and forced post-boot health failure. Confirm the journal, settings, API version and clock persist. No production update server or private signing key is part of this release.

Local multiplayer uses one LAN host, v1 room messages and the stable location ID. The host directory includes the browser and UDP setup. Reassess authentication, abuse controls, support costs and privacy before offering an internet-wide service.


