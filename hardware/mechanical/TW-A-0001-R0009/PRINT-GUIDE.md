# R0009 handheld print and assembly guide

One handheld uses 16 printed parts. The 12 original device positions include the revised housing with its socket shroud and speaker seat, and the rotor with its 4.40 mm H2 head counterbore. The additional parts are one flexible socket diaphragm and three separate light guides. The two inert battery gauges are shop tools. All dimensions are in millimetres. The STEP and viewer share assembly axes, with west toward negative X and the display toward positive Z.

## Print preparation

Import each file at 100% scale and retain its supplied orientation. Move it in XY to center the part. Each STL starts on the bed at Z = 0. R0009 uses the R0008 circular working arcs, teardrop roofs, oblique journal poses and keyed rod datums. The electronic plug opening reproduces the installed USB-C interface. Each status channel has an eight-sided section.

| Device part | Face on plate | Outer brim |
|---|---|---:|
| Housing | West rear diagonal land | 8 mm |
| Bezel | Front bezel face | 0 |
| Rotor | Diagonal outer rim land | 5 mm |
| Folding stem | Diagonal hinge-eye flat | 5 mm |
| Grip and collar | Sleeve end and annular thrust face respectively | 0 |
| Power key cap | Back flange | 0 |
| Rod grip | Flat leading nose of dovetail | 8 mm |
| Grip screw keeper and receiver nut keeper | Washer face and closed cap face respectively | 0 |
| Key PCB retainer and wire bridge | Top bar and flat deck underside respectively | 0 |
| USB-C diaphragm | Full outward face | 0 |
| Each of three light guides | Supplied longitudinal flat | 3 mm |
| PKCELL maximum-body gauge | Broad face | 0 |
| Adafruit supplier-shape gauge | Flat end opposite the lead stubs | 5 mm |

The Bambu A1 simulation uses a 0.4 mm nozzle, 0.20 mm Standard, textured PEI, 30° automatic supports and support on model enabled. Use PETG for the rigid opaque parts and TPU 95A for the flexible mask. Remove support from the underside grip receiver, encoder lands, reel well, cable/key edges and rotor rim recess. Preserve the housing diagonal land, bearing surfaces and circular contact arcs. The print audit gives masses, support, times and triangle-level slope checks per plate. [Per-part results](QA/print-audit.json)

The diaphragm is one part. For the two-tone finish, load the supplied multi-part 3MF and assign case-colour opaque TPU 95A to usbSurround and charcoal opaque TPU 95A to usbEscutcheonLip. Keep the supplied relative position and print both regions together. Use a TPU-compatible dual-material feeding process. In Bambu Studio or OrcaSlicer, select each registered subpart in the object tree, assign the two actual TPU filament slots, then inspect the first and subsequent layers in the filament preview. The verified generic A1 import preserved geometry but assigned both regions to one filament by default. Keep the mask face unpainted where it touches the connector. Confirm the continuous dark lip, 0.51 mm maximum free thickness and uninterrupted 0.32 mm flex web under magnification. The single STL is the exact union for a monochrome first fit. Match opaque flange colour to the case on a coupon before making the finished unit. The 3MF defines material IDs and geometry. The ordinary PETG/TPU simulations are single-material toolpaths and exclude purge or changeover time.

The three guides have 1.20 mm across-flats polished faces. Transparent PETG is suitable for checking actual insertion and optical transfer. Optical-resin fabrication or a separate qualified transparent material process can reproduce the same CAD. Clean, polish and deburr the end faces. Keep every opaque channel partition intact. Confirm transfer, viewing angle, ambient contrast and cross talk on the assembled unit.

## Assembly

