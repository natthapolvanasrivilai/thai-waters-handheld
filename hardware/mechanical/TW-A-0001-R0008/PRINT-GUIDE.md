# TW-A-0001-R0008 fit-print guide

Print one each of the 12 device parts for one handheld. The two battery gauges are separate shop tools. The ZIP includes a device-print-register.csv list of all twelve required part revision IDs, quantities and control hashes. The compressed STEP and the exploded viewer use installed device coordinates. The STLs are already rotated into the verified build pose with the first layer at Z=0.

## At the printer

1. Import a single STL at 100%, in millimetres. Keep its supplied rotation when centering it on the plate.
2. For the verified profile, select a Bambu Lab A1, 0.4 mm nozzle, Generic PETG, 0.20 mm Standard, textured PEI and normal automatic supports at 30° with support on model enabled. Use the outer brim widths below. The toolpaths and time estimates in the QA report apply to this profile and individual plates.
3. After cooling, lift each part and remove its brim. On the housing, clear support from the rear grip receiver, encoder lands, reel well and the smaller key and wire-tunnel regions. On the rotor, clear the outer rim and recessed face. Keep the circular working arcs clean. Check the small folding eye for distortion where it met the brim.

| STL stem | First layer | Outer brim | Predicted support |
|---|---|---:|---:|
| housing-battery-bay | West rear diagonal land | 8 mm | 4.410 g |
| bezel | Front face | 0 | 0 |
| rotor | Diagonal land on outer rim | 5 mm | 0.414 g |
| folding-stem | Diagonal flat on hinge eye | 5 mm | 0 |
| grip | Reel sleeve end | 0 | 0 |
| collar | Annular thrust face | 0 | 0 |
| power-cap | Back flange | 0 | 0 |
| rod-grip | Flat leading end of dovetail | 8 mm | 0 |
| grip-screw-keeper | Washer face | 0 | 0 |
| receiver-nut-keeper | Closed face | 0 | 0 |
| key-board-retainer-west | Top bar | 0 | 0 |
| battery-wire-bridge | Flat deck underside | 0 | 0 |
| PKCELL-max-body-with-wire-sockets | Broad pack face | 0 | 0 |
| Adafruit-258-CAD-with-PCM-and-stubs | Flat end opposite protruding leads | 5 mm | 0 |

For one complete set including gauges, the specified-brim simulation uses 92.08 g and seven hours of model print time. The rod grip stands 130.4 mm tall. Allow for machine preparation, plate changes, cooling and cleanup. See [the per-part print audit](QA/README.md) for first-layer toolpaths and the Rev G comparison.

## Fit on the bench

- Fit the bezel to the empty housing. It should seat around the frame with the entire active touchscreen opening exposed. Check the accessible connectors with their matching plugs.
- Install the power cap and its carrier, then press through 0.70 mm travel and confirm the cap returns and stays captive. The outer guide and inner flange counterbore provide 0.25 mm and 0.30 mm nominal radial clearance. The two roofs point diagonally in the installed housing.
- Fit the M3 hardware, slide the handle into its stop and tighten the captive screw. Retract it through the 5.30 mm modeled stroke. Slide the handle clear and repeat. Check the front shoulder for rocking and the keeper for capture throughout travel.
- Fit the rotor, collar, hinge and reel sleeve. Check a full turn both folded and deployed, and fold the crank through 90°. Nominal radial clearances are 0.30 mm at the housing journal, 0.15 mm at the collar and 0.24 mm between sleeve and stem.
- Remove the wire bridge before vertical gauge insertion. Test the 35.3 × 62.3 × 5.3 mm maximum-body gauge and the supplier-CAD gauge separately. Dress the inert leads, seat the bridge and confirm the connector can withdraw 4 mm. The modeled maximum pack sits 0.65 mm below the bridge. Keep the pack path, underside of the bridge, fastener tips and lead tunnel free of support residue.

The horizontal bores consist of two power-aperture steps, three captive-grip fastener steps and two inert-gauge lead sockets. Each has a 45° tangent roof and 270° circular working arc. The rotor and stem build at 45° to both bearing axes, preserving their cylindrical contacts. The bezel's partial 26° reel relief sits open at its edge. It carries the upward-facing circular segment of the assembly opening. The battery gauge with rigid lead stubs retains the supplier envelope.

These are digital fit and slice results. Record physical fastener hold, moving fits, gauge insertion, harness clearance, print adhesion and strength on the first build before proceeding with a powered assembly. See [the measured bore profiles](horizontal-bores.json) and [the assembly checks](fit-verification.json).

## Rebuild and inspect

Use Python 3.11 with CadQuery 2.8, NumPy and trimesh. Run `python build.py` beside the inputs directory. This rebuilds the CAD, oriented STLs and transformation manifest from the Rev G print datums and supplier STEP. Run `python verify_bores.py` for the analytical bore-profile probes. In the repository checkout, `verify_fit.py --reference-step <uncompressed Rev G STEP> --cache <scratch directory>` repeats the installed-component, gauge, contact and motion checks. The release packager uses the checkout's Rev G viewer, metadata and reference verification modules. The printable kit includes SHA-256 hashes for every member.
