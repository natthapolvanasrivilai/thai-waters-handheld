# Print the R0016 USB indicator housing

**Print plate 1 for the revised housing.** Reuse the separate USB1 gauge from plate 7 and the clear U light guide from plate 4. The project keeps the R0015 power-key relief and the integral A3 seats. [Editable X1 Carbon project](Thai-Waters-R0016-PCB-Fit-X1C.3mf) · [Housing and dry assembly](../README.md) · [Seven-plate material and part list](../../TW-A-0001-R0014/Printing/README.md)

Open the 3MF as a project in Bambu Studio. Plate 1 uses opaque PETG, a 0.4 mm nozzle, the SuperTack plate, 255 °C nozzle and 70 °C bed. The saved housing sits on the receiver soles without a brim. Keep its automatic normal supports, the local USB1 support blocker and the 0.10 mm layer-height range at build Z14.4–15.0 mm. The rest of the housing uses the 0.20 mm process. The plate-1 estimate is **2 h 7 min and 53.91 g**.

After the part cools, remove the normal supports from the open case. Steady the small shelf under the USB well when clearing support from below it. Look into the slot from its service-edge end (−Y). The floor, low inner lip, far stop and roof should be intact, with an open passage to the stop. The slice places no support in the board's route. A strand or sag from the roof can still catch the real gauge. Start with the loose, unpowered gauge in the empty case and follow the [dry-fit sequence](../README.md). If the gauge binds, withdraw it toward the service edge and inspect the shelf and roof before trying again.

## Native print checks

Bambu Studio 02.09.01.70 sliced all seven plates, with model paths for all 33 expected instances. An independent reopening and slice of plate 1 reproduced the local measurements. The housing has one connected first-layer model footprint of 776.24 mm². Both A3 rails and both sides of the power-key relief retained their established extrusion witnesses. [Project and toolpath measurements](QA/project-check.json) · [Seven-plate result](QA/native-all.json) · [Independent plate-1 result](QA/native-reopen.json) · [Reopened plate-1 preview](QA/plate-1-reopen.sliced.3mf)

| Checked feature | Result from the native bead footprints |
| --- | --- |
| Entry and slide | At Y−15 mm, the full gauge lowers clear. Along the 15 mm slide to the +Y stop the swept body and lens contain zero model and support bead area. These checks use the registered gauge blocks and the height of each deposited layer. |
| Bearing and headroom | The bearing top is at build Z14.70 mm. The central roof underside is Z18.00 mm, leaving 0.10 mm nominal vertical space beyond the 3.20 mm gauge. The parent print profile rounded the bearing up to Z14.80 mm and filled part of the sliding route with support. |
| Lip and far stop | Model beads cover at least 99.7% of the interior lip witness and 100% of the far-stop witness on their sampled layers. |
| Roof under the USB well | Model beads cover the 0.92 × 4.56 mm central roof witness on each of three layers. On the first roof layer the longest individual centerline segment inside the unsupported slot window is 1.30 mm. Physical sag and surface finish still need an actual print. |
| Support under the projecting shelf | The 17.00 mm² shelf starts at build Z14.20 mm. The support at Z13.80 mm projects onto 8.12 mm² of that footprint, matching the automatic-support control. The 0.20 mm vertical separation lets the support release. Inspect the shelf after removal. |

The CAD and toolpath numbers describe the nominal dry assembly. The first print still needs gauge entry, reverse removal, retention, printed dimensions and optical alignment checked by hand.

## Reproduce the checks

Use the repository CAD Python environment, Bambu Studio and fresh scratch locations. Create the control directory before running the commands. The control uses the same final housing mesh with the parent automatic-support and layer settings.

```text
python prepare.py --slicer /path/to/bambu-studio --scratch SCRATCH --automatic-only-control CONTROL/auto.3mf
bambu-studio --slice 1 --outputdir CONTROL --export-3mf sliced.3mf CONTROL/auto.3mf
python verify_print.py SCRATCH CONTROL
```
