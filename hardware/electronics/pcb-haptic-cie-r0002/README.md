# A3 haptic daughterboard, CIE R0002

KiCad 10.0.8 reports zero DRC violations, unconnected items, schematic parity errors and ERC violations. The R0001 negative control reproduces all three J1 courtyard overlaps. R0002 rotates U1 by 90°, relocates both capacitors and both optional pull-up footprints, and reroutes the two copper layers. The entire footprint library matches R0001 byte for byte. J1 stays on its original 1.40 mm shim. Motor polarity on the silkscreen now follows the actual nets, with OUT+ at TP1 and OUT− at TP2. [Editable project](A3-CIE-R0002.kicad_pro) · [Rule results](drc.json) · [ERC](erc.json) · [Schematic](circuit.pdf)

| Footprint | Population | Planar gap to J1 courtyard bounds | Seated supplier header to fitted component |
|---|---|---:|---:|
| C1 | 1 µF | 0.230 mm | 1.048 mm |
| C2 | 1 µF | 0.580 mm | 1.361 mm |
| U1 | DRV2605LDGSR | 0.860 mm | 1.610 mm |
| R1, R2 | Both DNP | 2.530 mm each | Vacant |

The 20 × 20 mm board has the same outline, installed datum, J1 land pattern and two motor holes as R0001. A populated native STEP export contained 95 solids. The 14 fitted electronic solids and bare substrate matched the installed BReps. Among the seated header, plug, TPA, shim and two motor leads, the closest pair is U1 to the plug at 0.565 mm, with zero common material. The separately checked connector seating, solder-tail projection, real assembly tolerances and on-device measurements remain first-article gates. [Placement](placement.json) · [CAD measurements and digests](placed-verification.json) · [Substrate](placed/drvBoard.brep) · [Fitted electronics](placed/drvParts.brep)

The Gerber and Excellon reconstruction recovered all 7 nets, 25 electrical pads and 18 plated holes, including the five 1.00 mm J1 holes on 2.50 mm centers. Check the square end pad J1-1 for VCC, J1-2 for the grounded trigger, J1-3 for SCL, J1-4 for SDA and J1-5 for ground. Verify the ground strap between pins 2 and 5 with the harness removed. TP1 connects to U1 pin 7 and TP2 to U1 pin 9. Both optional 2.2 kΩ bus pull-ups remain vacant. A4 supplies the shared pull-ups. [Review fabrication archive](A3-CIE-R0002-fab.zip) · [Independent artwork check](artwork-verification.json) · [Netlist](connectivity.xml) · [Population and sourcing](bom.csv) · [Three-board extraction and replay](../../verification/r0013/routed.py)

## Reproduce

Run these commands from this folder. Use KiCad 10.0.8 with its stock libraries, Gerbonara 1.5.0 and Shapely 2.1.1 for artwork, and CadQuery 2.8 for installed geometry. Prepare the manufacturer files locally, then run the model-preparation script before the STEP check. Add `--write-placed` to regenerate the assembly BReps and substrate. [Local supplier preparation](../harness-r0005/source-cad/prepare_sources.py)

```text
python verify_electrical.py --kicad kicad-cli
<KiCad Python> check_layout.py
<CadQuery Python> make_models.py
<CadQuery Python> verify_placed.py --kicad kicad-cli
```

The Boardoza-derived circuit, TI package and footprint sources retain their CC BY-SA 4.0 terms. The CviLux header model and full populated export are local engineering inputs. [Original Boardoza evidence](../../components/boardoza-drv2605l/README.md) · [License](LICENSE) · [Previous revision](../pcb-haptic-cie-r0001/README.md)
