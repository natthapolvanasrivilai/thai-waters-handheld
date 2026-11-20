# Pocket Reel USB diagnostic preview (host only)

On Windows, use the same Python environment as the existing private USB packaging tools. Capture additionally requires pyserial (already a dependency of esptool); offline replay and the synthetic tests use only Python's standard library. Nothing here installs packages, flashes firmware, or changes a device setting.

On an approved bench unit, identify the actual Pocket Reel COM port in Device Manager and close any Serial Monitor. Use a USB data cable. Commands:

```powershell
py -3 usb_diagnostics.py capture --port COM7 --output reel-sample.jsonl
py -3 usb_diagnostics.py capture --port COM7 --seconds 20 --output reel-session.jsonl
py -3 usb_diagnostics.py replay reel-session.jsonl
py -3 usb_diagnostics.py validate fixtures/synthetic-wrap-dropout.jsonl
py -3 -m unittest -v test_usb_diagnostics.py
```

Capture opens only the explicitly selected enumerated port at 115200 8N1, with DTR/RTS false, validates the API v1 capabilities before sample/stream, and creates a new local file rather than overwriting one. Windows/driver behavior at open still requires an approved physical bench check. A stream is opt-in (1–120 seconds); stop is attempted in finally. If the cable is removed, the trace is incomplete, and the device may still be streaming after reconnection. Restart the approved bench unit (or use its approved recovery procedure) before another capture when stop is unconfirmed. Captures are labeled LIVE; unit tests are SYNTHETIC. Replay preserves recorded order and the original LIVE/SYNTHETIC source label, adding mode REPLAY to every emitted row. It does not emulate elapsed wall time, inject controls or claim firmware/board equivalence.

Captured signals: sampled accelerometer, gyro only if already available/enabled in device, magnetic field code and valid 12-bit absolute reel count. Missing battery mV/state, charging, VBUS state, switches, touch and unwrapped position are null. Unknown raw vectors are null even when firmware emits numeric placeholders. The firmware's caps fw field is what the device reported, not a source SHA. The 10 Hz diagnostic stream cannot establish travel direction, count all edges, reproduce the native Wheel's 90 ms continuity threshold or validate physical performance. No raw boot text, credentials, journal contents, configuration commands, HID injection, network or OTA access.


## Scope and evidence

The read-only host contract is the current [production API implementation](../../WillowCreek/Connected.cpp) and [interface notes](../../Interfaces.md). Only the fixed four `caps/sample/stream on/stream off` requests are allowed. The real collector uses Windows-only pyserial with the explicit port checked against enumerated devices; no module installation or physical access is needed for replay or validation. No automatic reconnect: after unplug or reset, start a new capture and keep the interrupted file as incomplete.

The checked-in `fixtures/synthetic-wrap-dropout.jsonl` is **synthetic only**. It covers AS5600 rollover, uptime rollover, magnetic dropout and optional gyro validity. It is not obtained from a board; no left/right direction or dropped device packet counts are inferred. `seq` is the host's recorded row order, not a device source sequence. `validate` prints counts and exits nonzero for a bad or incomplete trace; `replay` emits recorded rows in order without injecting game controls. Actual Windows COM behavior, permission, physical gyro transfer, PMIC/switch/touch reporting, automated reconnect and native/browser gameplay parity remain separate acceptance work.
