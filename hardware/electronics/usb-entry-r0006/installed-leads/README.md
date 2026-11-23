# Fixed USB leads on the display subassembly

W2 carries the protected A5 output to the **PCB solder tail of A1 J8-1**. W3 returns through one common pigtail on the **PCB solder tail of J8-3**. W7 carries the MCU-independent, current-limited CTRL rail to the input hole on the existing lamp resistor board USB-PCB2. Its previous direct wire from J8-1, USB-W4A, is removed with both stripped ends. The lamp retains its resistor, LED and ground return. [Installed parts and digests](installed.json) · [Forming coordinates](routes.json)

| Wire | A5 hole in device X, Y | Destination | Conductor length to destination | Copper resistance at 70 °C |
|---|---|---|---:|---:|
| W2 | 34.45, 12.00 mm | A1 J8-1 fitted tail | 58.04 mm | 23.63 mΩ |
| W3 | 34.45, 5.00 mm | A1 J8-3 through lamp ground tee | 56.38 mm plus 5.25 mm shared | 25.09 mΩ |
| W7 | 30.65, 17.30 mm | USB-PCB2 at X −19.98, Y 18.47 mm | 55.03 mm | 22.40 mΩ |

Insert leads through the A5 back face, facing A1 when installed. The board model has 0.70 mm drills and its component side faces down in device coordinates. W2 and W3 strip 1.39 mm from Z18.30 to 16.91 mm. W2 reaches the lower face of the original J8-1 tail. Strip W7 by 1.54 mm at A5 and solder on the component face. At USB-PCB2 strip 1.61 mm and solder on the underside of its 0.40 mm input hole. Reserve a 1.24 mm diameter adhesive keepout around this hole when mounting USB-PCB2 to the fixed header. Solder shapes are nominal wetting envelopes. The carrier STEP represents the substrate and hole. Its fabrication artwork defines the corresponding copper land. [Carrier artwork definition](../../usb-status-r0003/carriers.py)

W3 branches from the continuing lamp ground 5.00 mm along its original centerline from the J8-3 jacket end. Expose a 2.50 mm window around that station and cover the finished side tap with the modeled insulating overcoat. The common pigtail keeps a single wire on the header tail. The model uses 0.254 mm solid copper and a conservative 0.52 mm jacket envelope for the Jonard R30 lead family. Resistance uses copper resistivity of 1.724 × 10⁻⁵ Ω·mm at 20 °C and a temperature coefficient of 0.00393/°C. Solder/contact losses, workmanship, wire tolerances and installed resistance require measurement. [Assembly population](../assembly.csv)

Form and solder the display-side subassembly before fixing A5 over the available space. Dress and restrain each lead along its controlled coordinates. The smallest modeled centerline bends are 0.94 mm at W2 and W3, and 0.86 mm at W7. Inspect jacket condition, maximum jacket diameter, pigtail insulation, strain relief and repeatable spacing on the identified article. Lead shapes show the target dress between their bonded ends. Retention along those spans requires physical verification.

The A1 PCB position of LRC4-1 remains unverified, so W1 has no installed path. W4/W5 need confirmed CC1 and CC2 landings on the identified V2 PCB. Those three runs and solder access remain open. The harness and controller remain on engineering hold. [Input boundary](../boundary.json)

The first W7 trial put solder on the upper sides of both boards. Exact geometry found five unwanted contacts at the lamp resistor and the two adhesives. The revised solder locations and keepout give 0.29 mm from W7 solder to the lamp adhesive and 0.60 mm to the resistor. The W7 jacket clears the resistor by 0.30 mm. [Original failed fit and input digests](negative-fit.json)

Each modeled solder fillet wets 0.5177 mm² of its assigned native A5 copper pad. The far-end W7 fillet covers 0.2165 mm² of the lamp carrier's plotted annulus. The native check also follows W2 and W3 through their solder and copper to the nominated J8 tails. These measurements describe the nominal geometry. [Contact measurements](fit.json)

**The smallest seated dressing margin is 0.0668 mm** between the W2 jacket and the lamp ground jacket. W7 has 0.090 mm to the A5 spacer. Both margins can be consumed by hand dressing or dimensional variation. The nominal lamp adhesive relief removes 0.540 mm³ and retains contact with both USB-PCB2 and J8. The W3 side-tap representation has 0.00685 mm³ of coincident conductor material inside the specified joint window. Inspect the actual side tap, bond and wire retention on the article.

Over 133 seated-display withdrawal stations, the lowest sampled clearance to a flexible W4 lead was 0.6151 mm in native CAD, from SDA to the W7 copper tip at 4.25 mm of withdrawal. The rigid assembly came closest at full withdrawal, with 4.9299 mm from the TPA to W3. The separate W4 clearance study evaluates the intervals between stations. [Route and service checks](../../harness-r0006/check.py)

Rebuild with CadQuery using `python form.py <registered-R0011-BRep-cache>`. After preparing the final A5 and fitted bond, run `python check_fit.py <registered-R0011-BRep-cache>` with CadQuery, OCP, NumPy and python-fcl. The recorded seated and moving checks use the closed display configuration. [Nominal fit results](fit.json)
