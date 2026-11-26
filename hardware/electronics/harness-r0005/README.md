# R0005 haptic harness and stationary W1 service trial

The service candidate uses a CviLux CIEP05P1HK0-NH right-angle header, CIEP05SL000 housing, CIEP05C0010 terminal-position assurance insert and four CIEPT021PP0 terminals. The display assembly must be lifted for the modeled service motion. The fixture keeps all four W1 trunks, their solder taps and the unplugged J8 connector at their installed coordinates. Only the four W4 branches flex.

The local inspection page opens in a WebGL-capable browser. Its slider first presses the rocker, then holds the rocker while translating the housing, TPA, four terminals and their crimped conductors 8.25 mm along +Y. Switch **Display boards seated** on to see the clearance lost with the display still in place. **Latch close-up** and the section at X 24.26 mm show the right-hand retaining boss. The exact supplier views are generated locally from the [source register](source-cad/source-manifest.json). The [service review](../../mechanical/TW-A-0001-R0012/README.md) includes measurements and build instructions.

## Cavity and dressing fixture

Orient A3 with its headers opening toward +Y. The square J1 land at the low-X end is cavity 1. The four solder taps are fixed to W1, and the overcoat shoulder provides the stationary end of each W4 service loop. Compare the finished fixture against [installed parts](installed.json), [routing points and jacket lengths](routing.json) and the [form parameters](loop-forms.json). Jacket lengths extend from the insulation-crimp shoulder to the insulating tap overcoat. They exclude stripped conductor.

| Cavity | Installed X, mm | Net | Fixed tap X, Y, Z, mm | Jacket length, mm | Smallest modeled bend radius, mm |
|---|---:|---|---|---:|---:|
| 1 | 15.96 | VCC | 22.00, 18.00, 9.10 | 27.212 | 2.623 |
| 2 | 18.46 | IN/TRIG, grounded on A3 | Vacant | — | — |
| 3 | 20.96 | SCL | 26.20, 19.65, 12.28 | 26.961 | 1.361 |
| 4 | 23.46 | SDA | 28.20, 21.30, 11.22 | 28.464 | 0.916 |
| 5 | 25.96 | GND | 30.25, 22.95, 10.16 | 29.781 | 1.456 |

The [supplier terminal drawing](source-cad/source-manifest.json) specifies AWG 24–26 with 1.28–1.42 mm insulation OD. The fit study uses 26 AWG with the 1.42 mm maximum jacket. The source spring geometry continues to the open-wing transition. The modeled conductor and insulation barrels use formed envelopes. Crimp height, pull force, strand condition and lance seating need a lot-specific crimp section and pull test. The 0.916 mm SDA centerline radius at full withdrawal is an unresolved wire-life constraint. No selected wire has been qualified for this repeated bend.

## Mechanical and electrical checks before a service trial

Use a de-energized mockup for the first service trial. Fixture A3 and W1 independently, support the display, and leave the fixed tap coordinates visible against a registration scale. Record the initial and fully withdrawn dress, the resulting wire bend radius, bias on each crimp, and actual actuator and pull travel. The predicted rocker movement uses an assumed flexure axis. Compare the measured retention pocket and stop locations with those recorded in the [clearance report](clearance.json). The unmodified supplier housing and TPA intersect at the estimated seating datum. A sample or a complete mated CAD model must establish the actual internal geometry and operating clearance.

Identify each pin with the meter before seating. Check cavity-to-land continuity, J1-2 to ground independently of the removable plug, then interlead isolation on the loose harness. Repeat continuity after a service cycle and inspect the wire jackets, terminal lances and tap overcoats. The A3 PCB has a 2.50 mm CviLux footprint and a 1.40 mm insulating support between the nominal substrate face and the header feet. All five rigid tails intersect the substrate model by 0.06764 mm³ apiece. CIEP08SA identifies retention kinks on the two outer pins. The other three overlaps also require inspection. Gauge hole diameter, actual tail insertion/retention and solder-tail projection before accepting the header.

