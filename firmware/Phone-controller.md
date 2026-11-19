# Thai Waters Rod · controller preview 0.9.4

The handheld sends motion and reel input to the game running in Safari as a Bluetooth Low Energy keyboard. This USB preview targets the Waveshare 31137 ESP32-S3-Touch-LCD-3.5B, the documented Rev F sensor wiring, 16 MB flash and 8 MB OPI PSRAM. Real board and iPhone testing remains open. [Apple accessory pairing](https://support.apple.com/en-us/105108) · [Bluetooth HID over GATT](https://www.bluetooth.com/specifications/specs/hid-over-gatt-profile-1-0/) · [Espressif 3.3.10 BLE library](https://github.com/espressif/arduino-esp32/tree/3.3.10/libraries/BLE)

The full field guide carries 2,545 species-specific portraits. The browser includes the entire collection offline. The handheld includes 464 resident portraits, including Brahmaputra labeo, and reads the other 2,081 from the field-art card. Each stored catch keeps its stable ID and receipt history.

The ESP32-S3 target build uses 2,970,566 of 3,145,728 application bytes, leaving 175,162 bytes in its OTA slot. The field-art card file is 3,772,432 bytes. Its SHA-256 is `443b7332de79b57a48791ae31def92792fed1c5317274e84ee2dcd6df2c6c4fa`.

## Prepare the field-art card

Copy the package’s `sdcard/TW-FISH.BIN` into the top level of a FAT32-formatted microSD. Insert the card into the Waveshare 31137 onboard TF slot before powering on. The firmware checks its byte count and SHA-256 against the compiled index and copies the verified pixels to PSRAM. After startup, the game reads that memory to render catch and journal portraits. No installation writes go to the card or the collection filesystem. An absent, damaged, incompatible or unreadable card leaves the 464 resident fish available to catch. The field guide retains the full catalog. Returning the matching card and restarting restores the complete illustrated collection.

## Pair and play

1. On the handheld, calibrate both poses in **Menu → Sound + controls → Rod calibration**. In **Bench test**, turn the knob in your normal winding direction and verify **Winding IN**. Change the reverse option if needed.
2. Open **Menu → Connections → Phone controller**. On iPhone select **Settings → Bluetooth → Thai Waters Rod**. Enter the six digits displayed on the handheld when prompted.
3. Open the private playtest in Safari, enable its handheld controller and focus the fishing surface. Once paired, tap **Start** on the handheld. Raise the rod, then lower it briskly to cast. Lift at a bite to hook. Wind or pay out line with the knob.
4. Tap **Pause** before typing or switching apps. iOS routes hardware keys to the foreground app. **Disconnect**, Back or tapping outside the controller sheet disconnects the phone and stops advertising. After an unexpected disconnect, advertising resumes while the sheet remains open. Tap Start to re-arm after reconnecting.

The rod uses the board’s filtered gravity vector and stored calibration. A weak or missing AS5600 magnetic field suppresses reel travel. Opening the controller sheet pauses local fishing. Local reel-click audio and haptics still follow the physical knob at 12 feedback teeth per turn, subject to the configured intensity and rate limits. Game-driven fish/bite feedback stays on the web game. This keyboard protocol has no game-rumble return channel.

## Catch receipts and physical controls

Tap anywhere on the landed-fish screen to file the catch. The centered prompt pulses over 2.4 seconds, with the clock and battery at the upper right. Each individual catch stores its measured size and type, estimated mass, species, fishing spot, time period, weather and bait. Its time comes from a valid RTC or network sync. An unavailable clock leaves the timestamp unknown. Open **Menu → Fish collection → Catch log** to browse filed receipts by time and sequence. Undiscovered entries appear as silhouettes in the collection. A tap opens habitat and bait hints. Export committed receipts over USB with `api1 catches` followed by `api1 catch 1` and subsequent sequence numbers. [Storage schema and recovery](Interfaces.md)

The 480×320 touchscreen uses two-column controls for the primary menu, spots, rod workshop, bait, sound settings and connections. Main actions span 196×54 pixels (approximately 30×8.3 mm on the nominal 3.5-inch display). Back areas are 80×48 px, spot selectors are 196×49 px, and the controller buttons are 196×64 px. The bench actions use 120×52 px. The nine diagnostic crosses check touch accuracy to Â±12 pixels. Verify physical tolerance, visibility and operation with a thumb on the actual LCD.

## HID v1

Keyboard usage page 0x07, HID service 0x1812, report ID 1. Each 8-byte input value contains the modifier, reserved byte and six key slots. The report-reference descriptor supplies the ID separately. All modifiers and unused slots stay zero. The device sends an all-released report between pulses. Boot keyboard input and standard host LED output are also exposed.

| Physical key code | Meaning |
| --- | --- |
| KeyC / KeyH | Cast / lift edge |
| KeyJ / KeyU / KeyI / KeyO | Wind 1 / 2 / 4 / 8 increments |
| KeyK / KeyN / KeyM / KeyP | Pay out 1 / 2 / 4 / 8 increments |
| Digit1 â€¦ Digit9 | Calibrated absolute rod elevation from rest to raised, in eighths |
| KeyV | Controller heartbeat approximately once per second |

Each increment is 1/24 turn. The firmware accumulates signed 12-bit encoder changes across wraparound. Opposite movements may cancel between reports. The pending movement is bounded to one turn during a transport stall. Angle changes use hysteresis and the current angle refreshes approximately twice a second. Newly armed connections start with a neutral report. Handle physical key codes on keydown and expire the receiver after three seconds without a heartbeat.

The firmware requires a subscribed keyboard input on an authenticated, encrypted, bonded connection before arming. Each reboot starts with the BLE stack inactive. After first use, a single reusable GATT allocation stays in RAM until reboot. Closing the controller sheet releases keys, disconnects links and stops advertisements. The Wi-Fi switch remains independent. Measure post-session idle current on hardware. The internal PnP identifier 0xFFFF must be replaced with an assigned product identity before commercial release.

## Physical acceptance

| Check | Record |
| --- | --- |
| Pairing with Wi-Fi off | Verify cold-boot radio silence, the advertised name, passcode, HID subscription and zero keys before pressing Start. |
| Marked knob and rod | Slowly turn exactly once each way and observe +24/âˆ’24 input increments. Rest, half tilt and raised produce bins 1, 5 and 9. Cast, hook and land a catch in Safari. |
| Sound and rumble | At low speed, count 12 handheld feedback ticks per revolution. Test audio mute and haptics-off independently. |
| Disconnect | Move out of range during a turn, return, re-arm and repeat after screen lock. Check heartbeat expiry, absence of stuck keys and clean first gesture. |
| Power and memory | Measure battery current with BLE cold, advertising, streaming and exited. Repeat 20 sessions with Wi-Fi on/off and capture free heap, controller latency and power. |
| Regression | Confirm display, journal, stored poses, sound, charge lamp, offline fishing and USB programming on the serial-numbered board. Record phone model, iOS, layout and board revision. |

## Build and flash

Use Arduino-ESP32 3.3.10 and the 0.9 Waveshare Arduino_GFX, SensorLib, XPowersLib and ES8311 libraries. The BLE dependency ships with the core. Build the WillowCreek sketch for **esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,FlashMode=qio,PartitionScheme=app3M_fat9M_16MB,USBMode=hwcdc,CDCOnBoot=cdc**.

Use the four USB images and matching field-art file in the preview archive. The archive includes hashes, a flash utility and the private preview source. The preview is outside the signed OTA release channel. The host fixture in tests/rod_hid.cpp covers signed encoder input, queueing, motion quantization, time rollover and neutral releases. Both target compilation and host tests are separate from the pending physical acceptance.

Extract the ZIP and open a terminal in its top-level directory. Run the offline check first. To install, use a USB data cable, close the serial monitor and replace COM7 with the board port shown by your operating system. On macOS a typical port begins with /dev/cu.usbmodem and on Linux with /dev/ttyACM.

```sh
python flash-controller-preview.py --check
python -m pip install "esptool>=5,<6"
python flash-controller-preview.py --port COM7
```

The flash command writes the bootloader, partition table, OTA selection data and the first application slot. It leaves NVS in place on the existing Thai Waters partition layout. On an unknown board image, back up any existing data you wish to keep before writing.
