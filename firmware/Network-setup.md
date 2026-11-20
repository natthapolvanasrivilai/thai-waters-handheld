# Wi-Fi setup, Device Info and phone linking

## Current prototype and local Wi-Fi

The configured target is [Waveshare 31137 ESP32-S3-Touch-LCD-3.5B](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B), with 2.4 GHz 802.11b/g/n and Bluetooth LE. It cannot join a 5 GHz-only SSID. The package targets the existing Rev F sensor pinout, 16 MB flash and 8 MB OPI PSRAM. A package does not verify an individual controller's installed firmware, PCB revision, or serial.

From the handheld's network menu, choose **Phone setup**. Connect the phone to the temporary Wi-Fi shown on the handheld and open the local address printed on its screen. This is a local, WPA-protected temporary access point with an HTTP form, not phone account pairing or a login to any remote site. The home-network password is masked and transmitted to the handheld inside the local AP connection; it is not submitted to an Internet service. There is no password in a URL, printed diagnostic or response. Close the setup after use and do not share its temporary access-point password.

**Remember on this device** is off by default. Unchecked, a successful connection remains active for this powered Wi-Fi session without replacing an older record or saving the radio preference. Turning Wi-Fi off or restarting ends the session. Checked, the handheld stores credentials only after confirming a new connection reached the selected network. If a different record is already stored (including a changed password on the same SSID), this prototype keeps the prior record and reports that fact. The existing trusted-USB Forget mechanism is separate. A normal touchscreen Forget confirmation is future work, not something the phone form silently does. Link and clock messages are separate; a Wi-Fi link does not prove Internet access.

The supported 3.3.10 Arduino profile initializes its [Wi-Fi SDK storage in RAM](https://github.com/espressif/arduino-esp32/blob/3.3.10/libraries/WiFi/src/WiFiGeneric.cpp) when persistence is disabled before any Wi-Fi mode/start. The application stores approved remembered credentials in its own Preferences namespace, not via automatic SDK saves. This is not a claim that NVS is encrypted on existing hardware or that volatile SDK buffers are immediately wiped on every transition.

## Follow-ons

1. **Handheld Settings:** Manual async scan, localized display names, bounded cached rows with best-signal deduplication, hidden SSID entry and explicit confirmation. Keep playing responsive. Separate turning the radio off, dropping a live connection without deleting a remembered network, and explicit Forget. Offline, resolving, associated and not able to reach a network/service are distinct. Do not auto-start scans when opening the information page.
2. **Device Info:** Unit serial only from actual provisioning (otherwise Not provisioned); controller PCB revision only from an authoritative installed-unit record (otherwise Not verified); separate enclosure revision, running firmware build/commit and game/content revision. Do not fall back to a PCB MAC as a serial, and do not put identity or logs in screenshots/exports by default.
3. **Future authenticated phone QR, design only:** Disabled unless an owner deliberately requests a session. A provisioned/authenticated handheld tells a first-party authenticated service that it is ready to link. The service returns a public opaque *request reference* scoped to that device/session for a short window (initial trial ≤2 minutes). The displayed HTTPS QR contains only the first-party URL plus the opaque request reference; it is not a credential and never contains a Wi-Fi password, device key, serial/MAC, pairing secret, saved game, access token or account data. A scanner must sign in; scanning or retrieving the URL grants no device or save access. Both ends inspect the intended link; the authenticated handheld explicitly confirms a verifier tied to that signed-in request before a one-time server-side atomic claim. Expire on timeout/power-off/cancel; reject replay and two-phone races; limit attempts and support unlink/revocation. No save transfer or new authority is implied by authorizing a link. Backend, device provisioning, account enrollment, save transfer, and live connectivity are not implemented here.

Host-only acceptance:

```sh
python3 firmware/tests/run-connected-privacy.py
```

This exercises the real Connected.cpp against fake radio, HTTP and Preferences hooks with dummy values only. It does not compile the ESP32 target, validate physical Wi-Fi/firmware, transfer data, or flash.