1. With the case open and the cell and controller removed, fit the 0.50 mm compressed perimeter gasket to the bottom grille. Place the Adafruit 3923 speaker cloth side down. Enter from the top with its center 24 mm east of final location. Lower to 0.65 mm above the seated plane, slide west 24 mm, then lower onto the gasket. Its two factory terminal positions face negative Y. Match the wire route and positive/negative BTL contacts to the electrical traveler. The designed free conductor centerlines to J9 exceed the stock 30 mm lead. Check solderability on a sample before re-leading the transducer. Check acoustic seal, cone clearance, polarity, maximum-volume distortion and temperature after closure.
2. Fit the three individual guides into the corresponding engraved status positions. The P point indicates the red ESP_EN/system-power lamp, U the independent blue USB VBUS lamp, and C the green CHGLED lamp. The power/charge pickups are 0.38 mm from the manufacturer's package faces. The blue pickup is 0.30 mm from its lens. Seat the blue daughterboard in its paired guides and shelf. Secure the current-limiter carrier by the specified insulating RTV joint, then cure and inspect it under the electrical traveler.
3. Seat the controller on its mounting datums. From the west, work the flexible inner lip over the outside perimeter of the metal socket with a smooth nonmetallic tool. Keep the fixture outside the receptacle and support the board during installation. Press the outer bead into its annular groove. Inspect the entire circumference. The stress-free print opening is 8.18 × 2.40 with R0.90 corners. A 0.38 mm radial preload and compliant web allow the ring to follow assembly offsets. The computer model preserves both material volumes at every included offset. Check the actual contact force, gap closure, adjustment range and pull-through after repeated plugging. The ring is a continuous privacy and trim collar. Its forward face is X −39.78, behind the socket mouth at X −40.00. The installed opening is 8.94 × 3.16 with R1.28 corners. The dark visible border measures 10.44 × 4.66 outside. The outer shell scallop measures approximately 14.74 × 8.46 and the inner cable corridor 13.62 × 7.76. The plug axis is Y 0, Z 19.33.
4. Check the fully seated plug with data, VBUS and retention at the actual device. The CAD audit uses a 12.35 × 6.50 R1 overmold, 8.28 × 2.43 maximum metal plug and 6.0–6.4 mm insertion. Check seating with actual target cables and confirm the shoulder clears the TPU, housing and bezel. Test all three light points in bright and dim ambient conditions, including charging plus running, connected idle, system off on USB, and unplugged operation. [Cable fit and sampled sightlines](QA/usb-port.json)
5. Fit the top-left key carrier, fasteners, haptic module and dressed harness according to the current travelers. Gauge each supported battery shape through the open bay before installing the lead bridge. Check the full touchscreen area, cap capture and electrical switch actuation, shaft movement, hinge, reel, detachable grip and audio with the final components installed. Record gauge results, seating forces, cable strain relief, clearances and first-article observations before approving a powered unit.

The installed STEP uses supplier-shape battery B1 and its registered lead routes. The viewer offers a separate engineering-allowance layer and individual battery comparisons. The historical comparison results remain associated with their original reference release. The static closeups show the device from the socket side with the status emitters off.

## Rebuild

Use a checkout containing R0008, R0009, the registered component inputs, electrical placement folders and the visualization bundle. Use Python 3.11 with CadQuery, NumPy, trimesh and VTK; use the project CAD environment where available. Run these commands in the R0009 folder.

```text
python build.py
python speaker.py
python diaphragm.py
python surface_finishes.py
python package.py cache --exports <exports> --work <scratch> --reference-step <decompressed-R0008-dressed.step>
python QA/verify_speaker.py <scratch>/r8-reference
python render_port.py <scratch>/r8-reference
python package.py step viewer --exports <exports> --work <scratch> --reference-step <decompressed-R0008-dressed.step>
python verify_exports.py --exports <exports> --work <scratch>
python package.py kit --exports <exports> --work <scratch>
```

The supplied STLs and 3MF can be printed directly from the ZIP. For an offline print-only rebuild, extract the ZIP and run `python build.py` followed by `python diaphragm.py`. The sealed R0008 input archive supplies all required baseline solids and print datums. The checksum manifest covers every kit member. Physical tests remain open until measured on a built unit.

