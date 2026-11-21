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

## Offline native reel witness (#33)

This local tool exercises the actual shared firmware `creek::Wheel` math with a
complete validated API1 trace. It does not open a COM port. Run from this directory
in a shell with an existing C++17 compiler and Python:

```sh
g++ -std=c++17 -O2 -Wall -Wextra -Werror -Wno-misleading-indentation -pedantic game_replay.cpp -o .local-wheel-replay
python -m unittest -v test_usb_diagnostics.py test_game_replay.py
python prepare_game_replay.py < fixtures/synthetic-wrap-dropout.jsonl > replay-input.txt &&
  ./.local-wheel-replay < replay-input.txt
```

The GCC flag disables two inherited formatting warnings in the untouched
`Waters.h`; it does not change compilation semantics. The two-step command avoids
using an incomplete conversion, including in shells that do not report upstream
pipe errors. The prepared text contains only validated timestamps and reel
counts; keep it local or use the checked-in synthetic sample only. Do not
overwrite a real trace while redirecting output.

- Device uptime is used, not the host's polling interval. Modulo 32-bit rollover
  is handled normally; a backwards discontinuity resets the local wheel baseline.
  Invalid field/first reading/stale time/duplicate time and implausible jumps do
  not create a turn. A new trace/process always starts as a new session.
- An API1 stream is nominally 10 Hz. At about 100 ms between rows it is **too slow
  for the native Wheel's 90 ms continuity bound**. The existing synthetic
  10 Hz trace demonstrates exactly this; do not infer direction, fill gaps or
  extrapolate. `counts:0` denotes accepted zero movement only when `event` is
  `accepted`; always read that validity label.
- Output remains `mode:REPLAY`, preserving `source:LIVE` or `SYNTHETIC`. A
  live-origin replay exercises only Wheel and reports null game fields. In the
  synthetic lane only, a known cast/hook seed opens a controlled Fight and
  accepted 12–90 ms input intervals advance the shared game; use `--reverse`
  to test signed direction. No time/turns are invented across rejected samples.
  This is not real elapsed fight playback, an IMU/switch replay, a simulator UI
  integration, or a complete renderer/PCM parity check.
- This witness was built and tested on a host compiler, not on Windows/ESP32
  here. The existing Windows capture command allowlist and USB firmware are
  unchanged. Actual Windows disconnect/line-state behavior, faster diagnostic
  rate design, motion/power channel proof and physical tests remain on hold.
