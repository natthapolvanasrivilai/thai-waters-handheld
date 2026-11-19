# Rev F top-edge power key

The player operates a guarded, captive key at the left end of the top edge. Its normally open switch closes the two contacts of the original Waveshare PWR button. This preserves battery cold-start and hardware long-press shutdown, including when the ESP32 is asleep. The integrated capacitive touchscreen handles menu taps. RESET and BOOT keep their service functions. [Waveshare board resources](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B)

## Wiring

```text
A1 stock controller                       W3 harness                 PCB1 / top edge
K3 pin 2, raw switch node   ───────────── white ────────────────o
                                                                SW1  NO momentary
K3 pin 1, ground            ───────────── black ────────────────o

The original K3 stays fitted across these same two nodes.
```

| Connection | V1 and V2 electrical identification | Assembly check |
|---|---|---|
| White, raw button node | K3 pin 2 shares R38 pad 2. R38 is 510 Ω from that contact to PWRON. PWRON reaches AXP2101 pin 30 and J8 pin 23. | With USB and the cell disconnected, identify the K3 solder contact with continuity to R38 pad 2. Check the path to header J8 pin 23 through R38. |
| Black, ground | K3 pin 1 connects to the ground plane. | Identify by continuity to J8 pin 3 or 4, then verify the stock button shorts the two identified switch contacts when pressed. |
| SW1, external dry contact | One wire to each side of SW1. Its four through-hole leads form two internally common pairs. | Meter the selected pair on the loose switch. It should be open at rest and close only while pressed. The case tabs on the stock switch serve as mechanical anchors. |

V1 senses PWRON through R37. V2 takes its R37 input from the K3 side of R38 and adds a 100 kΩ pull-up at the transistor gate. Soldering to the two K3 contacts preserves each revision's intended signal path. J8 pin 23 bypasses the series resistor if shorted directly to ground. The header therefore serves as a measurement point for this assembly. [Waveshare V1 schematic, POWER and PinOut blocks](https://files.waveshare.com/wiki/ESP32-S3-Touch-LCD-3.5B/ESP32-S3-Touch-LCD-3.5B-Schematic.pdf) · [Waveshare V2 schematic, same blocks](https://github.com/waveshareteam/ESP32-S3-Touch-LCD-3.5B/blob/main/hardware/schematic/ESP32-S3-Touch-LCD-3.5B-V2-Schematic.pdf)

## Carrier and harness

- **SW1** uses an Omron B3F-1002-G gold-contact, through-hole switch. The nominal footprint is 6 × 6 mm. Plunger height above the mounting plane is 4.3 ± 0.2 mm, operating force is nominally 1.76 N and pretravel spans 0.15–0.45 mm. The printed cap acts on its 3.5 mm diameter plunger. [Omron B3F datasheet, pages 1, 3 and 4](https://components.omron.com/us-en/datasheet_pdf/A070-E1.pdf)
- **PCB1** is an 11 mm wide × 10 mm high × 1.0 mm thick FR-4 coupon in the shell tracks. Center four 1.0 mm finished holes at X = ±3.25 mm and Z = ±2.25 mm relative to the plunger. Use four electrically isolated lands or four bare holes with individually insulated terminations for the fit unit. Trim, solder and dress leads parallel to the coupon so the complete rear termination stays within the modelled 0.8 mm envelope. Omron's drawing illustrates 1.6 mm PCB stock. The 1.0 mm prototype carrier and its terminal retention require a solder and pull check.
- **W3** uses two 30 AWG fine-stranded insulated leads. Start with 100 mm of each, trim on the seated assembly and allow enough slack to remove the carrier. Restrain the insulated pair at both the carrier and the fixed frame before the board joints. Route through the left-side channel clear of the screw boss, cell pouch, antenna region and reel. Close the shell slowly and check that the pair stays out of the seam.
- Position the actuator toward the top wall, along +Y. CAD targets X = −36 mm and Z = 12.5 mm. On the actual print, verify the cap returns freely, leaves the switch open under resting pocket pressure, closes before reaching the cap stop and transmits the end load to the housing.

## Bench verification

1. On the isolated harness, cycle SW1 while observing continuity. Repeat after seating the coupon and fitting the cap. Flex the dressed leads gently to check for an intermittent short or open circuit.
2. Record the actual A1 revision and identify K3 using the vendor component drawing and a meter. Attach W3 with USB and battery disconnected. Verify that either physical key independently closes the same contacts and both release.
3. Start with the existing board controls and flash Thai Waters. Firmware programs the AXP2101 for a nominal one-second battery power-on hold and four-second shutdown hold. On battery alone, verify boot from off, shutdown from the game and boot again through the top key. Record elapsed times and verify a saved catch remains in the collection.
4. Repeat with USB attached and during charging. Record LCD/backlight state, current and USB behavior separately. Confirm the stock button and USB programming still work. Operate the key through the full guarded travel with the case closed.

These are nominal schematic and mechanical checks. The Rev F harness, physical key timing, pocket pressure and assembled usability require a built unit. Production sourcing should specify the controller revision and provide dedicated harness pads or a connector with equivalent raw-button and ground nets to replace prototype hand rework.
