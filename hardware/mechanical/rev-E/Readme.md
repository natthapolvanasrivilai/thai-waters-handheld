# Riffle Pocket | Assembly fit review

**Rev D fails at the reel sensor. Rev E passes the nominal rigid-body CAD checks and is ready for a fit print. The assembled device still needs a physical fit check before the playable firmware milestone.**

Open Riffle-PCB-viewer.html in a WebGL 2 desktop browser. It opens on the controller underside. Choose **Sensor mount** and switch **Show original Rev D supports** on and off. Red shows the two measured common volumes in the original housing. Choose **Assembled** to fold and turn the right-side reel. Explode is an inspection aid. Only the seated positions correspond to the fit results.

## What changed

The product uses the stock Waveshare ESP32-S3-Touch-LCD-3.5B (31137) and a separate Adafruit 6357 angle sensor. The earlier published assembly showed outline references for both. This review registers the two manufacturer STEP models in the printed case. The controller model contributes 546 solids and the populated encoder model contributes 25. The supplied controller CAD includes the camera geometry. Waveshare lists the camera separately for the standard board. Retaining the supplier geometry reserves that space conservatively.

Each JST-SH socket on the encoder overlaps a Rev D pad by **15.30955 mm³**. Soldering to the through-holes still leaves both factory sockets in place. Rev E replaces the two pads with four Ø3.70 mm lands at the manufacturer's mounting holes and two diagonal Ø1.86 mm locating pins. The holes are nominally Ø2.5 mm. The design allocates 0.25 mm between the lands and the component-side board face for adhesive or shims. Center the IC over the axle as the adhesive sets. Mounting changes are internal. The stowed envelope is 108.5 × 69 × 30 mm, with the original folding right-side reel. The replacement housing uses the other five Rev D printed parts.

## Nominal CAD results

### Touch glass and bezel

The 31137 board already carries a capacitive touch panel with an AXS15231B controller. In landscape, the manufacturer's lens drawing gives a 92.44 × 61.00 mm cover with R6 corners and a 73.44 ±0.15 × 48.96 ±0.15 mm viewing area. The active UI uses 480 × 320 pixels. The viewing window provides the nominal optical reference for this check. The supplier drawing does not dimension the electrical edge response of the touch sensor. [Waveshare board and dimensional resources](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B/Resources-And-Documents)

The printed bezel opening is 76.80 × 52.20 mm, R1.60, centered on that reference. Straight-edge margins are 1.68 mm left/right and 1.62 mm top/bottom. Extruding the entire rectangular viewing area upward through the installed bezel gave 0.00 mm³ overlap, including all four corners. The glass top is at Z 28.50 mm. The bezel underside above the glass is at Z 28.75 mm, giving 0.25 mm nominal clearance. The rim top is at Z 30.00 mm, 1.50 mm above the glass. It overhangs the inactive cover perimeter by 7.82 mm left/right and 4.40 mm top/bottom.

On the assembled print, display a full-screen border and verify all four sides. Trace each edge and corner with a bare fingertip, tap the smallest menu controls, then repeat with the enclosure closed and the reel in hand. Check for missed touches, phantom touches and rim pressure as the screws are tightened. Printed warp, lens registration, tightening load and finger-pad contact can change the result. [Waveshare factory touch test](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B/Instructions-For-Use)

### Assembly and service

| Test | Coverage | Result |
|---|---|---|
| Installed assembly | 19,986 cross-component pairs across both purchased assemblies, printed parts, reel hardware and reserved cell/speaker volumes | Zero interferences above 0.002 mm³ |
| Populated controller installation | Lower 16 mm from the display side. Housing, installed reel, encoder, cell and speaker present | Clear throughout swept bounds where certified. Remaining candidate pairs clear at 0.5 mm steps |
| Encoder installation | Lower into vacant controller bay with 8 mm inboard offset, then slide outboard onto the corner pins | Clear over 24 mm approach at 1 mm steps and 8 mm seating stroke at 0.5 mm steps |
| Bezel closure | Last 5 mm of vertical travel with both boards installed | Clear at 0.5 mm steps for candidate pairs |
| Reel and collar installation | Rotor from the right before fitting collar, then collar from inside before installing encoder | Clear at 0.5 mm steps over the modeled strokes |
| Reel versus all fixed parts | Seven conservative rotational envelopes, 575 obstacles each. All shaft angles and all handle angles 0–90°, including simultaneous fold and crank | All seven original moving solids inside their envelopes. All envelopes clear |
| Moving parts relative to each other | Stem, grip and retainer against the rotor, hinge screw, collar and magnet during opening at 5° steps | Clear at all sampled positions. The full-turn envelope concerns external obstacles |
| Service and fastener gauges | Four rear screw body/head envelopes, four straight driver corridors, two hinge shims, one example USB overmold | Clear for modeled sizes. Threaded engagement with mating inserts is intentional and excluded |
| Wire and connector space | Six individual reservations around A2 solder fanout, W1 bundle, J8 plug, battery splice, speaker lead | All six clear the fixed parts. Plug mating depth, flexible loops, and the leads as a connected set require a physical mock-up |

