# Rev F exploded assembly and geometric release review

Open the standalone Riffle-Rev-F-exploded.html in a browser with WebGL. Its assembled, exploded, internal, harness and grip views use the CAD coordinate frame and geometry. Click any visible body or search the 79 selectable entries. The component record identifies its BOM reference and modeling method. Optional battery variants and the external USB gauge can be enabled independently of the nominal product. The seven assembly stages illustrate access and installation order. Animation paths separate parts for identification and do not certify tool or insertion clearance.

The nominal STEP includes the enclosure, bezel, attachable grip, reel, cap, slide/collar and lock components, fasteners including washers, sleeve and pins, controller/display board (546 vendor solids grouped for selection), 25-solid encoder assembly, battery, driver, motor, speaker, plugs, splice sleeves and individually modeled conductor runs. The 26 BOM lines map to geometry in bom-coverage.csv. The parts.json manifest describes mesh sources, proxy scope and position. The routes.json register gives all 16 proposed wire centerlines in millimetres, including the two 100 mm battery leads. The full STEP includes one catalog-nominal battery. The inspection alternatives are switchable in the HTML. The smaller additional-hardware.step.gz contains only new reference geometry to place over the existing product STEP at the same origin. The standalone full STEP can be opened after gzip extraction.

## Geometric evidence

| Assessed item | Result at nominal rigid dimensions |
|---|---|
| Released shell with catalog-nominal B1, dressed wiring and haptic option | 2,109 added-to-product pair comparisons, 223 candidates evaluated by solid intersection, 29 expected mating/termination overlaps, zero other intersections above 0.002 mm³ |
| Product-linked drawing, centered minimum / nominal / maximum | Housing intersection 0 / 11.983 / 30.124 mm³ |
| Alternate supplier CAD including PCM cap and lead stubs, centered | 118.397 mm³ overlap with the housing |
| Eight available placement trials, including quarter- and half-turns | Smallest tested housing overlap 109.371 mm³ at X +1.5, Y −1.5 mm. A 90-degree trial also enters the speaker by up to 1,569.696 mm³ |
| Clearance-window proposal at the least-interfering position | 38 × 64 × 7.3 mm, covering X −29…9, Y −32…32, Z 3.1…10.4 mm. Intercepts 171.702 mm³ of housing, 28.080 and 19.800 mm³ of the PH adapter halves, and 0.829 mm³ of one splice sleeve |

The additional-part test compares each pair involving a new member once, including new wire against new wire. The existing rev-F analysis covers inherited members. Exclusions, expected positive overlaps and source trial coordinates remain in placement-results.json. Actual copper, solder fillets, solder mask, threads, crimp barbs, wire stiffness and aperture tolerances require correlation. A connector's reference solid and a routed wire are packaging models. The haptic PCB outline comes from the QT Eagle board (25.4 × 17.78 mm), with height envelopes for the soldered parts. The older 17.78 × 16.51 mm board STEP in inputs is retained for provenance. The actual ordered board, plug heights, top-switch alignment, housing retention, rod/rail loads, reel detents, wire chafe, advertised wire bend limits and final assembly tools need physical inspection.

The separately supplied inert gauges test 35.30 × 62.30 × 5.30 mm drawing-maximum fit and the alternate 37 × 63 × 6 mm CAD envelope with cap and lead stubs. Follow gauges/README.md. The service window includes modeled 0.5 mm allowances at the sides/ends/below and 0.8 mm above. Confirm vendor swelling and pressure allowances, obtain controlled maximum dimensions for the purchased pack and move the PH pair/sleeve before choosing a future enclosure cut. Frozen Rev F prints remain the fit reference. Production battery fit is open.

## Reproduce

Use Python with CadQuery 2.8.0, NumPy and Trimesh. Put Three 0.180.0 and esbuild 0.25.x in a Node resolution path and install Playwright for browser testing. These example commands run at the project workspace root.

~~~powershell
$r=(Resolve-Path outputs/thai-waters-handheld/hardware/mechanical/rev-F/review).Path
& work/cad-env/Scripts/python.exe "$r/build_review.py" --work work/rev-f-inspection --check --full-step
& work/cad-env/Scripts/python.exe "$r/make_gauges.py"
$env:NODE_PATH=(Resolve-Path work/audit/node_modules).Path
& work/audit/node_modules/.bin/esbuild.cmd "$r/viewer.js" --bundle --minify --format=iife --outfile=work/rev-f-inspection/renderer.js
python -X utf8 "$r/pack_view.py" --work work/rev-f-inspection --output outputs/Riffle-Rev-F-exploded.html
Copy-Item work/rev-f-inspection/Riffle-Rev-F-dressed-assembly.step.gz outputs/Riffle-Rev-F-dressed-assembly.step.gz
$env:NODE_PATH=(Resolve-Path work/node_modules).Path
node "$r/viewer-test.cjs" outputs/Riffle-Rev-F-exploded.html outputs/Riffle-Rev-F-exploded-preview.png
~~~

Build inputs are fingerprinted in input-sha256.json. Run in a fresh work directory after changing a source STEP to invalidate its mesh cache. The viewer embeds its font, mesh arrays and renderer. The smoke test opens the file directly and checks for external requests, tests object selection by ray, group filter/isolation, optional modules, section and explode controls, seven assembly stages and phone width.

[Adafruit QT driver board, CC BY-SA 3.0](https://github.com/adafruit/Adafruit-DRV2605-PCB) · [Adafruit battery CAD, MIT](https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/258%201200mAh%20lipo) · [PKCELL product drawing, page 5](https://cdn-shop.adafruit.com/product-files/258/C101-_Li-Polymer_503562_1200mAh_3.7V_with_PCM_APPROVED_8.18.pdf). Source licenses accompany the references in inputs. The board-derived geometry carries the same CC BY-SA 3.0 attribution. Three uses the bundled MIT notice and Atkinson Hyperlegible Next uses the bundled OFL notice.
