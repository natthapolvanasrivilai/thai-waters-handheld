# TW-A-0002-R0004 · W4 haptic connector

Engineering fit candidate for **TW-A-0001-R0011**. A3 is the 20 × 20 mm Boardoza B0601V10000076 DRV2605L R1.0 breakout. Remove its straight male J1 strip and install Würth 61900519521 on a 1.00 mm unclad FR-4 spacer. A 61900511621 female housing encloses all five horizontal posts. Four 619100126015 factory-crimped 26 AWG leads connect the bus and power. J1 position 2 carries the unused trigger input. An insulated link connects that input to ground on the underside of A3. [Boardoza PCB and source](../../components/boardoza-drv2605l/README.md) · [TI DRV2605L pin functions](https://www.ti.com/lit/ds/symlink/drv2605l.pdf)

## Identify the cavities before mating

With the display removed, look down on the installed A3 PCB. The mating direction is toward −Y and withdrawal is toward +Y. The J1 pad row is at Y −14.90 mm. Pin 1 is the square pad at the smaller X coordinate. The five pin centers are 2.54 mm apart. Looking into the **removed female mating face** reverses a view taken from its wire-entry face. Mark the VCC end on the housing and mark each of the four black leads on the wiring fixture and record its tap. Establish cavity identity against the PCB square pad with the meter.

| Position on A3 | Installed X (mm) | Connection | W1 tap center X, Y, Z (mm) | Jacket path from insulation crimp to tee strip (mm) |
|---|---:|---|---|---:|
| 1 | 15.88 | Filtered 3.3 V | 21.80, 12.85, 9.10 | 13.15 |
| 2 | 18.42 | IN/TRIG to J1-5 on the PCB underside | Vacant housing cavity | — |
| 3 | 20.96 | SCL, A1 GPIO7 | 20.05, 9.61, 12.28 | 8.43 |
| 4 | 23.50 | SDA, A1 GPIO8 | 22.80, 10.69, 11.22 | 9.22 |
| 5 | 26.04 | GND | 24.75, 11.77, 10.16 | 10.37 |

The five source PCB drills and the five [Würth footprint drills](source-cad/61900519521.kicad_mod) are each 1.00 mm nominal. The installed header uses the exact [manufacturer STEP](source-cad/61900519521.step). The [source register](source-cad/README.md) identifies the different evidence available for the housing and crimp. These two supplier articles are specified by part number. The corresponding installed CAD uses drawing-derived geometry. The spring force, locking ramp, terminal retention and toleranced mated envelope remain first-article checks.

## Build the branch

1. Isolate USB and the battery. Confirm A3 is the documented R1.0 variant. Photograph its header orientation. Desolder the supplied strip without damaging the plated barrels, remove solder and inspect both sides at magnification. Check the unsoldered replacement fits by hand.
2. Make the spacer from 1.00 mm unclad FR-4. Cut a 6.15 × 13.10 mm rectangle. Starting from the same long edge, place the row of five Ø1.20 mm holes 1.35 mm in. Starting from the short end nearest cavity 5, drill at 1.46, 4.00, 6.54, 9.08 and 11.62 mm. Deburr. The installed BRep is named A3-J1-spacer. Solder the angled header on the component side with the top-lock tongue accessible and the spacer flat. Check heel/PCB clearance and solder wetting on all five tails.
3. Form the local mode strap using the retained 30 AWG, 0.80 mm OD insulated wire. Run its insulated portion just inboard of the J1 solder row on the underside. Solder the two short stripped ends to the J1-2 and J1-5 lands. Inspect the two intervening SCL/SDA tails, PCB floor gap and pad adhesive. Check for continuity with the W4 plug removed. TI specifies the ground connection when the trigger input is unused.
4. Seat four factory-terminated 619100126015 pigtails in cavities 1, 3, 4 and 5. Engage each contact lance. Use the retained crimp at the connector end and shorten only the opposite free end. Check the purchased lot’s jacket OD against the 1.50 mm CAD routing envelope, then use a fixture and the [formed paths](routing.json) to trim the stock. The listed lengths start **inside the insulation crimp**. They exclude the bare tee end. Do not cut the entire pigtail to the jacket dimension. Retain approximately the modeled 1.4–1.7 mm conductor reach from the insulation shoulder to the W1 center at each tee; confirm wetting and trim stray strands.
5. Move the four individually overcoated taps to the W1 straight runs approaching the encoder. Use a continuous W1 conductor through each 2.8 mm jacket window. Strip, wrap and solder the branch to its own net. Insulate each exposed section separately and inspect all neighboring leads before dressing the next tap. The CAD models the soldered electrical path and insulation envelope. Use fitted insulating material and a measured clearance coupon to establish the finished overcoat on the first unit.
6. Locate A3 with its center at X 20.80, Y −6.80 mm. Its component side faces the display and its J1 opens toward +Y. The original two 3M support strips sit below the board. Align to the STEP, press only inside the adhesive strips and leave the underside strap clear. Form the two factory motor leads to their original pads TP1 OUT+ and TP2 OUT−. Check wire identity against the motor marking and the board design. Seat the W4 plug using its plastic body. Finish the W1/encoder dress before closing the case.

## Inspect and service

Remove external power, open the case and disconnect the battery. Support the A1 display and release the AS5600/W1 loom from its installed dressing so the four short W4 branches can follow the plug. Grip both housing ends, support A3 and withdraw parallel to +Y. The [clearance report](clearance.json) tests a straight 8.25 mm rigid-housing travel against the stationary hardware. In the dressed assembly W1 first intersects the moving housing at 6.25 mm. With W1 parked, the sampled closest fixed item is the motor lead at 0.171 mm. That small gap requires a physical trial before the extraction sequence can be approved. Never use the pigtails as a handle. The installed cable shape is neutral only at full seating. A trial unit must establish where the freed loom can be parked, finger or nonconductive tool access, extraction force, terminal retention and repeatable re-dress. A pinched or stretched wire requires rework before applying power.

Measure the following on each first article with USB and battery disconnected. Record the meter, compensated lead resistance, serial and actual readings.

| Measurement | Prototype acceptance |
|---|---|
| Each W4 lead from its W1 tap to intended A3 land, plug seated | <1 Ω after lead compensation. Verify every cavity individually. |
| A3 J1-2 to J1-5, plug removed and seated | <1 Ω in both states. |
| Loose 4-lead harness before attaching W1 taps | Each populated cavity isolated from every other cavity and from the vacant cavity; >1 MΩ on dry, unconnected harness. |
| Assembled SDA/SCL/VCC/GND | Verify against PCB nets. The populated 2.2 kΩ pull-ups provide intentional paths. Record measured resistance after capacitors settle. Investigate a low-ohm short or unexpected polarity before power. |
| Motor terminals | Verify both land-to-lead connections and winding resistance against the motor lot. Confirm neither output is shorted to ground. |
| Closed and reopened unit | Mark 1 and GND, inspect crimp engagement, check no jacket pinch marks, compression on A3 or contact with the pouch. Flex each branch gently and repeat continuity through one service cycle. Record actual plug travel, contact retention, dimensions and force. |

Use the [installed solids and SHA-256 manifest](installed.json) and [build script](place.py) for digital configuration. The [audit script](audit.py) takes the uncompressed R0011 dressed STEP, using CadQuery and python-fcl. The closed STEP has 1.033 mm between adjacent W4 jackets, 1.645 mm between W4 and the motor assembly, 0.640 mm between the mode strap and adhesive, and 0.850 mm between A3 and the shell. Physical closure, load, endurance, vibration, insulation and electrical measurements are outstanding. The shared [R0003 base harness](../harness-r0003/README.md) supplies the remaining wiring. [W4 purchasing delta](bom-delta.csv)
