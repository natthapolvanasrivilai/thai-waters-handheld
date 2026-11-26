# R0012 CviLux service-motion review

The rigid connector can withdraw 8.25 mm with W1 held in its installed position. The nominal open-display digital model has 3.240 mm minimum sampled clearance from the moving rigid parts to W1. The smallest modeled W4 jacket clearance is 0.347 mm against a neighboring fixed wire. Actual catch engagement, flex force, TPA seating, wire life and repeatable service remain open.

| Measurement | Result and location |
|---|---|
| Rigid housing, rocker, TPA, terminals and stripped ends to stationary W1 | 3.240 mm from 3.875 through 8.250 mm. The first sampled minimum is on W1 SDA between X 28.31 and 31.55 at Y 3.875, Z 11.22 mm. |
| Continuous rigid-to-W1 lower bound | 3.156 mm. Native intervals are 0.125 mm in translation and 1.625° in rotation. A rigid distance varies by at most the relative surface displacement. The worst unsampled allowance is 0.08432 mm. |
| Sensitivity of rigid-to-W1 lower bound | 2.256 mm after an illustrative 0.90 mm stack. Allocations are 0.20 mm registration, 0.20 mm housing and 0.50 mm fixture dress. These are engineering assumptions for this comparison. |
| W4 branches, display assembly lifted | The sampled mesh minimum is 0.345 mm, W4 GND jacket to W1 SCL, at the seated position. Native BRep gives 0.347397 mm and zero common volume. The nearest points are (30.605, 19.756, 13.020) and (30.605, 19.707, 12.676) mm. A 0.50 mm dressing variation can consume this clearance. |
| Display fully installed | Rigid motion clears raised A4 by at least 0.471 mm in the sampled sweep. The bending SCL jacket first reaches A5 at 0.500 mm withdrawal. Service requires an open display assembly and independent support for the unplugged J8 end. |
| Released rocker to header | 0.256 mm at full modeled press and zero withdrawal. The fully withdrawn rigid connector is 1.825 mm clear of the header. |
| Supplied mating geometry | Two seated boss intersections total 0.968 mm³. The five pins intersect the blind cosmetic pockets by 4.406 mm³. The registered TPA intersects the supplier housing by 10.167 mm³. Four formed terminal studies each intersect capped cavities by 7.248 mm³. The TPA also touches the two outer W4 jackets, with common material of 0.00053 mm³ on VCC and 0.01085 mm³ on GND. The complete assembly therefore has zero nominal minimum clearance. |
| Rocker model | The actual supplier rocker was split just above its flexure neck and rotated 13° about X at Y −6.55, Z 13.56 mm. A 0.168 mm³ overlap at the root remains in this rigid-rotation approximation. No elastic solution or release-force measurement has been substituted. |

**Inspection controls.** Open the generated R0012 connector-motion HTML in a WebGL-capable browser. Use **Seated**, **Pressed** and **Withdrawn** to compare the two motions. Drag or scroll to inspect the paired bosses and fixed W1 taps. The optional seated-display overlay shows where the modeled W4 leads strike the hardware during withdrawal. Both the supplier header and housing are displayed directly from their native shapes. The flat underside of the supplier rocker omits the retention pocket needed to resolve the seated condition.

The [full path CSV](QA/service-path.csv) contains nine release stations and 67 withdrawal stations. The [detailed fit report](../../electronics/harness-r0005/clearance.json) lists the stationary, moving and removed components, uncertainty inputs, formed-lead radii and each interference. Flexible wire results and surrounding hardware use a sampled triangular screen. Only rigid plug to W1 has a native full-path lower bound. The [STEP verification](export-verification.json) and [service round trip](QA/service-roundtrip.json) bind the installed measurements to the exported assembly. The [harness fixture](../../electronics/harness-r0005/README.md) contains the cavity and service data.

## Rebuilding the local supplier view

Use the source manifest and the [manufacturer download preparation](../../electronics/harness-r0005/source-cad/prepare_sources.py) to prepare the CviLux models locally. Retain the supplier license and source conditions. Supply the controlled R0011 dressed STEP archive, CadQuery 2.8, NumPy, SciPy and python-fcl. The inspection page bundles Three.js and OrbitControls with esbuild. Exact supplier solids and rendered mesh pages belong in local engineering storage.

1. Run the [harness placement builder](../../electronics/harness-r0005/place.py). It installs the A3 substrate, soldered header, individual contact studies, retaining insert, PCB supports and formed harness.
2. Run [assembly.py](assembly.py) with `--reference R0011.step.gz --work WORK --exports EXPORTS`. It reloads the compressed file, checks every installed component against the ledger and repeats the lower-port closure test.
3. Run [baseline_cache.py](baseline_cache.py) with the reference archive and a cache directory. Run [service_check.py](service_check.py) with `--baseline-breps CACHE` and [verify_service_roundtrip.py](verify_service_roundtrip.py) with the R0012 compressed STEP.
4. Bundle [service-viewer.js](service-viewer.js) using esbuild with Three.js available, `--bundle --format=iife --minify` and an output file. Run [service_view.py](service_view.py) with `--baseline-breps CACHE --bundle BUNDLE --exports EXPORTS`. Run [viewer.py](viewer.py) with `--exports EXPORTS` for the full exploded assembly page.
5. Run [test_service_view.cjs](test_service_view.cjs) with the motion HTML, a test JSON path and a PNG preview path, using Playwright Core and Edge. It checks all three motion stations, animation, comparison overlay, keyboard control and mobile width.

The measured alternative service forms supersede an earlier routing hypothesis whose W4 GND touched W1 GND when seated and whose VCC jacket struck the bridge and housing during withdrawal. Raising A4 by 1.00 mm retained the original XY and replaced the three 3 mm spacers with 2 mm spacers. The prior A4 position intersected the pressed rocker by 1.813 mm³. Lifting the display still provides room for the W4 leads, whose upper envelope reaches Z 21.20 mm.