The CAD checks use OpenCascade solid intersections in millimetres. Broad-phase boxes reject disjoint pairs. The remaining pairs use solid booleans with a 0.002 mm³ reporting threshold. Surface contact, including a board standoff on its seat, can have zero interference volume. Closest-surface distances below were calculated independently. Internal construction of each supplier model is treated as a single purchased assembly. Wires, adhesive, threads, fabric and loads are outside the rigid interference test. The STEP contains 582 solids. Ancillary guides and screw gauges are represented in the test scripts and ledgers.

## Clearances and fit sensitivity

| Interface | Smallest nominal gap |
|---|---:|
| Display stack to bezel | 0.250 mm |
| Bare cell envelope to housing/fences | 0.400 mm |
| Speaker envelope to housing | 0.450 mm |
| Controller to encoder board | 0.474 mm |
| Magnet face to AS5600 package | 1.200 mm |
| Encoder sockets to revised housing | 1.500 mm |
| Controller to bare cell envelope | 6.500 mm |
| Controller to speaker envelope | 7.550 mm |

Three independent one-axis perturbations illustrate sensitivity. They are assumed displacements for this exercise. They do not constitute a statistical tolerance stack or supplier manufacturing limits.

- At 0.40 mm inward movement the sensor PCB clears A1. At 0.50 mm it intersects the controller substrate and display backing.
- The nominal 0.25 mm lens gap reaches contact at a 0.25 mm rise. At 0.30 mm the display interferes with the bezel.
- The cell envelope reaches a lateral fence at 0.40 mm displacement. At 0.50 mm it penetrates that fence. A pack's folded seal, protection board, lead exit and actual thickness matter here.

## Fit-print acceptance

1. Print the trial housing from the ZIP and use the matched Rev D bezel and reel components. The STL was checked as one watertight solid. Seat the controller on all four posts. With the lens unloaded, verify that the bezel sits fully on its rim and a thin feeler or removable witness strip confirms positive lens clearance. Measure the four seats and the bezel recess if the gap closes.
2. Seat the assembled A2 board with its through-hole wiring edge toward the case floor. Confirm that both factory sockets clear their lands. With the board fastened, check the 0.474 mm nominal board-edge gap with a nonconductive shim and record the actual value. Rotate the reel under finger load for a full turn with the handle folded and deployed. Verify free travel and consistent AS5600 magnet-detect, with neither weak-field nor strong-field status across the full turn.
3. Measure the received speaker including gasket and strain relief against the 15 × 30 × 7 mm reservation. Measure the protected cell including its sealed edges and lead exit against the 34 × 62 × 5 mm reservation. Trial-fit with the intended tape. The rear cover and board must seat freely with no pressure or witness marks on the pouch.
4. Dry-fit the actual J8 right-angle header, insulated tails, both battery adapter halves, the speaker plug and the USB programming cable. Route and retain the finished harness, seat the board and inspect during closure for pinching, stretched leads or connector side load. The USB gauge assumes a 12 × 6.5 mm overmold and 6 mm metal projection. Record the actual cable dimensions and verify full seating and USB data.
5. Pass the hardware gate when these observations and the received board revision are recorded. The first gameplay build then targets Willow Creek, with a cast, upward hook-set, reel-angle retrieval, selectable music level and bite cues. Firmware is pending this hardware gate.

## Reproducing the review

The ZIP contains the assembled STEP, printable trial housing, original STEP inputs, scripts and result ledgers. From the extracted scripts directory, use Python 3.11, CadQuery 2.8, NumPy and trimesh 5. Run the four modes of the static/path/motion/distance audit, then the envelope and gauge scripts.

```text
python audit.py static
python audit.py path
python audit.py motion
python audit.py metric
python continuous.py
python gauges.py
```

The scripts load the adjacent inputs folder and regenerate the revised housing from the original. Results write beside the scripts. The provided results folder also includes the analytic envelope ledger, closest-distance witnesses and a SHA-256 manifest for the CAD inputs. A1.000–545 and A2.00–24 follow the order of the imported supplier solids. A2.06 and A2.07 are the factory sockets. A2.16 is the chip body.

Waveshare supplies the display board mechanical file and the kit packing list. [Board resources](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B/Resources-And-Documents) · [Board variants and packing list](https://www.waveshare.com/esp32-s3-touch-lcd-3.5b.htm)

Adafruit supplies the populated breakout STEP and the Eagle board file used to register the sensor die package and four mounting holes. [AS5600 mechanical CAD](https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/6357%20AS5600%20Magnetic%20Sensor) · [PCB layout](https://github.com/adafruit/Adafruit-AS5600-Magnetic-Angle-Sensor-PCB) · [Protected cell](https://www.adafruit.com/product/258)
