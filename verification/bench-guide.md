# Rev E open-case bench guide · Thai Waters 0.5

Run the board on USB and connect the kit speaker to J9. The normal reel harness connects the AS5600 to J8. Flash the four images using the command in the firmware README, then open **Menu → Bench test**. The bench page is accessible from the first calibration screen and pauses the fishing clock.

| Check | Action | Expected observation |
|---|---|---|
| Battery gauge | Test on the protected cell, then plug in USB. Power down before changing battery wiring. Also test on USB alone. | The play header and Bench page show the AXP2101 estimate in percent. A leading + indicates active charging. USB indicates external power with no detected cell. Two dashes indicate an unavailable reading. Refresh interval is three seconds. |
| Board power key | Hold the device landscape with the screen facing you and the reel to your right. Find the long lower-edge service slot near the left corner. PWR is the first of three buttons, closest to the USB end. On battery, hold PWR for about four seconds to switch off and about one second to start after first configuration. | Verify using the actual pack and board. Test USB attached separately because external power can keep the board supplied. PWR, RESET and BOOT sit 8.5 mm apart. The PWR tip sits 7.65 mm inside the lower wall. CAD clears a straight 2 mm diameter probe, but finger access and a production cap still need a fit test. |
| Line tension | Hook a fish. Wind during a run, then ease off. | The eight segments on the right edge of the active LCD fill upwards. Amber begins at 55% and red at 80%, accompanied by EASE. Landing or losing the fish clears the light. |
| Playing and lifted poses | Complete the two-pose calibration first. Hold the normal pose, then raise the rod and return it briskly. | Near zero degrees at rest. Crossing 70% of your calibrated span registers a lift. Returning below 27% within 0.9 seconds of the high pose registers a cast. Each counter advances once per gesture. The page shows the actual thresholds, live acceleration in g and last event. |
| Encoder and wind direction | Turn the knob one full revolution, then unwind. | Raw angle passes through 4095/0 smoothly. Signed turns rise by about +1.00 in the winding direction and return near zero. Tap **Reverse direction** if needed. Changing direction clears the session turn total. Weak, strong or missing magnetic field gets its own status. |
| Bite volume | With the speaker fitted, tap **Cue level** to cycle 0–3. Tap **PLAY BITE** at each level. | Level 0 is silent. Higher levels audition the two-note bite at the selected volume, even if gameplay normally uses visual-only cues. The separate music level is under **Sound + controls**. The on-screen level is the digital setting. Loudness must be judged with the actual speaker and grille. |
| Optional haptics | With power removed, fit the optional parts below. Power up, re-enter Bench test, select rumble 1–3 and tap **Tease**, **Bite**, then **Pull**. | The page detects the driver. A tease is a light single tap, a bite is a distinct double click, and a pull is a buzz. During play, pulls become closer together as tension rises or a fish runs. Level 0 disables all rumble. |
| Species signatures | In Bench test choose a rumble level and tap **Prawn pick**, **Bottom hold** and **Fast run**. With the case closed, have someone play the samples in a different order while you hold the device normally. | Identify three light pre-bite picks, a broad loaded buzz and a rapid three-tick burst by touch. Check that the motor starts at Low and stops when you leave the bench. In play, prawn picks follow individual tip twitches, a bottom hold repeats its buzz under load and a sprint repeats its burst during the run. |
| Crosstalk and closure | With the device resting, audition each rumble setting while the reel is stationary. Slowly rotate the knob through a full turn with the motor pulsing. Repeat with music playing, the board seated and the bezel resting on the rim. | No false lift or cast, loss of magnet status, reset, stalled encoder or audible supply glitch. Dry-fit every lead with clearance to the reel, battery pouch and lens. Check the 3.3 V rail under simultaneous display/audio/motor load before enclosed testing. |

## Rumble wiring and incremental parts

| Qty | Component | Prototype cost |
|---:|---|---:|
| 1 | Adafruit 2305 DRV2605L STEMMA QT haptic driver | US$7.95 |
| 1 | Adafruit 1201 coin ERM, Ø10 × 2.7 mm | US$1.95 |
| — | Short insulated leads, splice insulation and mounting tape | From workshop stock |

The two purchased parts total **US$9.90** before shipping and tax. Adafruit gives a typical motor draw of about 60 mA at 3 V. Startup current, actual duty cycle and battery runtime with rumble are unmeasured. [Driver](https://www.adafruit.com/product/2305) · [Motor](https://www.adafruit.com/product/1201)

Branch from the board-side 3.3 V I²C harness so the original AS5600 keeps its existing wiring. Use the J8 signal labels from the verified wiring diagram for your board revision. The two peripheral addresses are 0x36 and 0x5A.

| From | To |
|---|---|
| J8 3V3 | Driver VIN |
| J8 GND | Driver GND |
| J8 SDA / GPIO8 | Driver SDA |
| J8 SCL / GPIO7 | Driver SCL |
| Driver OUT+ | Motor red lead |
| Driver OUT− | Motor blue lead |

The motor is driven across the two output terminals. Leave the optional trigger input disconnected. The sketch identifies the DRV2605L, selects the ERM ROM library, programs open-loop drive, and issues finite effects. The driver finishes each effect independently of the next I²C command. [Driver pinout](https://learn.adafruit.com/adafruit-drv2605-haptic-controller-breakout/pinouts) · [TI register and waveform tables](https://www.ti.com/lit/ds/symlink/drv2605l.pdf)

## Candidate position inside Rev E

With the Rev E CAD origin at the center of the display in plan view, +X points toward the reel, +Y toward the J8 side, and +Z toward the screen. Both parts sit on the exposed case floor immediately to the right of the battery fence.

| Part | Center X, Y (mm) | Bottom Z (mm) | Orientation |
|---|---|---:|---|
| Driver | +19, −6 | 3.0 | 25.8 mm side along Y. Allow 17.8 mm across X and 4.6 mm height. Use low-profile soldered connections. |
| Motor | +19, +19 | 3.0 | Disc face parallel to case floor. Bond to the shell for vibration transfer. |

The Rev E solid check found zero nominal intersection for these two envelopes. It included the populated boards, folded reel, housing, bezel, cell and speaker allowances, and six existing wire reservations. Each part has 0.50 mm underneath for its adhesive stack. The driver clears the controller by 10.03 mm and the nearest existing wire reservation by **0.93 mm**. The motor clears the controller by 10.20 mm and the sensor assembly by 16.58 mm. These are digital distances. The new solder joints, motor leads, glue, plug bodies and tolerance stack still need the open-case check above. Keep the cell on its own supports. The archive includes the numeric clearance results.


## Connected and sensor checks

Read the USB API v1 capabilities, enable the gyro and collect stationary and raised samples. Turn the physical knob both ways across the 4095/0 boundary and verify field status. Compare a phone and board side by side at rest, +20° and +40° using their own calibrated axes. Record timing, noise, false gestures and total turns. Check the clock against Bangkok time after network sync, after turning Wi-Fi off, and after removing main power with the intended RTC supply. Join a shared event from two Rev E units, unplug the LAN host and verify that solo fishing continues. Exercise OTA power interruption, rejection and rollback on an engineering unit before closing the case.
