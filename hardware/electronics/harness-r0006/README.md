# W4 service harness R0006

The four W4 leads allow the CviLux plug to withdraw 8.25 mm along +Y with the display stack seated. J8, the four W1 trunks, their eight tap solids and the A3 header stay at their installed coordinates. Each 26 AWG lead leaves its insulation crimp on a 5.60 mm straight axis. Its flexible section begins 0.25 mm beyond the TPA rear plane. A circular jacket of 1.42 mm OD represents the upper insulation diameter in the CIEPT021PP0 crimp drawing. The complete assembly and service sequence are in the [R0013 mechanical review](../../mechanical/TW-A-0001-R0013/README.md).

For a first crimp-and-flex coupon, Pico 8826-0-44 provides 26 AWG wire with a listed 1.30 mm PVC jacket. Confirm the lot diameter against the terminal's 1.28–1.42 mm range, the conductor strand construction and service-cycle performance before approving the wire. The CAD clearance study retains the 1.42 mm jacket limit. [Manufacturer's wire specification and order codes](https://picocanada.com/view_product/8826-0)

## Dressing dimensions

Orient the A3 header mouth toward +Y. The square J1 pad at the low-X end is cavity 1. The wire axis at the crimp is Z 10.36 mm. Jacket length runs from the insulation-crimp shoulder to the dressed W1 tap shoulder, and excludes stripped conductor. J1-2 connects to ground on A3. Plug cavity 2 stays vacant.

| Plug cavity | Net | Crimp X, mm | Fixed tee copper center X, Y, Z, mm | Jacket length, mm | Smallest sampled centerline radius, mm | Continuous radius lower bound, mm |
|---|---|---:|---|---:|---:|---:|
| 1 | VCC | 15.96 | 22.00, 18.00, 9.10 | 51.9047 | 2.7868 | 1.9123 |
| 3 | SCL | 20.96 | 26.20, 19.65, 12.28 | 43.7990 | 2.3131 | 1.6757 |
| 4 | SDA | 23.46 | 28.20, 21.30, 11.22 | 43.5779 | 3.5143 | 2.6855 |
| 5 | GND | 25.96 | 30.25, 22.95, 10.16 | 44.6106 | 3.7901 | 3.0144 |

Fixture each tap overcoat shoulder 2.00 mm above its copper center. Form the installed lead against the XYZ stations in the fixture table. Measure along the jacket from the crimp. The table also gives the expected withdrawn dress at the same material stations. Compare the dressed physical leads against the released CAD before cycling. [Fixture coordinates](dress-fixture.csv) · [Crimp and tap datums](routing.json) · [Installed jacket solids and hashes](installed.json)

## Clearance evidence

The independent native check uses the four installed curves and the actual board, housing, other W4 leads, stationary loom and fixed USB parts. At 133 stations spaced 0.0625 mm apart, the checker subtracts the 0.71 mm jacket radius from the native centerline-to-part distances. Bernstein control hulls bound how far each centerline can move between stations. The six distinct W4 lead pairs receive both radii and both motion allowances. The spherical endpoint envelopes enclose the flat jacket end caps. All four W4 leads pass a 0.500 mm continuous nominal clearance gate against stationary parts and one another over the complete stroke. The own bonded tap and the modeled rigid crimp are documented joints. [Stationary and interlead clearance](continuous-clearance.json) · [Interval and bend-radius bounds](motion-bound.json) · [Sampled native witnesses](clearance.json) · [Station table](service-path.csv)

The closest native external witness is SDA to the fixed A5 W7 copper tip, 0.615070 mm at 4.25 mm travel. VCC clears J8 by 0.695593 mm at full withdrawal. SCL clears the motor by 0.693121 mm at 7.6875 mm travel. At the limiting sampled interlead pair, SCL and GND have a 0.793947 mm native gap at full withdrawal. Maximum native jacket-length variation across all stations is 0.0000000001 mm. The report binds these measurements to the final A3 and A5 boards, shaped adhesive and installed USB wire hashes.

The moving-member check presses the rocker through its modeled 13° release angle before translation and holds it there throughout withdrawal. It tests each free span against the plug body, rocker, TPA, all four terminals and all four stripped conductors in the plug coordinate frame. The straight crimp stub and TPA translate together with 0.040 mm nominal separation. The native check establishes 0.0399 mm continuous clearance for the examined moving interfaces. The minimum rocker-to-jacket centerline-envelope clearance throughout pressing, after rotational allowance, is 1.565 mm. The unmodified supplier plug still has blind pocket geometry around the inserted terminals and straight crimp stub. The [connector certificate](connector-clearance.json) and [original supplier registration](../harness-r0005/README.md) describe that scope.

At full withdrawal with the display seated, the R0012 negative control puts each old W4 jacket inside the old A5 solid. Measured overlap is 3.0600 mm³ VCC, 3.1013 mm³ SCL, 1.5290 mm³ SDA and 2.5167 mm³ GND. The [clearance report](clearance.json) retains the measurements from the original jacket and board solids.

## Reproduction and physical acceptance

Run these from this directory in the CAD environment. The baseline argument is the R0011 installed-coordinate BRep cache. The checker applies the R0012 harness and the R0013 A3, A5, adhesive and USB-lead overlays.

```text
python place.py
python motion_bound.py
python connector_gate.py
python certify.py --baseline-breps <R0011-BRep-directory>
python check.py --baseline-breps <R0011-BRep-directory> --stations 133
```

The wire source, strand construction and insulation must support the required repeated bend. The minimum sampled radius is on SCL adjacent to its tap. The interval lower bounds are conservative limits on its mathematical form. On a de-energized build, fixture the taps, form the leads, seat the display and measure the actual minimum radius, rebound, TPA rub, crimp load and continuity through withdrawal and reseating. A 0.50 mm independent wire-dressing error toward a neighbor would consume the certified external reserve. A 0.04 mm inward TPA deviation would close the modeled straight-jacket gap. Record the actual insulation lot, fixture repeatability, latch force, terminal seating and service-cycle results before accepting the physical harness.
