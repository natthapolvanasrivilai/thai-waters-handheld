# A3 haptic daughterboard, CIE R0001

The editable [KiCad project](A3-CIE-R0001.kicad_pro) adapts the Boardoza DRV2605L R1.0 breakout to a five-position right-angle CviLux header. The new PCB has a 2.50 mm pitch, a ground trace from J1-2 to J1-5, and two unpopulated local pull-up positions. A4 supplies the shared bus pull-ups. This is a custom board. Purchasing the stock breakout supplies a different header and pitch. [Population and sourcing](bom.csv) · [Schematic](circuit.pdf) · [Boardoza upstream revision and license](../../components/boardoza-drv2605l/README.md)

## Identify the cable

With the installed board component-side up, J1-1 is the square pad at assembly X15.96 mm. Counting toward increasing assembly X, the row ends at X25.96 mm. The header opens toward +Y. Mark the VCC end before comparing the mating face and the wire-entry face, which mirror each other.

| Cavity | Board signal | Installed lead |
|---|---|---|
| 1 | VCC, regulated 3.3 V | W1 VCC tap |
| 2 | GND, grounding the driver's IN/TRIG input | Empty housing cavity, copper strap on PCB |
| 3 | SCL, U1 pin 2 | W1 SCL tap |
| 4 | SDA, U1 pin 3 | W1 SDA tap |
| 5 | GND, U1 pin 8 | W1 GND tap |

TP1 goes to motor OUT+, TP2 to OUT−. On an unpowered loose assembly check each cavity against the [schematic netlist](connectivity.xml), check ground between J1-2 and J1-5 with W4 removed, and check for adjacent shorts. Verify the CIE terminal, wire OD, crimp height, insulation grip, extraction force and polarity on the actual lot before electrical testing. CviLux specifies 19.6 N minimum crimp tensile strength for 26 AWG and an initial 10 mΩ maximum contact resistance under its dry-circuit test. The proposed W4 wire is Pico 8826-0-44. Usable service bend, delivered jacket OD, tooling and the crimp process remain open. [Terminal drawing](https://www.cvilux.com/uploads/drawings/101/749/CIEP06S.pdf) · [CviLux performance specification](https://www.cvilux.com/uploads/spec/101/753/SPCI172.pdf)

## Board and enclosure evidence

The engineering [Gerber and drill archive](A3-CIE-R0001-fab.zip) has five 1.00 mm J1 holes on 2.50 mm centers. The 20 × 20 mm board specifies 1.60 mm finished thickness. The nominal header drawing calls for finished holes Ø1.00 +0.10/−0.00 mm. Its unrestrained kinked end pins need insertion and post-solder inspection with the 1.40 mm insulating shim. Nominal straight-tail projection is approximately 0.4 mm below the finished board. The bare substrate STEP measures 1.51 mm, excluding the nominal outer layer stack. [Header drawing](https://www.cvilux.com/uploads/drawings/101/752/CIEP08S.pdf) · [Installed geometry](../harness-r0005/mate.py)

KiCad ERC found zero issues. DRC found zero unconnected items and zero schematic-parity issues. Three **unwaived courtyard errors** remain at the elevated J1. Its projected outline overlaps vacant R1 and populated C1/U1. With the nominal support installed, the housing-to-C1 and housing-to-U1 distances in the supplier geometry are 0.515 and 0.565 mm. Those distances depend on seating, board thickness and part tolerances. The physical shim, plug insertion, soldering and closed-case service check remain open. An independent check reconstructed all seven signal nets and 25 pads from fresh plotted copper and 14 plated drills. Two isolated fiducials carry no electrical pins. [ERC](erc.json) · [DRC](drc.json) · [Artwork evidence](artwork-verification.json)

Replacing the rectangular courtyard with the exact projected shroud would still intersect all three component courtyards. Extruding their KiCad XY bounds vertically through the supplier housing captured 6.343 mm³ at C1, 6.791 mm³ at R1 and 15.252 mm³ at U1. Clearing J1 in the positive PCB X direction requires moves exceeding 4.170, 4.170 and 4.425 mm respectively. The first two moves reach the opposite passive positions. Moving U1 also changes its ten pin routes and the registered populated CAD. A physical remedy requires a coordinated layout, component placement and service-path revision. The elevated approach remains a held alternative. [Relocation and clearance measurements](../../verification/r0012/courtyard-measurements.json)

## Source and reproduction

The symbol and footprint snapshots keep the source design editable with KiCad 10.0.8. The five-position header footprint was drawn from CviLux CIEP08SA. The upstream PCB, schematic geometry and TI package solid are adapted from Boardoza's DRV2605L project, licensed CC BY-SA 4.0. The derived Boardoza material is distributed under the [same license](LICENSE). The CviLux model is obtained from its manufacturer separately. The [model preparation script](make_models.py) builds the header model with its installed shim offset and recovers the TI device solids from the licensed Boardoza assembly. A clean native KiCad export produced 88 valid solids. The six header solids and fourteen fitted electronic solids matched the installed enclosure assembly in all bounding coordinates within 0.000001 mm. [Reconstruction evidence](../../verification/r0012/model-rebuild.json)

Use the [three-board verification instructions](../../verification/r0012/README.md) to regenerate the plot and rule checks. Loose-board order, powered bring-up and system acceptance remain on hold. No procurement quote or first article is recorded here.
