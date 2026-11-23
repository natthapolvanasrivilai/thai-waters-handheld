# PCB fit gauge dimensions

All dimensions below are nominal millimetres at 100% scale. Each STL contains one connected part on its intended print face. The source assembly is TW-A-0001-R0013 with TW-A-0002-R0006 electronics. Spacers, shims and housing parts have their own geometry. [Installed STEP ledger](../TW-A-0001-R0013/installed-step.json) · [STL hashes, installed coordinates and print datums](geometry.json) · [Independent final-STL measurements](geometry-checks.json)

| Gauge | Bed footprint | Height | Mechanical interface reproduced |
|---|---:|---:|---|
| [A1 display/controller](meshes/A1-display.stl) | 92.44 × 61.00 | 13.40 | R6 glass face down, LCD and backing stack, controller perimeter, four boss seats, USB-C, J7/J8/J9 and button lands |
| [A2 reel sensor](meshes/A2-sensor.stl) | 25.40 × 17.78 | 4.53 | 1.57 substrate, four corner holes, six wiring holes, opposed side sockets and central sensor |
| [A3 haptic](meshes/A3-haptic.stl) | 20.00 × 20.00 | 9.76 | R0002 substrate, motor-wire holes, U1, capacitors and J1 housing envelope |
| [A4 integration](meshes/A4-integration.stl) | 23.00 × 13.00 | 2.03 | Outline, bonded back plane and individual populated-side bodies |
| [A5 power](meshes/A5-power.stl) | 23.00 × 16.00 | 2.385 | R0006 outline, bonded back plane, wire holes and individual populated-side bodies |
| [Key switch](meshes/KEY-switch.stl) | 11.00 × 10.00 | 5.30 | Key PCB edge, switch housing and fixed unpressed actuator on its centerline |
| [USB-PCB1 indicator](meshes/USB-PCB1.stl) | 4.80 × 3.20 | 0.852 | LED projection on the face of the light daughterboard |
| [USB-PCB2 resistor](meshes/USB-PCB2.stl) | 3.20 × 2.00 | 1.05 | Series-resistor projection on its separate small PCB |

## Seat the A2 gauge

The broad flat back is the print face. Turn the populated face toward the carrier posts and the reel magnet. The rectangular central land represents the AS5600 package. The two taller sockets flank it. The row of six small wire holes runs along the edge nearest the case floor. Align the four corner holes with the seats and lower the board squarely onto the locating pins. Leave the trial unbonded so that you can inspect seating and lift the gauge out.

The four Ø2.50 corner holes are **20.32 × 12.70** on centers. Each hole center is 2.54 from the adjacent straight outside edges. The outside corners are R2.54. In installed coordinates the PCB extends from X39.48 to X41.05. The center of the sensor face is X42.55, Y0, Z14.80. The modeled magnet’s near face at X43.75 gives a nominal 1.20 gap. Keep that gap open while turning the reel by hand. A printed plastic gauge can show rocking, pin contact or mechanical rubbing. Magnetic response requires the real sensor and magnet. [Adafruit PCB artwork](../rev-E/scripts/inputs/Adafruit-AS5600.brd) · [Magnet location](../../components/radial-8995/README.md) · [Carrier registration](../TW-A-0001-R0013/QA/r20-carrier-fit.json)

## Interpreting the other gauges

- **A1.** The nominal distances between the four insert centers are 72.00 and 48.50. Each boss has a 4.00 OD and a smooth Ø2.00 blind pilot that identifies its axis. Use the four seats to check height and alignment. Insert threads, lens recess, optical behavior and switch travel require actual parts. The USB and harness connectors are solid witnesses for outside clearance. They do not accept a plug. The component-height lands fill some space beneath overhangs and omit fine contacts, small passives and the display flex.
- **A3.** The J1 outer block reserves 14.90 × 9.45 of board area. Its roof is at installed Z14.36. Plastic fills the space down to the board so the gauge prints flat. Check the underside separately for the real header tails, which project 0.4675 below the board. The mating plug, lock, shim details, contact cavities, solder and wires are outside the gauge. The revised electronics locations come from the R0002 layout. [A3 mechanical and licensing record](../../electronics/pcb-haptic-cie-r0002/README.md)
- **A4 and A5.** The three spacer locations on each board establish installed height. The gauges’ flat backs are at Z18.535 and Z17.840, respectively, including the maximum back copper height. Individual components project toward decreasing Z. Preserve these planes when using the supplied dry spacers. The terminal pads, leads, solder and adhesive fillets need their own clearance.
- **Key and USB.** The fixed key plunger represents the unpressed position. The real switch’s trimmed terminals project 0.80 below the board. Check that clearance separately. The two tiny USB daughterboards represent individual board and package envelopes. The LED optical path, bonds and lead routing require the physical assembly.

## Geometry checks and rebuild

The release check reads each delivered STL and registers it back to installed coordinates. It measures exterior bounds against the source ledger, traces the top surfaces at 15 independently selected landmark locations, and sections the bore walls. The A2 outline and corner holes are also checked against the Adafruit Eagle artwork independently of the STEP. Its outline differs by 0.0081 square millimetres or less after circular edges are triangulated. Printed layer heights and real hole sizes depend on the machine and material. [Measurement program](verify_gauges.py) · [Per-gauge results](geometry-checks.json)

A clean rebuild from the digest-matched STEP reproduced all eight delivered STL files and the geometry ledger byte for byte. Build with the uncompressed assembly STEP and CadQuery 2.8, manifold3d, NumPy and trimesh. Run from this folder.

```text
python build_gauges.py /path/to/TW-A-0001-R0013-dressed.step
python verify_gauges.py
```

The A1 and A2 dimensions reference Waveshare ESP32-S3-Touch-LCD-3.5B and Adafruit 6357. The A3 substrate gauge adapts the Boardoza DRV2605L geometry through the project's R0002 layout under CC BY-SA 4.0. Its CviLux J1 witness is a project-authored rectangular envelope. The key dimensions reference Omron B3F-1002-G and the KiCad family model. Keep the supplier credits with any permitted copies. [Project provenance](../../../third-party/NOTICE.md) · [Boardoza attribution](../../components/boardoza-drv2605l/README.md) · [A3 license](../../electronics/pcb-haptic-cie-r0002/LICENSE) · [Switch provenance](../../components/omron-b3f-1002-g/README.md)
